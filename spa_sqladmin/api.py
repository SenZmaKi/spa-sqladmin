"""JSON API endpoints for the React frontend."""

from __future__ import annotations

import functools
import inspect
import json
import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

from starlette.datastructures import FormData, UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from spa_sqladmin._menu import CategoryMenu, DirectLinkMenu, ViewMenu
from spa_sqladmin.filters import OperationColumnFilter
from spa_sqladmin.helpers import get_object_identifier, slugify_class_name
from spa_sqladmin.models import ModelView

if TYPE_CHECKING:
    from spa_sqladmin.application import Admin

logger = logging.getLogger(__name__)

FIELD_TYPE_MAP: dict[str, str] = {
    "StringField": "string",
    "TextAreaField": "textarea",
    "IntegerField": "integer",
    "IntegerRangeField": "integer",
    "DecimalField": "decimal",
    "DecimalRangeField": "decimal",
    "FloatField": "float",
    "BooleanField": "boolean",
    "DateField": "date",
    "DateTimeField": "datetime",
    "DateTimeLocalField": "datetime",
    "TimeField": "time",
    "SelectField": "select",
    "RadioField": "select",
    "SelectMultipleField": "select_multiple",
    "QuerySelectField": "relation_select",
    "QuerySelectMultipleField": "relation_select_multiple",
    "AjaxSelectField": "ajax_select",
    "AjaxSelectMultipleField": "ajax_select_multiple",
    "FileField": "file",
    "JSONField": "json",
    "IntervalField": "interval",
    "Select2TagsField": "tags",
    "EmailField": "email",
    "TelField": "tel",
    "URLField": "url",
    "PasswordField": "password",
    "ColorField": "color",
    "HiddenField": "hidden",
}


def _serialize_value(value: Any) -> Any:
    """Convert a Python value to a JSON-serializable type."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    try:
        return str(value)
    except Exception:
        return repr(value)


def _is_required(field: Any) -> bool:
    """Check if a WTForms field is required."""
    if not hasattr(field, "validators"):
        return False
    for validator in field.validators or []:
        cls_name = type(validator).__name__
        if cls_name in ("DataRequired", "InputRequired"):
            return True
    return False


def _serialize_field_value(field: Any) -> Any:
    """Serialize a WTForms field's current value."""
    data = field.data
    if data is None:
        return None
    if isinstance(data, Enum):
        return data.value
    if isinstance(data, (datetime, date, time)):
        return data.isoformat()
    if isinstance(data, timedelta):
        return str(data)
    if isinstance(data, Decimal):
        return float(data)
    if isinstance(data, UUID):
        return str(data)
    if isinstance(data, (list, tuple, set)):
        return [_serialize_value(v) for v in data]
    if isinstance(data, dict):
        return data
    if isinstance(data, (str, int, float, bool)):
        return data
    if hasattr(data, "__str__"):
        return str(data)
    return data


def api_login_required(func: Callable[..., Any]) -> Callable[..., Any]:
    """Like login_required but returns JSON 401 instead of redirect."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        admin: Admin = args[0]
        request: Request = args[1]
        auth_backend = getattr(admin, "authentication_backend", None)
        if auth_backend is not None:
            response = await auth_backend.authenticate(request)
            if isinstance(response, Response):
                return JSONResponse({"error": "Not authenticated"}, status_code=401)
            if not bool(response):
                return JSONResponse({"error": "Not authenticated"}, status_code=401)
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        return func(*args, **kwargs)

    return wrapper


@api_login_required
async def api_site(admin: "Admin", request: Request) -> Response:
    """Site metadata: models, menu, config."""
    models = []
    for view in admin.views:
        if not isinstance(view, ModelView):
            continue
        if not view.is_visible(request):
            continue
        models.append(
            {
                "identity": view.identity,
                "name": view.name,
                "name_plural": view.name_plural,
                "icon": view.icon or "",
                "permissions": {
                    "can_create": view.can_create,
                    "can_edit": view.can_edit,
                    "can_delete": view.can_delete,
                    "can_view_details": view.can_view_details,
                    "can_export": view.can_export,
                },
            }
        )

    menu = _serialize_menu(admin, request)

    return JSONResponse(
        {
            "title": admin.title,
            "logo_url": admin.logo_url,
            "favicon_url": admin.favicon_url,
            "color_palette": admin.color_palette,
            "base_url": admin.base_url,
            "models": models,
            "menu": menu,
            "has_auth": admin.authentication_backend is not None,
        }
    )


def _serialize_menu(admin: "Admin", request: Request) -> list[dict]:
    items = []
    for item in admin._menu.items:
        if not item.is_visible(request):
            continue
        items.append(_serialize_menu_item(item, request))
    return items


def _serialize_menu_item(item: Any, request: Request) -> dict:
    if isinstance(item, CategoryMenu):
        children = []
        for child in item.children:
            if child.is_visible(request):
                children.append(_serialize_menu_item(child, request))
        return {
            "type": "category",
            "name": item.display_name,
            "icon": item.icon or "",
            "children": children,
        }
    if isinstance(item, DirectLinkMenu):
        return {
            "type": "item",
            "name": item.display_name,
            "icon": item.icon or "",
            "identity": item.identity,
            "is_model": False,
            "is_link": True,
            "url": item.direct_url,
        }
    if isinstance(item, ViewMenu):
        is_link = getattr(item.view, "is_link", False)
        return {
            "type": "item",
            "name": item.display_name,
            "icon": item.icon or "",
            "identity": getattr(item.view, "identity", ""),
            "is_model": getattr(item.view, "is_model", False),
            "is_link": is_link,
            # LinkView routes live inside the admin sub-app at /{identity}.
            # The sidebar derives the href from identity, not url.
            "url": "",
        }
    return {}


@api_login_required
async def api_list(admin: "Admin", request: Request) -> Response:
    """Paginated list data with column definitions and filter info."""
    identity = request.path_params["identity"]
    model_view = admin._find_model_view(identity)

    if not model_view.is_accessible(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    pagination = await model_view.list(request)

    columns = []
    for prop_name in model_view._list_prop_names:
        label = model_view._column_labels.get(prop_name, prop_name)
        sortable = prop_name in model_view._sort_fields
        is_relation = prop_name in model_view._relation_names
        columns.append(
            {
                "name": prop_name,
                "label": label,
                "sortable": sortable,
                "is_relation": is_relation,
            }
        )

    rows = []
    for obj in pagination.rows:
        pk = str(get_object_identifier(obj))
        row: dict[str, Any] = {"_pk": pk}
        for prop_name in model_view._list_prop_names:
            value, formatted = await model_view.get_list_value(obj, prop_name)
            if prop_name in model_view._relation_names:
                row[prop_name] = _serialize_relation_value(value, formatted)
            else:
                row[prop_name] = _serialize_value(value)
        rows.append(row)

    filters = await _serialize_filters(model_view, request)

    return JSONResponse(
        {
            "rows": rows,
            "columns": columns,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "count": pagination.count,
            "page_size_options": list(model_view.page_size_options),
            "searchable": len(model_view._search_fields) > 0,
            "search_placeholder": model_view.search_placeholder(),
            "filters": filters,
            "actions_in_list": dict(model_view._custom_actions_in_list),
            "actions_in_detail": dict(model_view._custom_actions_in_detail),
            "action_confirmations": dict(model_view._custom_actions_confirmation),
            "export_types": list(model_view.export_types),
            "permissions": {
                "can_create": model_view.can_create,
                "can_edit": model_view.can_edit,
                "can_delete": model_view.can_delete,
                "can_view_details": model_view.can_view_details,
                "can_export": model_view.can_export,
            },
            "name": model_view.name,
            "name_plural": model_view.name_plural,
            "identity": model_view.identity,
        }
    )


def _serialize_relation_value(value: Any, formatted: Any) -> Any:
    """Serialize a relationship value for the list view."""
    if value is None:
        return None
    if isinstance(value, (list, set, tuple)):
        items = []
        for item in value:
            try:
                items.append(
                    {
                        "pk": str(get_object_identifier(item)),
                        "repr": str(item),
                        "identity": slugify_class_name(item.__class__.__name__),
                    }
                )
            except Exception:
                try:
                    identity = slugify_class_name(item.__class__.__name__)
                    items.append({"repr": str(item), "identity": identity})
                except Exception:
                    items.append({"repr": repr(item)})
        return items
    try:
        return {
            "pk": str(get_object_identifier(value)),
            "repr": str(value),
            "identity": slugify_class_name(value.__class__.__name__),
        }
    except Exception:
        try:
            return str(value)
        except Exception:
            return repr(value)


async def _serialize_filters(model_view: "ModelView", request: Request) -> list[dict]:
    filters = []
    for f in model_view.get_filters():
        info: dict[str, Any] = {
            "name": f.parameter_name,
            "title": f.title,
            "has_operator": isinstance(f, OperationColumnFilter),
        }
        if isinstance(f, OperationColumnFilter):
            info["operations"] = f.get_operation_options_for_model(model_view.model)
        else:
            options = await f.lookups(
                request, model_view.model, model_view._run_arbitrary_query
            )
            info["options"] = [(str(v), str(label)) for v, label in options]
        filters.append(info)
    return filters


@api_login_required
async def api_detail(admin: "Admin", request: Request) -> Response:
    """Single record detail data."""
    identity = request.path_params["identity"]
    model_view = admin._find_model_view(identity)

    if not model_view.can_view_details or not model_view.is_accessible(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    model = await model_view.get_object_for_details(request)
    if not model:
        return JSONResponse({"error": "Not found"}, status_code=404)

    pk = str(get_object_identifier(model))

    fields = []
    for prop_name in model_view._details_prop_names:
        label = model_view._column_labels.get(prop_name, prop_name)
        value, formatted = await model_view.get_detail_value(model, prop_name)
        is_relation = prop_name in model_view._relation_names

        field_data: dict[str, Any] = {
            "name": prop_name,
            "label": label,
            "value": _serialize_value(value),
            "is_relation": is_relation,
        }

        if is_relation and value is not None:
            field_data["related"] = _serialize_relation_value(value, formatted)

        fields.append(field_data)

    return JSONResponse(
        {
            "fields": fields,
            "pk": pk,
            "repr": str(model),
            "permissions": {
                "can_edit": model_view.can_edit,
                "can_delete": model_view.can_delete,
            },
            "actions": dict(model_view._custom_actions_in_detail),
            "action_confirmations": dict(model_view._custom_actions_confirmation),
            "name": model_view.name,
            "identity": model_view.identity,
        }
    )


@api_login_required
async def api_form_schema(admin: "Admin", request: Request) -> Response:
    """Return form schema for create or edit."""
    identity = request.path_params["identity"]
    model_view = admin._find_model_view(identity)

    action = request.query_params.get("action", "create")
    pk = request.query_params.get("pk")

    if action == "create":
        if not model_view.can_create or not model_view.is_accessible(request):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        Form = await model_view.scaffold_form(model_view._form_create_rules)
        form = Form()
        obj = None
    elif action == "edit":
        if not model_view.can_edit or not model_view.is_accessible(request):
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        # Inject pk into path_params so get_object_for_edit can find it
        request.path_params["pk"] = pk
        obj = await model_view.get_object_for_edit(request)
        if not obj:
            return JSONResponse({"error": "Not found"}, status_code=404)
        Form = await model_view.scaffold_form(model_view._form_edit_rules)
        form = Form(
            obj=obj,
            data=admin._normalize_wtform_data(obj),
        )
    else:
        return JSONResponse({"error": "Invalid action"}, status_code=400)

    fields = []
    for field in form:
        if field.type == "HiddenField" and field.name == "csrf_token":
            continue
        field_info = _serialize_form_field(field, model_view)
        fields.append(field_info)

    return JSONResponse(
        {
            "fields": fields,
            "save_as": model_view.save_as,
            "save_as_continue": model_view.save_as_continue,
            "identity": model_view.identity,
            "name": model_view.name,
            "pk": pk,
        }
    )


def _serialize_form_field(field: Any, model_view: "ModelView") -> dict[str, Any]:
    """Serialize a single WTForm field to a JSON description."""
    field_type_name = type(field).__name__
    ui_type = FIELD_TYPE_MAP.get(field_type_name, "string")

    result: dict[str, Any] = {
        "name": field.name,
        "label": field.label.text if hasattr(field.label, "text") else str(field.label),
        "type": ui_type,
        "required": _is_required(field),
        "value": _serialize_field_value(field),
        "description": field.description or "",
    }

    # Widget args (readonly, disabled, etc.)
    widget_args = model_view.form_widget_args.get(field.name, {})
    if widget_args:
        result["widget_args"] = widget_args

    # Select fields: include choices
    if ui_type == "select" and hasattr(field, "iter_choices"):
        options = []
        for choice in field.iter_choices():
            val = choice[0]
            label = choice[1]
            if val == "__None":
                options.append({"value": "", "label": label or "---"})
            else:
                options.append({"value": str(val), "label": str(label)})
        result["options"] = options

    # Relation select fields: include current options
    if ui_type in ("relation_select", "relation_select_multiple"):
        options = []
        allow_blank = getattr(field, "allow_blank", False)
        if allow_blank:
            blank_text = getattr(field, "blank_text", "---") or "---"
            options.append({"value": "", "label": blank_text})
        if hasattr(field, "_select_data"):
            for pk_val, label_obj in field._select_data:
                get_label = getattr(field, "get_label", str)
                options.append(
                    {
                        "value": str(pk_val),
                        "label": str(get_label(label_obj)),
                    }
                )
        result["options"] = options
        # Also serialize the current value properly for relations
        if ui_type == "relation_select":
            data = field.data
            if data is not None and not isinstance(data, str):
                try:
                    result["value"] = str(get_object_identifier(data))
                except Exception:
                    result["value"] = str(data) if data else None
        elif ui_type == "relation_select_multiple":
            data = field.data
            if data is not None:
                try:
                    result["value"] = [
                        str(get_object_identifier(item))
                        if not isinstance(item, str)
                        else item
                        for item in data
                    ]
                except Exception:
                    result["value"] = [str(item) for item in data] if data else []

    # Ajax select fields: include URL and current value info
    if ui_type in ("ajax_select", "ajax_select_multiple"):
        result["ajax_url"] = model_view.ajax_lookup_url + f"?name={field.name}"
        if ui_type == "ajax_select" and field.data:
            try:
                loader = getattr(field, "loader", None)
                if loader and field.data:
                    result["value"] = str(field.data)
                    result["value_label"] = str(field.data)
            except Exception:
                pass
        elif ui_type == "ajax_select_multiple" and field.data:
            try:
                result["value"] = [str(v) for v in field.data]
            except Exception:
                pass

    # JSON field: serialize value as object, not string
    if ui_type == "json":
        if isinstance(field.data, str):
            try:
                result["value"] = json.loads(field.data)
            except (json.JSONDecodeError, TypeError):
                pass
        elif field.data is not None:
            result["value"] = field.data

    return result


@api_login_required
async def api_create(admin: "Admin", request: Request) -> Response:
    """Create a new model instance from JSON data."""
    identity = request.path_params["identity"]
    model_view = admin._find_model_view(identity)

    if not model_view.can_create or not model_view.is_accessible(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    Form = await model_view.scaffold_form(model_view._form_create_rules)

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        form_data = _json_to_formdata(body)
    else:
        form_data = await admin._handle_form_data(request)

    form = Form(form_data)

    if not form.validate():
        errors = {}
        for field_name, field_errors in form.errors.items():
            errors[field_name] = [str(e) for e in field_errors]
        return JSONResponse({"errors": errors}, status_code=400)

    form_data_dict = admin._denormalize_wtform_data(form.data, model_view.model)

    try:
        obj = await model_view.insert_model(request, form_data_dict)
    except Exception as e:
        logger.exception(e)
        return JSONResponse({"error": str(e)}, status_code=400)

    pk = str(get_object_identifier(obj))
    return JSONResponse(
        {
            "success": True,
            "pk": pk,
            "repr": str(obj),
            "identity": identity,
        }
    )


@api_login_required
async def api_edit(admin: "Admin", request: Request) -> Response:
    """Update an existing model instance."""
    identity = request.path_params["identity"]
    pk = request.path_params["pk"]
    model_view = admin._find_model_view(identity)

    if not model_view.can_edit or not model_view.is_accessible(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    model = await model_view.get_object_for_edit(request)
    if not model:
        return JSONResponse({"error": "Not found"}, status_code=404)

    Form = await model_view.scaffold_form(model_view._form_edit_rules)

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        form_data = _json_to_formdata(body)
    else:
        form_data = await admin._handle_form_data(request, model)

    form = Form(form_data)

    if not form.validate():
        errors = {}
        for field_name, field_errors in form.errors.items():
            errors[field_name] = [str(e) for e in field_errors]
        return JSONResponse({"errors": errors}, status_code=400)

    form_data_dict = admin._denormalize_wtform_data(form.data, model)

    try:
        obj = await model_view.update_model(request, pk=pk, data=form_data_dict)
    except Exception as e:
        logger.exception(e)
        return JSONResponse({"error": str(e)}, status_code=400)

    return JSONResponse(
        {
            "success": True,
            "pk": str(get_object_identifier(obj)),
            "repr": str(obj),
            "identity": identity,
        }
    )


@api_login_required
async def api_delete(admin: "Admin", request: Request) -> Response:
    """Delete one or more model instances."""
    identity = request.path_params["identity"]
    model_view = admin._find_model_view(identity)

    if not model_view.can_delete or not model_view.is_accessible(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    params = request.query_params.get("pks", "")
    pks = params.split(",") if params else []

    if not pks:
        return JSONResponse({"error": "No primary keys provided"}, status_code=400)

    deleted = []
    for pk in pks:
        model = await model_view.get_object_for_delete(pk)
        if not model:
            return JSONResponse(
                {"error": f"Object with pk={pk} not found"}, status_code=404
            )
        await model_view.delete_model(request, pk)
        deleted.append(pk)

    return JSONResponse({"success": True, "deleted": deleted})


@api_login_required
async def api_export(admin: "Admin", request: Request) -> Response:
    """Export model data (reuses existing export logic)."""
    identity = request.path_params["identity"]
    export_type = request.path_params["export_type"]
    model_view = admin._find_model_view(identity)

    if not model_view.can_export or not model_view.is_accessible(request):
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    if export_type not in model_view.export_types:
        return JSONResponse({"error": "Invalid export type"}, status_code=404)

    rows = await model_view.get_model_objects(
        request=request, limit=model_view.export_max_rows
    )
    return await model_view.export_data(rows, export_type=export_type)


@api_login_required
async def api_ajax_lookup(admin: "Admin", request: Request) -> Response:
    """Ajax lookup for relationship fields (Select2 compatible)."""
    identity = request.path_params["identity"]
    model_view = admin._find_model_view(identity)

    name = request.query_params.get("name")
    term = request.query_params.get("term", "")

    if not name:
        return JSONResponse({"error": "Missing name parameter"}, status_code=400)

    try:
        from spa_sqladmin.ajax import QueryAjaxModelLoader

        loader: QueryAjaxModelLoader = model_view._form_ajax_refs[name]
    except KeyError:
        return JSONResponse({"error": "Invalid ajax ref name"}, status_code=400)

    data = [loader.format(m) for m in await loader.get_list(term)]
    return JSONResponse({"results": data})


async def api_login(admin: "Admin", request: Request) -> Response:
    """Handle login via JSON."""
    if admin.authentication_backend is None:
        return JSONResponse({"error": "Authentication not configured"}, status_code=503)

    if request.method != "POST":
        return JSONResponse({"error": "Method not allowed"}, status_code=405)

    ok = await admin.authentication_backend.login(request)
    if not ok:
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)

    return JSONResponse({"success": True})


async def api_logout(admin: "Admin", request: Request) -> Response:
    """Handle logout."""
    if admin.authentication_backend is None:
        return JSONResponse({"error": "Authentication not configured"}, status_code=503)

    response = await admin.authentication_backend.logout(request)
    if isinstance(response, Response):
        return response

    return JSONResponse({"success": True})


async def api_auth_status(admin: "Admin", request: Request) -> Response:
    """Check current authentication status."""
    if admin.authentication_backend is None:
        return JSONResponse({"authenticated": True, "has_auth": False})

    response = await admin.authentication_backend.authenticate(request)
    if isinstance(response, Response):
        return JSONResponse({"authenticated": False, "has_auth": True})
    return JSONResponse({"authenticated": bool(response), "has_auth": True})


def _json_to_formdata(data: dict) -> FormData:
    """Convert a JSON dict to FormData for WTForms processing."""
    items: list[tuple[str, str | UploadFile]] = []
    for key, value in data.items():
        if isinstance(value, list):
            for v in value:
                items.append((key, str(v) if v is not None else ""))
        elif isinstance(value, bool):
            # WTForms BooleanField: "false" is in false_values
            items.append((key, str(value).lower()))
        elif isinstance(value, dict):
            # JSON fields: serialize back to string
            items.append((key, json.dumps(value, ensure_ascii=False)))
        elif value is None:
            items.append((key, ""))
        elif isinstance(value, str):
            items.append((key, _normalize_datetime_str(value)))
        else:
            items.append((key, str(value)))
    return FormData(items)


def _normalize_datetime_str(value: str) -> str:
    """Convert ISO 8601 datetime strings to WTForms-compatible format."""
    from datetime import datetime as dt
    from datetime import timezone as tz

    # Strip trailing Z (UTC) and replace with +00:00 for fromisoformat compatibility
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    # Try fromisoformat first — handles timezone-aware strings like
    # "2026-03-07T11:33:31+03:00"
    try:
        parsed = dt.fromisoformat(normalized)
        # Strip timezone info so WTForms (which expects naive datetimes) accepts it
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(tz.utc).replace(tzinfo=None)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # Fallback: try explicit strptime formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ):
        try:
            parsed = dt.strptime(value, fmt)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    return value
