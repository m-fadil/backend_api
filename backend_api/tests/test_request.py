from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend_api.api.core.exceptions import BadRequestException
from backend_api.api.core.request import get_request_data


class TestRequest(TestCase):
	def test_get_request_data_merges_kwargs_body_and_form(self):
		fake_request = SimpleNamespace(data='{"body_only": "value", "shared": " body "}')
		fake_form_dict = {"form_only": "value", "shared": "form", "cmd": "ignored"}

		with (
			patch("backend_api.api.core.request.frappe.request", fake_request),
			patch("backend_api.api.core.request.frappe.form_dict", fake_form_dict),
		):
			result = get_request_data({"kwarg_only": "value", "shared": "kwarg"})

		self.assertEqual(
			result,
			{
				"kwarg_only": "value",
				"body_only": "value",
				"form_only": "value",
				"shared": " body ",
			},
		)

	def test_get_request_data_rejects_invalid_json_body(self):
		fake_request = SimpleNamespace(data="not-json")

		with (
			patch("backend_api.api.core.request.frappe.request", fake_request),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				get_request_data({"name": "ok"})

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_JSON_BODY")

	def test_get_request_data_accepts_bytes_json_body(self):
		fake_request = SimpleNamespace(data=b'{"name": "bytes-body"}')

		with (
			patch("backend_api.api.core.request.frappe.request", fake_request),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			result = get_request_data()

		self.assertEqual(result, {"name": "bytes-body"})

	def test_get_request_data_treats_empty_body_as_empty_payload(self):
		for raw_body in (None, "", b""):
			with self.subTest(raw_body=raw_body):
				with (
					patch("backend_api.api.core.request.frappe.request", SimpleNamespace(data=raw_body)),
					patch("backend_api.api.core.request.frappe.form_dict", {"name": "form"}),
				):
					result = get_request_data({"source": "kwargs"})

				self.assertEqual(result, {"source": "kwargs", "name": "form"})

	def test_get_request_data_rejects_non_utf8_bytes_body(self):
		fake_request = SimpleNamespace(data=b"\xff")

		with (
			patch("backend_api.api.core.request.frappe.request", fake_request),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				get_request_data()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_JSON_BODY")

	def test_get_request_data_rejects_non_object_json_body(self):
		fake_request = SimpleNamespace(data='["not", "object"]')

		with (
			patch("backend_api.api.core.request.frappe.request", fake_request),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				get_request_data()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_JSON_BODY")
