from importlib import import_module, reload
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend_api.api.core.exceptions import BadRequestException, UnprocessableEntityException
from backend_api.api.core.logging import _to_legacy_error_response, log


class TestLegacyLoggingCompat(TestCase):
	def test_api_exception_maps_to_legacy_error_response(self):
		error = UnprocessableEntityException(
			"customer_name is required",
			code="CUSTOMER_NAME_REQUIRED",
			payload={"field": "customer_name"},
		)

		self.assertEqual(
			_to_legacy_error_response(error),
			{
				"_status_code": 422,
				"_title": "Unprocessable Entity",
				"_detail": "customer_name is required",
				"_code": "CUSTOMER_NAME_REQUIRED",
				"_payload": {"field": "customer_name"},
			},
		)

	def test_log_decorator_converts_api_exception_before_legacy_log(self):
		captured = {}

		class FakeApiModule:
			@staticmethod
			def log():
				def decorate(fn):
					def wrapped(*args, **kwargs):
						captured["response"] = fn(*args, **kwargs)
						return captured["response"]

					return wrapped

				return decorate

		with patch("backend_api.api.core.logging.legacy_api", FakeApiModule):
			decorated = log()(
				lambda: (_ for _ in ()).throw(
					BadRequestException("Invalid JSON body", code="INVALID_JSON_BODY")
				)
			)
			result = decorated()

		self.assertEqual(
			result,
			{
				"_status_code": 400,
				"_title": "Bad Request",
				"_detail": "Invalid JSON body",
				"_code": "INVALID_JSON_BODY",
			},
		)
		self.assertEqual(captured["response"], result)

	def test_ping_endpoint_uses_legacy_log_decorator(self):
		calls = []

		def fake_log():
			def decorate(fn):
				def wrapped(*args, **kwargs):
					calls.append((args, kwargs))
					return fn(*args, **kwargs)

				return wrapped

			return decorate

		with patch("backend_api.api.core.decorators.legacy_log", fake_log):
			ping_module = import_module("backend_api.api.ping.ping")
			ping_module = reload(ping_module)
			result = ping_module.ping()

		self.assertEqual(result, {"message": "pong"})
		self.assertEqual(calls, [((), {})])

	def test_create_customer_endpoint_uses_legacy_log_decorator(self):
		calls = []

		def fake_log():
			def decorate(fn):
				def wrapped(*args, **kwargs):
					calls.append((args, kwargs))
					return fn(*args, **kwargs)

				return wrapped

			return decorate

		with patch("backend_api.api.core.decorators.legacy_log", fake_log):
			customer_module = import_module("backend_api.api.customer.create_customer")
			customer_module = reload(customer_module)
			with patch.object(customer_module, "create_customer_service", return_value={"name": "CUST-0001"}):
				with (
					patch("backend_api.api.core.request.frappe.request", None),
					patch(
						"backend_api.api.core.request.frappe.form_dict",
						{"customer_name": "ACME"},
					),
				):
					result = customer_module.create_customer()

		self.assertEqual(result, {"name": "CUST-0001"})
		self.assertEqual(calls, [((), {})])

	def test_create_customer_invalid_json_maps_to_legacy_error_response(self):
		calls = []

		class FakeApiModule:
			@staticmethod
			def log():
				def decorate(fn):
					def wrapped(*args, **kwargs):
						calls.append((args, kwargs))
						return fn(*args, **kwargs)

					return wrapped

				return decorate

		with (
			patch("backend_api.api.core.logging.legacy_api", FakeApiModule),
			patch(
				"backend_api.api.core.decorators.legacy_log",
				log,
			),
		):
			customer_module = import_module("backend_api.api.customer.create_customer")
			customer_module = reload(customer_module)
			with (
				patch("backend_api.api.core.request.frappe.request", SimpleNamespace(data="not-json")),
				patch("backend_api.api.core.request.frappe.form_dict", {}),
			):
				result = customer_module.create_customer()

		self.assertEqual(calls, [((), {})])
		self.assertEqual(
			result,
			{
				"_status_code": 400,
				"_title": "Bad Request",
				"_detail": "Invalid JSON body",
				"_code": "INVALID_JSON_BODY",
			},
		)
