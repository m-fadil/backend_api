from __future__ import annotations

import functools
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
	log: bool = True,
) -> Callable[[EndpointFn], EndpointFn]:
	def outer(fn: EndpointFn) -> EndpointFn:
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

			return fn(**raw)

		wrapped = legacy_log()(invoke) if log else invoke

		# ponytail: methods passthrough skipped. Add if repo Frappe version proves support on whitelist.
		return frappe.whitelist(allow_guest=guest)(wrapped)

	return outer
