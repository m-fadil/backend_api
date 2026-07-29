from __future__ import annotations

import json
from json import JSONDecodeError
from typing import Any

import frappe

from .exceptions import BadRequestException

# tuple, bukan set: `in` harus pakai == supaya body bertipe unhashable (dict, list)
# sampai ke pengecekan tipe di bawah, bukan mental jadi TypeError di guard ini.
EMPTY_REQUEST_DATA = ("", b"", None)


def _safe_frappe_value(owner: Any, name: str, default: Any) -> Any:
	try:
		return getattr(owner, name)
	except RuntimeError:
		return default


def _parse_json_body(raw_body: Any) -> dict[str, Any]:
	if raw_body in EMPTY_REQUEST_DATA:
		return {}

	if isinstance(raw_body, bytes):
		try:
			raw_body = raw_body.decode()
		except UnicodeDecodeError as exc:
			raise BadRequestException("Invalid JSON body", code="INVALID_JSON_BODY") from exc

	if isinstance(raw_body, str):
		try:
			body = json.loads(raw_body)
		except JSONDecodeError as exc:
			raise BadRequestException("Invalid JSON body", code="INVALID_JSON_BODY") from exc
	elif isinstance(raw_body, dict):
		body = raw_body
	else:
		return {}

	if not isinstance(body, dict):
		raise BadRequestException("JSON body must be an object", code="INVALID_JSON_BODY")

	return body


def get_request_data(kwargs: dict[str, Any] | None = None) -> dict[str, Any]:
	data = dict(kwargs or {})

	request = _safe_frappe_value(frappe, "request", None)
	request_data = _safe_frappe_value(request, "data", None) if request is not None else None
	data.update(_parse_json_body(request_data))

	form_dict = _safe_frappe_value(frappe, "form_dict", {}) or {}
	for key, value in dict(form_dict).items():
		data.setdefault(key, value)

	data.pop("cmd", None)
	return data
