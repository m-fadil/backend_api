from unittest import TestCase
from unittest.mock import patch

from backend_api.api.core.exceptions import BadRequestException
from backend_api.tests import load_endpoint_module, stub_whitelist


class TestPingEndpoint(TestCase):
	def setUp(self):
		self.calls = []
		self.module = load_endpoint_module("backend_api.api.ping.ping", self.calls)

	def test_ping_endpoint_is_importable_and_uses_decorator_bridge(self):
		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			result = self.module.ping()

		self.assertEqual(result, {"message": "pong"})
		self.assertEqual(self.calls, [((), {})])
		self.assertEqual(self.module.ping.whitelist_options, {"allow_guest": True, "methods": ["GET"]})
		self.assertTrue(self.module.ping.is_logged)

	def test_ping_endpoint_ignores_extra_query_params(self):
		"""form_dict membawa semua query param; endpoint tanpa DTO tidak boleh 500 karenanya."""
		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch("backend_api.api.core.request.frappe.form_dict", {"foo": "1", "cmd": "ignored"}),
		):
			self.assertEqual(self.module.ping(), {"message": "pong"})

	def test_endpoint_without_dto_rejects_missing_required_argument(self):
		"""Argumen wajib yang tidak dikirim client = 400, bukan TypeError yang jadi 500."""
		import backend_api.api.core.decorators as decorators

		with (
			patch.object(decorators, "legacy_log", lambda: lambda fn: fn),
			patch.object(decorators.frappe, "whitelist", stub_whitelist),
		):

			@decorators.endpoint()
			def needs_arg(required):
				return {"required": required}

		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				needs_arg()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_REQUEST_PAYLOAD")

	def test_endpoint_without_dto_passes_declared_arguments(self):
		import backend_api.api.core.decorators as decorators

		with (
			patch.object(decorators, "legacy_log", lambda: lambda fn: fn),
			patch.object(decorators.frappe, "whitelist", stub_whitelist),
		):

			@decorators.endpoint()
			def echo(required):
				return {"required": required}

		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch("backend_api.api.core.request.frappe.form_dict", {"required": " x ", "extra": "1"}),
		):
			self.assertEqual(echo(), {"required": "x"})
