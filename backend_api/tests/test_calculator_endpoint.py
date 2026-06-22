import importlib
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend_api.api.calculator.dto import CalculateDTO
from backend_api.api.core.exceptions import BadRequestException, UnprocessableEntityException


class TestCalculatorEndpoint(TestCase):
	def test_calculate_endpoint_is_importable_and_uses_decorator_bridge(self):
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
			module = importlib.import_module("backend_api.api.calculator.calculate")
			module = importlib.reload(module)

		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch(
				"backend_api.api.core.request.frappe.form_dict",
				{"left": " 8 ", "right": " 2 ", "operation": " divide ", "cmd": "ignored"},
			),
		):
			result = module.calculate()

		self.assertEqual(calls, [((), {})])
		self.assertEqual(module.calculate.whitelist_options, {"allow_guest": True})
		self.assertTrue(module.calculate.is_logged)
		self.assertEqual(
			result,
			{
				"operation": "divide",
				"left": 8.0,
				"right": 2.0,
				"result": 4.0,
			},
		)

	def test_calculate_endpoint_builds_dto_from_json_body(self):
		import backend_api.api.core.decorators as decorators

		def fake_log():
			def decorate(fn):
				return fn

			return decorate

		def fake_whitelist(**_options):
			def decorate(fn):
				return fn

			return decorate

		with (
			patch.object(decorators, "legacy_log", fake_log),
			patch.object(decorators.frappe, "whitelist", fake_whitelist),
		):
			module = importlib.import_module("backend_api.api.calculator.calculate")
			module = importlib.reload(module)

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"left": 7, "right": 5, "operation": "add"}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
			patch.object(module, "calculate_service", return_value={"result": 12.0}) as service,
		):
			result = module.calculate()

		self.assertEqual(result, {"result": 12.0})
		body = service.call_args.args[0]
		self.assertIsInstance(body, CalculateDTO)
		self.assertEqual(body.left, 7.0)
		self.assertEqual(body.right, 5.0)
		self.assertEqual(body.operation, "add")

	def test_calculate_endpoint_prefers_json_body_over_form_values(self):
		module = importlib.import_module("backend_api.api.calculator.calculate")

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"left": 9, "right": 3, "operation": "subtract"}'),
			),
			patch(
				"backend_api.api.core.request.frappe.form_dict",
				{"left": "100", "right": "100", "operation": "add"},
			),
		):
			result = module.calculate()

		self.assertEqual(result["result"], 6.0)
		self.assertEqual(result["operation"], "subtract")
		self.assertEqual(result["left"], 9.0)
		self.assertEqual(result["right"], 3.0)

	def test_calculate_endpoint_rejects_missing_left(self):
		module = importlib.import_module("backend_api.api.calculator.calculate")

		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch("backend_api.api.core.request.frappe.form_dict", {"right": "2", "operation": "add"}),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				module.calculate()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "LEFT_REQUIRED")

	def test_calculate_endpoint_rejects_invalid_operation(self):
		module = importlib.import_module("backend_api.api.calculator.calculate")

		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch(
				"backend_api.api.core.request.frappe.form_dict",
				{"left": "1", "right": "2", "operation": "mod"},
			),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				module.calculate()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "INVALID_OPERATION")

	def test_calculate_endpoint_rejects_divide_by_zero(self):
		module = importlib.import_module("backend_api.api.calculator.calculate")

		with (
			patch("backend_api.api.core.request.frappe.request", None),
			patch(
				"backend_api.api.core.request.frappe.form_dict",
				{"left": "10", "right": "0", "operation": "divide"},
			),
		):
			with self.assertRaises(UnprocessableEntityException) as ctx:
				module.calculate()

		self.assertEqual(ctx.exception.status_code, 422)
		self.assertEqual(ctx.exception.code, "DIVIDE_BY_ZERO")

	def test_calculate_endpoint_rejects_invalid_json_body(self):
		module = importlib.import_module("backend_api.api.calculator.calculate")

		with (
			patch("backend_api.api.core.request.frappe.request", SimpleNamespace(data="not-json")),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			with self.assertRaises(BadRequestException) as ctx:
				module.calculate()

		self.assertEqual(ctx.exception.status_code, 400)
		self.assertEqual(ctx.exception.code, "INVALID_JSON_BODY")

	def test_calculate_endpoint_ignores_unknown_extra_fields(self):
		module = importlib.import_module("backend_api.api.calculator.calculate")

		with (
			patch(
				"backend_api.api.core.request.frappe.request",
				SimpleNamespace(data='{"left": 1, "right": 2, "operation": "add", "extra": "x"}'),
			),
			patch("backend_api.api.core.request.frappe.form_dict", {}),
		):
			result = module.calculate()

		self.assertEqual(result["result"], 3.0)
		self.assertEqual(result["operation"], "add")
