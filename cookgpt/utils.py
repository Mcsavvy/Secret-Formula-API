"""Utilities"""
from datetime import datetime, timezone
from typing import Any, Callable, NoReturn, Optional, ParamSpec, TypeVar, Union

from apiflask import HTTPError
from apiflask.schemas import EmptySchema, FileSchema
from apiflask.types import SchemaType
from flask import jsonify as flask_jsonify
from flask import make_response


def jsonify(data, status=200):  # pragma: no cover
    """jsonify with status code"""
    return make_response(flask_jsonify(data), status)


def abort(status_code: int, message: str) -> NoReturn:
    """abort with status code and message"""
    raise HTTPError(status_code, message)


def no_ms(dt: datetime) -> datetime:
    """removes the micro seconds on a datetime"""
    return dt.replace(microsecond=0)


def utcnow() -> datetime:
    """return current datetime in utc timezone without ms"""
    return no_ms(datetime.now(tz=timezone.utc))


def utcnow_from__ts(timestamp) -> datetime:
    """
    convert a timestamp into a datetime with utc timezone without ms
    """
    return no_ms(datetime.fromtimestamp(timestamp, tz=timezone.utc))


def add_response(
    operation: dict,
    status_code: str,
    schema: Union[SchemaType, dict],
    description: str,
    example: Optional[Any] = None,
    examples: Optional[dict[str, Any]] = None,
    links: Optional[dict[str, Any]] = None,
    content_type: Optional[str] = "application/json",
) -> None:
    """Add response to operation.

    *Version changed: 1.3.0*

    - Add parameter `content_type`.

    *Version changed: 0.10.0*

    - Add `links` parameter.
    """
    operation["responses"][status_code] = {}
    if status_code != "204":
        if isinstance(schema, FileSchema):
            schema = {"type": schema.type, "format": schema.format}
        elif isinstance(schema, EmptySchema):
            schema = {}
        operation["responses"][status_code]["content"] = {
            content_type: {"schema": schema}
        }
    operation["responses"][status_code]["description"] = description
    if example is not None:
        operation["responses"][status_code]["content"][content_type][
            "example"
        ] = example
    if examples is not None:
        operation["responses"][status_code]["content"][content_type][
            "examples"
        ] = examples
    if links is not None:
        operation["responses"][status_code]["links"] = links


def api_output(
    schema: SchemaType,
    status_code: int,
    description: str,
    example: Optional[Any] = None,
    examples: Optional[dict[str, Any]] = None,
    links: Optional[dict[str, Any]] = None,
    content_type: str = "application/json",
):
    """Add a response to the Openapi spec"""

    if isinstance(schema, type):
        schema = schema()

    def decorator(func):  # pragma: no cover
        if not hasattr(func, "_spec"):
            func._spec = {}
        if func._spec.get("responses", None) is None:
            func._spec["responses"] = {}
        add_response(
            func._spec,
            schema=schema,
            status_code=str(status_code),
            description=description,
            example=example,
            examples=examples,
            links=links,
            content_type=content_type,
        )
        return func

    return decorator


P = ParamSpec("P")
R = TypeVar("R")


def make_field(
    field: Callable[P, R],
    description: Optional[str] = None,
    example: Optional[Any] = None,
    *args,
    **kwargs,
) -> Callable[P, R]:
    """Make a field with default metadata."""
    metadata = {"description": description, "example": example}
    if example is not None:
        metadata["example"] = example
    if description is not None:
        metadata["description"] = description

    def helper(*a: P.args, **k: P.kwargs) -> R:
        metadata.update(k.pop("metadata", {}))  # type: ignore
        k["metadata"] = metadata
        k.update(kwargs)
        a += args  # type: ignore
        return field(*a, **k)

    return helper


def cast_func_to(type: Callable[P, R]):
    """cast function"""

    def cast(func: Callable) -> Callable[P, R]:
        return func  # type: ignore

    return cast
