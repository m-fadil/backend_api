from importlib import import_module, reload
from unittest.mock import patch


def stub_whitelist(**options):
	def decorate(fn):
		fn.whitelist_options = options
		return fn

	return decorate


def load_endpoint_module(name: str, calls: list | None = None):
	"""Reload module endpoint dengan legacy_log & frappe.whitelist yang di-stub.

	`endpoint` memasang decorator saat import, jadi module harus di-reload di dalam
	patch. Dipanggil dari setUp supaya tiap test punya module bersih: kalau menumpang
	reload test sebelumnya, urutan test jadi bagian dari kontrak."""
	import backend_api.api.core.decorators as decorators

	def stub_log():
		def decorate(fn):
			def wrapped(*args, **kwargs):
				if calls is not None:
					calls.append((args, kwargs))
				return fn(*args, **kwargs)

			wrapped.is_logged = True
			return wrapped

		return decorate

	with (
		patch.object(decorators, "legacy_log", stub_log),
		patch.object(decorators.frappe, "whitelist", stub_whitelist),
	):
		return reload(import_module(name))
