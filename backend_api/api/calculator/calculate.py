from backend_api.api.calculator.dto import CalculateDTO
from backend_api.api.calculator.pipes import validate_calculation
from backend_api.api.calculator.service import calculate as calculate_service
from backend_api.api.core.decorators import endpoint


@endpoint(methods=("GET", "POST"), guest=True, dto=CalculateDTO, pipes=(validate_calculation,))
def calculate(body: CalculateDTO):
	return calculate_service(body)
