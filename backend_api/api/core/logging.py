from __future__ import annotations

from collections.abc import Callable
from typing import Any

import api as legacy_api

from .exceptions import ApiException


def _get_error_title(status_code: int) -> str:
	return {
		400: "Bad Request",
		401: "Unauthorized",
		403: "Forbidden",
		404: "Not Found",
		405: "Method Not Allowed",
		406: "Not Acceptable",
		408: "Request Timeout",
		409: "Conflict",
		410: "Gone",
		412: "Precondition Failed",
		413: "Payload Too Large",
		415: "Unsupported Media Type",
		418: "I'm a teapot",
		422: "Unprocessable Entity",
		500: "Internal Server Error",
		501: "Not Implemented",
		502: "Bad Gateway",
		503: "Service Unavailable",
		504: "Gateway Timeout",
		505: "HTTP Version Not Supported",
	}.get(status_code, "Error")


def _to_legacy_error_response(exc: ApiException) -> dict[str, Any]:
	response = {
		"_status_code": exc.status_code,
		"_title": _get_error_title(exc.status_code),
		"_detail": exc.message,
	}
	if exc.code:
		response["_code"] = exc.code
	if exc.payload:
		response["_payload"] = exc.payload
	return response


def log():
	legacy_log = legacy_api.log()

	def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
		def adapted(*args: Any, **kwargs: Any) -> Any:
			try:
				return fn(*args, **kwargs)
			except ApiException as exc:
				return _to_legacy_error_response(exc)

		return legacy_log(adapted)

	return decorate
