from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from backend_api.api.calculator.dto import CalculateDTO


def calculate(body: "CalculateDTO") -> dict[str, float | str]:
	operations = {
		"add": body.left + body.right,
		"subtract": body.left - body.right,
		"multiply": body.left * body.right,
		"divide": body.left / body.right,
	}
	result = operations[body.operation]
	return {
		"operation": body.operation,
		"left": body.left,
		"right": body.right,
		"result": result,
	}
