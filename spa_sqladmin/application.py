from __future__ import annotations

import inspect
import io
import logging
import types as _builtin_types
from pathlib import Path
from types import MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Sequence,
    cast,
    no_type_check,
)
from urllib.parse import urljoin

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from starlette.applications import Starlette
from starlette.datastructures import FormData, UploadFile
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
    RedirectResponse,
    Response,
)
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from spa_sqladmin._menu import CategoryMenu, DirectLinkMenu, Menu, ViewMenu
from spa_sqladmin._types import ENGINE_TYPE
from spa_sqladmin.api import (
    api_ajax_lookup as _api_ajax_lookup,
)
from spa_sqladmin.api import (
    api_auth_status as _api_auth_status,
)
from spa_sqladmin.api import (
    api_create as _api_create,
)
from spa_sqladmin.api import (
    api_delete as _api_delete,
)
from spa_sqladmin.api import (
    api_detail as _api_detail,
)
from spa_sqladmin.api import (
    api_edit as _api_edit,
)
from spa_sqladmin.api import (
    api_export as _api_export,
)
from spa_sqladmin.api import (
    api_form_schema as _api_form_schema,
)
from spa_sqladmin.api import (
    api_list as _api_list,
)
from spa_sqladmin.api import (
    api_login as _api_login,
)
from spa_sqladmin.api import (
    api_logout as _api_logout,
)
from spa_sqladmin.api import (
    api_site as _api_site,
)
from spa_sqladmin.authentication import (
    AuthenticationBackend,
    PathProtectionMiddleware,
    login_required,
)
from spa_sqladmin.forms import WTFORMS_ATTRS, WTFORMS_ATTRS_REVERSED
from spa_sqladmin.helpers import (
    is_async_session_maker,
    prettify_class_name,
    slugify_action_name,
    slugify_class_name,
)
from spa_sqladmin.models import BaseView, LinkView, ModelView

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore[attr-defined]

__all__ = [
    "Admin",
    "expose",
    "action",
]

logger = logging.getLogger(__name__)


class BaseAdmin:
    """Base class for implementing Admin interface.

    Danger:
        This class should almost never be used directly.
    """

    def __init__(
        self,
        app: Starlette,
        engine: ENGINE_TYPE | None = None,
        session_maker: sessionmaker | None = None,
        base_url: str = "/admin",
        title: str = "Admin",
        logo_url: str | None = None,
        favicon_url: str | None = None,
        color_palette: dict[str, dict[str, str]] | None = None,
        middlewares: Sequence[Middleware] | None = None,
        authentication_backend: AuthenticationBackend | None = None,
    ) -> None:
        self.app = app
        self.engine = engine
        self.base_url = base_url
        self.title = title
        self.logo_url = logo_url
        self.favicon_url = favicon_url
        self.color_palette = color_palette

        if session_maker:
            self.session_maker = session_maker
        elif isinstance(self.engine, Engine):
            self.session_maker = sessionmaker(bind=self.engine, class_=Session)
        else:
            self.session_maker = sessionmaker(
                bind=self.engine,  # type: ignore[arg-type]
                class_=AsyncSession,
            )

        self.session_maker.configure(autoflush=False, autocommit=False)
        self.is_async = is_async_session_maker(self.session_maker)

        middlewares = middlewares or []
        self.authentication_backend = authentication_backend
        if authentication_backend:
            middlewares = list(middlewares)
            middlewares.extend(authentication_backend.middlewares)

        self.admin = Starlette(middleware=middlewares)
        self._views: list[BaseView | ModelView] = []
        self._menu = Menu()
        # Mutable set shared with PathProtectionMiddleware so paths added later
        # (e.g. via add_link_view) are picked up without rebuilding the stack.
        self._protected_paths: set[str] = set()
        self._path_protection_active: bool = False
        self._session_on_parent: bool = False

    @property
    def views(self) -> list[BaseView | ModelView]:
        """Get list of ModelView and BaseView instances lazily.

        Returns:
            List of ModelView and BaseView instances added to Admin.
        """

        return self._views

    def _find_model_view(self, identity: str) -> ModelView:
        for view in self.views:
            if isinstance(view, ModelView) and view.identity == identity:
                return view

        raise HTTPException(status_code=404)

    def _ensure_session_on_parent(self) -> None:
        """Add session middleware to the parent app once (idempotent)."""
        if self._session_on_parent or self.authentication_backend is None:
            return
        self._session_on_parent = True
        for mw in self.authentication_backend.middlewares:
            self.app.add_middleware(mw.cls, **mw.kwargs)  # type: ignore[attr-defined]

    def protect_paths(self, paths: Sequence[str]) -> None:
        """Gate the given URL paths on the **parent** app behind admin authentication.

        Requests to the listed paths are intercepted before they reach the
        application's own route handlers.  Unauthenticated requests are
        redirected to the admin login page; authenticated requests pass through
        unchanged.

        This is most commonly used to protect auto-generated API documentation
        endpoints (``/docs``, ``/redoc``, ``/openapi.json``) so they are only
        accessible to logged-in admin users.

        .. note::
            If you also want to remove public access completely, disable the
            default endpoints in your framework (e.g. ``FastAPI(docs_url=None,
            redoc_url=None, openapi_url=None)``) and re-expose them through a
            :class:`~spa_sqladmin.models.LinkView` with ``protect=True``.

        Args:
            paths: Iterable of URL paths to protect (e.g. ``["/docs", "/redoc"]``).

        Example::

            admin.protect_paths(["/docs", "/redoc", "/openapi.json"])
        """
        if self.authentication_backend is None:
            return

        self._protected_paths.update(paths)

        if not self._path_protection_active:
            self._path_protection_active = True
            login_url = f"{self.base_url}/login"

            # PathProtectionMiddleware must run *after* the session middleware so
            # request.session is already populated.  Starlette processes middlewares
            # outermost-first, and add_middleware() prepends, so we add
            # PathProtectionMiddleware first (becomes inner) then the session
            # middlewares (become outer).
            # We add session middlewares unconditionally here — not via
            # _ensure_session_on_parent — to guarantee correct ordering even when
            # _setup_docs_protection has already added SessionMiddleware earlier.
            self.app.add_middleware(  # type: ignore[attr-defined]
                PathProtectionMiddleware,
                protected_paths=self._protected_paths,
                admin_login_url=login_url,
                auth_backend=self.authentication_backend,
            )
            for mw in self.authentication_backend.middlewares:
                self.app.add_middleware(mw.cls, **mw.kwargs)  # type: ignore[attr-defined]
            self._session_on_parent = True

    def add_view(self, view: type[ModelView] | type[BaseView]) -> None:
        """Add ModelView, BaseView, or LinkView classes to Admin.
        This is a shortcut that will handle ``add_model_view``, ``add_base_view``,
        and ``add_link_view``.
        """

        if view.is_model:
            self.add_model_view(view)  # type: ignore
        elif getattr(view, "is_link", False):
            self.add_link_view(view)  # type: ignore
        else:
            self.add_base_view(view)

    def _find_decorated_funcs(
        self,
        view: type[BaseView | ModelView],
        view_instance: BaseView | ModelView,
        handle_fn: Callable[
            [MethodType, type[BaseView | ModelView], BaseView | ModelView],
            None,
        ],
    ) -> None:
        funcs = inspect.getmembers(view_instance, predicate=inspect.ismethod)

        for _, func in funcs[::-1]:
            handle_fn(func, view, view_instance)

    def _handle_action_decorated_func(
        self,
        func: MethodType,
        view: type[BaseView | ModelView],
        view_instance: BaseView | ModelView,
    ) -> None:
        if hasattr(func, "_action"):
            view_instance = cast(ModelView, view_instance)
            route = Route(
                path=f"/{view_instance.identity}/action/" + getattr(func, "_slug"),
                endpoint=func,
                methods=["GET"],
                name=f"action-{view_instance.identity}-{getattr(func, '_slug')}",
            )
            # Insert before SPA catch-all routes (last 2)
            spa_idx = max(0, len(self.admin.router.routes) - 2)
            self.admin.router.routes.insert(spa_idx, route)

            if getattr(func, "_add_in_list"):
                view_instance._custom_actions_in_list[getattr(func, "_slug")] = getattr(
                    func, "_label"
                )
            if getattr(func, "_add_in_detail"):
                view_instance._custom_actions_in_detail[getattr(func, "_slug")] = (
                    getattr(func, "_label")
                )

            if getattr(func, "_confirmation_message"):
                view_instance._custom_actions_confirmation[getattr(func, "_slug")] = (
                    getattr(func, "_confirmation_message")
                )

    def _handle_expose_decorated_func(
        self,
        func: MethodType,
        view: type[BaseView | ModelView],
        view_instance: BaseView | ModelView,
    ) -> None:
        if hasattr(func, "_exposed"):
            if view.is_model:
                path = f"/{view_instance.identity}" + getattr(func, "_path")
                name = f"view-{view_instance.identity}-{func.__name__}"
            else:
                view.identity = getattr(func, "_identity")
                path = getattr(func, "_path")
                name = getattr(func, "_identity")

            route = Route(
                path=path,
                endpoint=func,
                methods=getattr(func, "_methods"),
                name=name,
            )
            # Insert before SPA catch-all routes (last 2)
            spa_idx = max(0, len(self.admin.router.routes) - 2)
            self.admin.router.routes.insert(spa_idx, route)

    def add_link_view(self, view: type[LinkView]) -> None:
        """Add a :class:`LinkView` to the Admin.

        Registers a protected route at ``/{identity}`` on the admin sub-app
        that delegates to ``view.get_response(request)``.  Unauthenticated
        visitors are redirected to the admin login page.

        ???+ usage
            ```python
            from spa_sqladmin import LinkView
            from starlette.responses import JSONResponse

            class StoreStats(LinkView):
                name = "Stats"
                icon = "BarChart2"

                async def get_response(self, request):
                    return JSONResponse({"users": 42})

            admin.add_link_view(StoreStats)
            ```
        """

        if not view.identity:
            view.identity = slugify_class_name(view.__name__)
        if not view.name:
            view.name = prettify_class_name(view.__name__)

        view._admin_ref = self
        view_instance = view()

        async def _handler(self_inner: Any, request: Request) -> Response:
            result = self_inner.get_response(request)
            if inspect.iscoroutine(result):
                return await result
            return result  # type: ignore[return-value]

        protected = login_required(_handler)
        bound_handler = _builtin_types.MethodType(protected, view_instance)

        route = Route(
            path=f"/{view_instance.identity}",
            endpoint=bound_handler,
            methods=["GET"],
            name=view_instance.identity,
        )
        # Insert before SPA catch-all routes (last 2)
        spa_idx = max(0, len(self.admin.router.routes) - 2)
        self.admin.router.routes.insert(spa_idx, route)

        self._views.append(view_instance)
        self._build_menu(view_instance)

    def add_model_view(self, view: type[ModelView]) -> None:
        """Add ModelView to the Admin.

        ???+ usage
            ```python
            from spa_sqladmin import Admin, ModelView

            class UserAdmin(ModelView, model=User):
                pass

            admin.add_model_view(UserAdmin)
            ```
        """

        view._admin_ref = self
        # Set database engine from Admin instance
        view.session_maker = self.session_maker
        view.is_async = self.is_async
        view.ajax_lookup_url = urljoin(
            self.base_url + "/", f"api/{view.identity}/ajax/lookup"
        )
        view_instance = view()

        self._find_decorated_funcs(
            view, view_instance, self._handle_action_decorated_func
        )

        self._find_decorated_funcs(
            view, view_instance, self._handle_expose_decorated_func
        )

        self._views.append(view_instance)
        self._build_menu(view_instance)

    def add_base_view(self, view: type[BaseView]) -> None:
        """Add BaseView to the Admin.

        ???+ usage
            ```python
            from spa_sqladmin import BaseView, expose

            class CustomAdmin(BaseView):
                name = "Custom Page"
                icon = "TrendingUp"

                @expose("/custom", methods=["GET"])
                async def test_page(self, request: Request):
                    return JSONResponse({"message": "custom page"})

            admin.add_base_view(CustomAdmin)
            ```
        """

        view._admin_ref = self
        view_instance = view()

        self._find_decorated_funcs(
            view, view_instance, self._handle_expose_decorated_func
        )
        self._views.append(view_instance)
        self._build_menu(view_instance)

    def _build_menu(self, view: ModelView | BaseView) -> None:
        if view.category:
            menu = CategoryMenu(name=view.category, icon=view.category_icon)
            menu.add_child(ViewMenu(view=view, name=view.name, icon=view.icon))
            self._menu.add(menu)
        else:
            self._menu.add(ViewMenu(view=view, icon=view.icon, name=view.name))


class Admin(BaseAdmin):
    """Main entrypoint to admin interface.

    ???+ usage
        ```python
        from fastapi import FastAPI
        from spa_sqladmin import Admin, ModelView

        from mymodels import User # SQLAlchemy model


        app = FastAPI()
        admin = Admin(app, engine)


        class UserAdmin(ModelView, model=User):
            column_list = [User.id, User.name]


        admin.add_view(UserAdmin)
        ```
    """

    def __init__(  # type: ignore[no-any-unimported]
        self,
        app: Starlette,
        engine: ENGINE_TYPE | None = None,
        session_maker: sessionmaker | "async_sessionmaker" | None = None,
        base_url: str = "/admin",
        title: str = "Admin",
        logo_url: str | None = None,
        favicon_url: str | None = None,
        color_palette: dict[str, dict[str, str]] | None = None,
        middlewares: Sequence[Middleware] | None = None,
        debug: bool = False,
        authentication_backend: AuthenticationBackend | None = None,
        embed_docs: bool = False,
        docs_title: str | None = None,
    ) -> None:
        """
        Args:
            app: Starlette or FastAPI application.
            engine: SQLAlchemy engine instance.
            session_maker: SQLAlchemy sessionmaker instance.
            base_url: Base URL for Admin interface.
            title: Admin title.
            logo_url: URL of logo to be displayed instead of title.
            favicon_url: URL of favicon to be displayed.
            embed_docs: When ``True``, embed ``/docs``, ``/redoc``, and
                ``/openapi.json`` into the admin sidebar.  If an
                ``authentication_backend`` is configured the endpoints are also
                gated behind admin auth; otherwise they are embedded as plain
                links with no extra protection.
            docs_title: Title prefix used for the Swagger UI and ReDoc pages
                when ``embed_docs=True``.  Defaults to the admin ``title``.
        """

        super().__init__(
            app=app,
            engine=engine,
            session_maker=session_maker,  # type: ignore[arg-type]
            base_url=base_url,
            title=title,
            logo_url=logo_url,
            favicon_url=favicon_url,
            color_palette=color_palette,
            middlewares=middlewares,
            authentication_backend=authentication_backend,
        )

        statics = StaticFiles(packages=["spa_sqladmin"])

        async def http_exception(
            request: Request, exc: Exception
        ) -> Response | Awaitable[Response]:
            if not isinstance(exc, HTTPException):
                raise TypeError("Expected HTTPException, got %s" % type(exc))

            return JSONResponse(
                {"error": exc.detail or "Error", "status_code": exc.status_code},
                status_code=exc.status_code,
            )

        # Build the SPA index.html path
        self._admin_ui_dir = Path(__file__).parent / "statics" / "admin-ui"
        self._spa_index_cache: str | None = None

        if authentication_backend is None:
            logger.warning(
                "spa-sqladmin: No authentication_backend configured — "
                "all admin routes are publicly accessible. "
                "Pass authentication_backend= to restrict access."
            )

        # Rate-limit the login endpoint via slowapi (IP + User-Agent key so
        # clients behind the same NAT/router are not conflated).
        login_endpoint: Any = self._api_login
        _rate_limit = getattr(authentication_backend, "login_rate_limit", None)
        if _rate_limit:
            from slowapi import Limiter
            from slowapi.middleware import SlowAPIMiddleware
            from slowapi.util import get_remote_address

            def _ip_ua_key(request: Request) -> str:
                ip = get_remote_address(request)
                ua = request.headers.get("user-agent", "")
                return f"{ip}:{ua}"

            _limiter = Limiter(key_func=_ip_ua_key)
            self.admin.state.limiter = _limiter
            self.admin.add_middleware(SlowAPIMiddleware)
            login_endpoint = _limiter.limit(_rate_limit)(login_endpoint)
            logger.debug("spa-sqladmin: login rate limit set to %s", _rate_limit)

        routes = [
            Mount("/statics", app=statics, name="statics"),
            # API routes
            Route("/api/site", endpoint=self._api_site, name="api:site"),
            Route(
                "/api/auth-status",
                endpoint=self._api_auth_status,
                name="api:auth-status",
            ),
            Route(
                "/api/login",
                endpoint=login_endpoint,
                name="api:login",
                methods=["POST"],
            ),
            Route(
                "/api/logout",
                endpoint=self._api_logout,
                name="api:logout",
                methods=["GET"],
            ),
            Route(
                "/api/{identity}/list",
                endpoint=self._api_list,
                name="api:list",
            ),
            Route(
                "/api/{identity}/detail/{pk:path}",
                endpoint=self._api_detail,
                name="api:detail",
            ),
            Route(
                "/api/{identity}/form-schema",
                endpoint=self._api_form_schema,
                name="api:form-schema",
            ),
            Route(
                "/api/{identity}/create",
                endpoint=self._api_create,
                name="api:create",
                methods=["POST"],
            ),
            Route(
                "/api/{identity}/edit/{pk:path}",
                endpoint=self._api_edit,
                name="api:edit",
                methods=["POST"],
            ),
            Route(
                "/api/{identity}/delete",
                endpoint=self._api_delete,
                name="api:delete",
                methods=["DELETE"],
            ),
            Route(
                "/api/{identity}/export/{export_type}",
                endpoint=self._api_export,
                name="api:export",
            ),
            Route(
                "/api/{identity}/ajax/lookup",
                endpoint=self._api_ajax_lookup,
                name="api:ajax_lookup",
            ),
            # SPA catch-all: serves React SPA for all non-API routes.
            # Named routes below allow url_for() calls from action/expose handlers.
            Route("/login", endpoint=self._spa_catchall, name="login"),
            Route("/{identity}/list", endpoint=self._spa_catchall, name="list"),
            Route(
                "/{identity}/details/{pk:path}",
                endpoint=self._spa_catchall,
                name="detail",
            ),
            Route("/{identity}/create", endpoint=self._spa_catchall, name="create"),
            Route(
                "/{identity}/edit/{pk:path}",
                endpoint=self._spa_catchall,
                name="edit",
            ),
            Route("/", endpoint=self._spa_catchall, name="index"),
            Route("/{path:path}", endpoint=self._spa_catchall, name="spa_catchall"),
        ]

        self.admin.router.routes = routes
        self.admin.exception_handlers = {HTTPException: http_exception}
        self.admin.debug = debug
        self.app.mount(base_url, app=self.admin, name="admin")

        if embed_docs:
            self._setup_docs_embed(docs_title=docs_title)

    # --- API endpoint wrappers ---
    def _setup_docs_embed(self, docs_title: str | None = None) -> None:
        """Embed /docs, /redoc, /openapi.json in the admin sidebar.

        Called automatically when ``embed_docs=True`` is passed to
        :class:`Admin`.

        When an ``authentication_backend`` is configured the endpoints are also
        gated behind admin auth (mirrors the `fastapi-docshield
        <https://github.com/example/fastapi-docshield>`_ approach):

        1. **Remove** the existing FastAPI doc routes from ``app.router.routes``
           and null out ``app.docs_url`` / ``app.redoc_url`` / ``app.openapi_url``
           so they are never re-added.
        2. **Register** replacement route handlers that check admin auth first,
           then call FastAPI's own ``get_swagger_ui_html``, ``get_redoc_html``,
           and ``app.openapi()`` to generate the response.
        3. **Redirect** unauthenticated requests to the admin login page.
        4. **Add sidebar entries** under an *API Docs* category.

        Without an ``authentication_backend`` the sidebar entries are added as
        plain direct links — no route replacement is performed.

        Args:
            docs_title: Title prefix for Swagger UI and ReDoc pages.  Falls
                back to the admin ``title`` when not provided.

        Raises:
            ImportError: If ``fastapi`` is not installed.
        """
        try:
            from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
        except ImportError as exc:
            raise ImportError(
                "embed_docs=True requires fastapi. Install it with: pip install fastapi"
            ) from exc

        auth_backend = self.authentication_backend
        parent_app = self.app
        page_title = docs_title or self.title

        if auth_backend is not None:
            # Gate the doc endpoints behind admin auth (docshield approach):
            # remove FastAPI's built-in routes and replace with auth-checking handlers.
            self._ensure_session_on_parent()

            login_url = f"{self.base_url}/login"
            doc_paths = {"/docs", "/redoc", "/openapi.json"}

            # Remove FastAPI's built-in doc routes so ours win.
            parent_app.router.routes = [  # type: ignore[attr-defined]
                r
                for r in parent_app.router.routes  # type: ignore[attr-defined]
                if getattr(r, "path", "") not in doc_paths
            ]
            # Null out FastAPI config attrs so they are never re-registered.
            for _attr in ("docs_url", "redoc_url", "openapi_url"):
                if getattr(parent_app, _attr, None) in doc_paths:
                    setattr(parent_app, _attr, None)

            def _make_handler(
                get_response: Callable[[], Response],
            ) -> Callable[[Request], Awaitable[Response]]:
                async def handler(request: Request) -> Response:
                    user = await auth_backend.authenticate(request)
                    if not user:
                        return RedirectResponse(login_url)
                    return get_response()

                return handler

            async def _openapi_handler(request: Request) -> Response:
                user = await auth_backend.authenticate(request)
                if not user:
                    return RedirectResponse(login_url)
                from starlette.responses import JSONResponse as _JSONResponse

                return _JSONResponse(parent_app.openapi())  # type: ignore[attr-defined]

            endpoints = [
                (
                    "/docs",
                    _make_handler(
                        lambda: get_swagger_ui_html(
                            openapi_url="/openapi.json",
                            title=f"{page_title} — Swagger UI",
                        )
                    ),
                ),
                (
                    "/redoc",
                    _make_handler(
                        lambda: get_redoc_html(
                            openapi_url="/openapi.json",
                            title=f"{page_title} — ReDoc",
                        )
                    ),
                ),
                ("/openapi.json", _openapi_handler),
            ]

            for path, handler in reversed(endpoints):
                # Insert at 0 to ensure our handlers are checked before FastAPI's.
                parent_app.router.routes.insert(  # type: ignore[attr-defined]
                    0, Route(path, endpoint=handler, methods=["GET"])
                )

        category = CategoryMenu(name="API Docs")
        category.add_child(
            DirectLinkMenu(
                name="Swagger UI",
                icon="BookOpen",
                url="/docs",
                identity="swagger-ui-docs",
            )
        )
        category.add_child(
            DirectLinkMenu(
                name="ReDoc",
                icon="FileText",
                url="/redoc",
                identity="redoc-docs",
            )
        )
        category.add_child(
            DirectLinkMenu(
                name="OpenAPI JSON",
                icon="Braces",
                url="/openapi.json",
                identity="openapi-json-docs",
            )
        )
        self._menu.add(category)

    async def _api_site(self, request: Request) -> Response:
        return await _api_site(self, request)

    async def _api_list(self, request: Request) -> Response:
        return await _api_list(self, request)

    async def _api_detail(self, request: Request) -> Response:
        return await _api_detail(self, request)

    async def _api_form_schema(self, request: Request) -> Response:
        return await _api_form_schema(self, request)

    async def _api_create(self, request: Request) -> Response:
        return await _api_create(self, request)

    async def _api_edit(self, request: Request) -> Response:
        return await _api_edit(self, request)

    async def _api_delete(self, request: Request) -> Response:
        return await _api_delete(self, request)

    async def _api_export(self, request: Request) -> Response:
        return await _api_export(self, request)

    async def _api_ajax_lookup(self, request: Request) -> Response:
        return await _api_ajax_lookup(self, request)

    async def _api_login(self, request: Request) -> Response:
        return await _api_login(self, request)

    async def _api_logout(self, request: Request) -> Response:
        return await _api_logout(self, request)

    async def _api_auth_status(self, request: Request) -> Response:
        return await _api_auth_status(self, request)

    async def _spa_catchall(self, request: Request) -> Response:
        """Catch-all route: serves SPA for client-side routing, 404 otherwise."""
        spa_html = self._get_spa_html()
        if spa_html:
            return Response(content=spa_html, media_type="text/html")
        raise HTTPException(status_code=404)

    def _get_spa_html(self) -> str | None:
        """Read and cache the SPA index.html with injected base URL."""
        if self._spa_index_cache is not None:
            return self._spa_index_cache

        index_path = self._admin_ui_dir / "index.html"
        if not index_path.exists():
            return None

        import json as _json

        html = index_path.read_text(encoding="utf-8")
        # Inject base href and admin config
        base_href = f"{self.base_url}/statics/admin-ui/"
        config = {
            "baseUrl": self.base_url,
            "apiUrl": f"{self.base_url}/api",
            "title": self.title,
            "logoUrl": self.logo_url,
            "faviconUrl": self.favicon_url,
            "colorPalette": self.color_palette,
        }
        config_json = _json.dumps(config)
        config_script = f"<script>window.__ADMIN_CONFIG__={config_json}</script>"
        # Set the HTML <title> tag
        html = html.replace("<title>Admin</title>", f"<title>{self.title}</title>", 1)
        # Inject favicon link if provided
        favicon_html = ""
        if self.favicon_url:
            favicon_html = f'\n<link rel="icon" href="{self.favicon_url}">'
        html = html.replace(
            "<head>",
            f'<head>\n<base href="{base_href}">\n{config_script}{favicon_html}',
            1,
        )
        self._spa_index_cache = html
        return html

    async def _handle_form_data(self, request: Request, obj: Any = None) -> FormData:
        """
        Handle form data and modify in case of UploadFile.
        This is needed since in edit page
        there's no way to show current file of object.
        """

        form = await request.form()
        form_data: list[tuple[str, str | UploadFile]] = []
        for key, value in form.multi_items():
            if not isinstance(value, UploadFile):
                form_data.append((key, value))
                continue

            should_clear = form.get(key + "_checkbox")
            empty_upload = len(await value.read(1)) != 1
            await value.seek(0)
            if should_clear:
                form_data.append((key, UploadFile(io.BytesIO(b""))))
            elif empty_upload and obj and getattr(obj, key):
                f = getattr(obj, key)  # In case of update, imitate UploadFile
                form_data.append((key, UploadFile(filename=f.name, file=f.open())))
            else:
                form_data.append((key, value))
        return FormData(form_data)

    def _normalize_wtform_data(self, obj: Any) -> dict:
        form_data = {}
        for field_name in WTFORMS_ATTRS:
            if value := getattr(obj, field_name, None):
                form_data[field_name + "_"] = value
        return form_data

    def _denormalize_wtform_data(self, form_data: dict, obj: Any) -> dict:
        data = form_data.copy()
        for field_name in WTFORMS_ATTRS_REVERSED:
            reserved_field_name = field_name[:-1]
            if (
                field_name in data
                and not getattr(obj, field_name, None)
                and getattr(obj, reserved_field_name, None)
            ):
                data[reserved_field_name] = data.pop(field_name)
        return data


def expose(
    path: str,
    *,
    methods: list[str] | None = None,
    identity: str | None = None,
    include_in_schema: bool = True,
) -> Callable[..., Any]:
    """Expose View with information."""

    @no_type_check
    def wrap(func):
        func._exposed = True
        func._path = path
        func._methods = methods or ["GET"]
        func._identity = identity or func.__name__
        func._include_in_schema = include_in_schema
        return login_required(func)

    return wrap


def action(
    name: str,
    label: str | None = None,
    confirmation_message: str | None = None,
    *,
    include_in_schema: bool = True,
    add_in_detail: bool = True,
    add_in_list: bool = True,
) -> Callable[..., Any]:
    """Decorate a [`ModelView`][sqladmin.models.ModelView] function
    with this to:

    * expose it as a custom "action" route
    * add a button to the admin panel to invoke the action

    When invoked from the admin panel, the following query parameter(s) are passed:

    * `pks`: the comma-separated list of selected object PKs - can be empty

    Args:
        name: Unique name for the action - should be alphanumeric, dash and underscore
        label: Human-readable text describing action
        confirmation_message: Message to show before confirming action
        include_in_schema: Indicating if the endpoint be included in the schema
        add_in_detail: Indicating if action should be dispalyed on model detail page
        add_in_list: Indicating if action should be dispalyed on model list page
    """

    @no_type_check
    def wrap(func):
        func._action = True
        func._slug = slugify_action_name(name)
        func._label = label if label is not None else name
        func._confirmation_message = confirmation_message
        func._include_in_schema = include_in_schema
        func._add_in_detail = add_in_detail
        func._add_in_list = add_in_list
        return login_required(func)

    return wrap
