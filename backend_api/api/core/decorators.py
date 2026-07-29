from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from typing import Any

import frappe

from .exceptions import BadRequestException
from .logging import log as legacy_log
from .pipes import run_default_pipes, run_pipes
from .request import get_request_data

EndpointFn = Callable[..., Any]


def endpoint(
	*,
	guest: bool = False,
	dto: type | None = None,
	pipes: tuple[Callable[[dict[str, Any]], dict[str, Any]], ...] = (),
	methods: tuple[str, ...] = ("GET",),
) -> Callable[[EndpointFn], EndpointFn]:
	def outer(fn: EndpointFn) -> EndpointFn:
		signature = inspect.signature(fn)
		takes_kwargs = any(p.kind is p.VAR_KEYWORD for p in signature.parameters.values())

		@functools.wraps(fn)
		def invoke(*args: Any, **kwargs: Any) -> Any:
			raw = get_request_data(kwargs)
			raw = run_default_pipes(raw)
			raw = run_pipes(raw, pipes)

			if dto is not None:
				try:
					body = dto(**raw)
				except TypeError as exc:
					raise BadRequestException(
						"Invalid request payload",
						code="INVALID_REQUEST_PAYLOAD",
					) from exc
				return fn(body)

			# form_dict membawa semua query param, jadi buang yang tidak diterima fn
			# dan cek kecocokan argumen sebelum memanggil: mismatch = 400, bukan 500.
			if not takes_kwargs:
				raw = {key: value for key, value in raw.items() if key in signature.parameters}
			try:
				signature.bind(**raw)
			except TypeError as exc:
				raise BadRequestException(
					"Invalid request payload",
					code="INVALID_REQUEST_PAYLOAD",
				) from exc

			return fn(**raw)

		# legacy_log wajib: di situlah ApiException diterjemahkan ke response legacy.
		# Melewatinya bikin tiap error validasi lolos mentah ke Frappe jadi 500.
		return frappe.whitelist(allow_guest=guest, methods=list(methods))(legacy_log()(invoke))

	return outer
