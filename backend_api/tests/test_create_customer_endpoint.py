from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend_api.api.core.exceptions import BadRequestException, UnprocessableEntityException
from backend_api.api.customer.dto import CreateCustomerDTO
from backend_api.tests import load_endpoint_module


class TestCreateCustomerEndpoint(TestCase):
	def setUp(self):
		self.calls = []
		self.module = load_endpoint_module("backend_api.api.customer.create_customer", self.calls)

	def test_create_customer_endpoint_builds_dto_and_calls_service(self):
		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "  ACME  ", "email": " test@example.com "}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {"phone": " 08123 ", "cmd": "ignored"}),
			patch.object(
				self.module, "create_customer_service", return_value={"name": "CUST-0001"}
			) as service,
		):
			result = self.module.create_customer()

		self.assertEqual(result, {"name": "CUST-0001"})
		self.assertEqual(self.calls, [((), {})])
		self.assertEqual(
			self.module.create_customer.whitelist_options, {"allow_guest": False, "methods": ["POST"]}
		)
		self.assertTrue(self.module.create_customer.is_logged)

		body = service.call_args.args[0]
		self.assertIsInstance(body, CreateCustomerDTO)
		self.assertEqual(body.customer_name, "ACME")
		self.assertEqual(body.email, "test@example.com")
		self.assertEqual(body.phone, "08123")

	def test_create_customer_endpoint_rejects_missing_customer_name(self):
		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "   "}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				self.module.create_customer()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "CUSTOMER_NAME_REQUIRED")

	def test_create_customer_endpoint_rejects_invalid_email(self):
		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "ACME", "email": "not-an-email"}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				self.module.create_customer()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "INVALID_EMAIL")

	def test_create_customer_endpoint_rejects_invalid_json_body(self):
		with (
			patch("backend_api.api.core.request.frappe.request", SimpleNamespace(data="not-json")),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				self.module.create_customer()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_JSON_BODY")

	def test_create_customer_endpoint_maps_dto_typeerror_to_bad_request(self):
		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "ACME", "unknown": "value"}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				self.module.create_customer()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_REQUEST_PAYLOAD")
