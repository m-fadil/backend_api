import importlib
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend_api.api.core.exceptions import BadRequestException, UnprocessableEntityException
from backend_api.api.customer.dto import CreateCustomerDTO


class TestCreateCustomerEndpoint(TestCase):
	def test_create_customer_endpoint_builds_dto_and_calls_service(self):
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
			module = importlib.import_module("backend_api.api.customer.create_customer")
			module = importlib.reload(module)

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "  ACME  ", "email": " test@example.com "}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {"phone": " 08123 ", "cmd": "ignored"}),
			patch.object(module, "create_customer_service", return_value={"name": "CUST-0001"}) as service,
		):
			result = module.create_customer()

		self.assertEqual(result, {"name": "CUST-0001"})
		self.assertEqual(calls, [((), {})])
		self.assertEqual(module.create_customer.whitelist_options, {"allow_guest": False})
		self.assertTrue(module.create_customer.is_logged)

		body = service.call_args.args[0]
		self.assertIsInstance(body, CreateCustomerDTO)
		self.assertEqual(body.customer_name, "ACME")
		self.assertEqual(body.email, "test@example.com")
		self.assertEqual(body.phone, "08123")

	def test_create_customer_endpoint_rejects_missing_customer_name(self):
		module = importlib.import_module("backend_api.api.customer.create_customer")

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "   "}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				module.create_customer()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "CUSTOMER_NAME_REQUIRED")

	def test_create_customer_endpoint_rejects_invalid_email(self):
		module = importlib.import_module("backend_api.api.customer.create_customer")

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "ACME", "email": "not-an-email"}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				module.create_customer()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "INVALID_EMAIL")

	def test_create_customer_endpoint_rejects_invalid_json_body(self):
		module = importlib.import_module("backend_api.api.customer.create_customer")

		with (
			patch("backend_api.api.core.request.frappe.request", SimpleNamespace(data="not-json")),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				module.create_customer()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_JSON_BODY")

	def test_create_customer_endpoint_maps_dto_typeerror_to_bad_request(self):
		module = importlib.import_module("backend_api.api.customer.create_customer")

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"customer_name": "ACME", "unknown": "value"}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				module.create_customer()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_REQUEST_PAYLOAD")
