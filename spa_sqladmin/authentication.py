from __future__ import annotations

import functools
import hmac
import inspect
import secrets
from typing import Any, Callable

from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response


class SimpleAuthBackend:
    """Ready-to-use in-memory authentication backend.

    Pass a dictionary of ``{username: password}`` pairs at construction time.
    Credentials are validated against that in-memory mapping on every login.

    Example::

        auth = SimpleAuthBackend(
            secret_key="change-me",
            credentials={"admin": "secret", "ops": "s3cur3"},
            login_rate_limit="5/minute",
        )
        Admin(app, engine, authentication_backend=auth)
    """

    def __init__(
        self,
        secret_key: str,
        credentials: dict,
        login_rate_limit: str = "60/minute",
        session_max_age: int = 3600,
        https_only: bool = False,
    ) -> None:
        from starlette.middleware.sessions import SessionMiddleware

        self.login_rate_limit = login_rate_limit
        self.middlewares = [
            Middleware(
                SessionMiddleware,
                secret_key=secret_key,
                max_age=session_max_age,
                https_only=https_only,
            ),
        ]
        self._credentials: dict[str, str] = {
            str(k): str(v) for k, v in credentials.items()
        }

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        stored = self._credentials.get(username, "")
        # Always compare (even for unknown users) to mitigate timing attacks.
        # `and stored` prevents empty-string false-positive on unknown usernames.
        if hmac.compare_digest(stored, password) and stored:
            # Clear existing session to prevent session fixation, then store
            # a random token so the authenticated value is unguessable.
            request.session.clear()
            request.session["token"] = secrets.token_hex(32)
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


class AuthenticationBackend:
    """Base class for implementing the Authentication into SQLAdmin.
    You need to inherit this class and override the methods:
    `login`, `logout` and `authenticate`.
    """

    def __init__(
        self,
        secret_key: str,
        session_max_age: int = 3600,
        https_only: bool = False,
    ) -> None:
        from starlette.middleware.sessions import SessionMiddleware

        self.middlewares = [
            Middleware(
                SessionMiddleware,
                secret_key=secret_key,
                max_age=session_max_age,
                https_only=https_only,
            ),
        ]

    async def login(self, request: Request) -> bool:
        """Implement login logic here.
        You can access the login form data `await request.form()`
        andvalidate the credentials.
        """
        raise NotImplementedError()

    async def logout(self, request: Request) -> Response | bool:
        """Implement logout logic here.
        This will usually clear the session with `request.session.clear()`.

        If a `Response` or `RedirectResponse` is returned,
        that response is returned to the user,
        otherwise the user will be redirected to the index page.
        """
        raise NotImplementedError()

    async def authenticate(self, request: Request) -> Response | bool:
        """Implement authenticate logic here.
        This method will be called for each incoming request
        to validate the authentication.

        If a `Response` or `RedirectResponse` is returned,
        that response is returned to the user,
        otherwise a True/False is expected.
        """
        raise NotImplementedError()


def login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to check authentication of Admin routes.
    If no authentication backend is setup, this will do nothing.
    """

    @functools.wraps(func)
    async def wrapper_decorator(*args: Any, **kwargs: Any) -> Any:
        view, request = args[0], args[1]
        admin = getattr(view, "_admin_ref", view)
        auth_backend = getattr(admin, "authentication_backend", None)
        if auth_backend is not None:
            response = await auth_backend.authenticate(request)
            if isinstance(response, Response):
                return response
            if not bool(response):
                return RedirectResponse(request.url_for("admin:login"), status_code=302)

        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper_decorator


class PathProtectionMiddleware:
    """ASGI middleware that gates a set of URL paths behind admin authentication.

    Added to the **parent** app by
    :meth:`~spa_sqladmin.application.BaseAdmin.protect_paths`
    so that direct navigation to protected paths (e.g. ``/docs``, ``/redoc``) is subject
    to the same session check as the admin UI itself.

    The ``protected_paths`` argument is a *mutable* :class:`set` shared with the
    admin instance, so paths registered after the middleware is created are
    automatically picked up without rebuilding the middleware stack.
    """

    def __init__(
        self,
        app: Any,
        protected_paths: set[str],
        admin_login_url: str,
        auth_backend: "AuthenticationBackend",
    ) -> None:
        self.app = app
        self.protected_paths = protected_paths
        self.admin_login_url = admin_login_url
        self.auth_backend = auth_backend

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            request = Request(scope, receive)
            if request.url.path in self.protected_paths:
                result = await self.auth_backend.authenticate(request)
                if isinstance(result, Response):
                    await result(scope, receive, send)
                    return
                if not bool(result):
                    response = RedirectResponse(
                        url=self.admin_login_url, status_code=302
                    )
                    await response(scope, receive, send)
                    return
        await self.app(scope, receive, send)
