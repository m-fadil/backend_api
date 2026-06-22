import importlib
from unittest import TestCase
from unittest.mock import patch


class TestPingEndpoint(TestCase):
	def test_ping_endpoint_is_importable_and_uses_decorator_bridge(self):
		import backend_api.api.core.decorators as decorators

		calls = []

		def fake_log():
			def decorate(fn):
				def wrapped(*args, **kwargs):
					calls.append((args, kwargs))
					return fn(*args, **kwargs)

				setattr(wrapped, "is_logged", True)
				return wrapped

			return decorate

		def fake_whitelist(**options):
			def decorate(fn):
				fn.whitelist_options = options
				return fn

			return decorate

		with (
			patch.object(decorators, "legacy_log", fake_log),
			patch.object(decorators.frappe, "whitelist", fake_whitelist),
		):
			module = importlib.import_module("backend_api.api.ping.ping")
			module = importlib.reload(module)

		result = module.ping()

		self.assertEqual(result, {"message": "pong"})
		self.assertEqual(calls, [((), {})])
		self.assertEqual(module.ping.whitelist_options, {"allow_guest": True})
		self.assertTrue(module.ping.is_logged)
