from backend_api.api.core.decorators import endpoint
from backend_api.api.customer.dto import CreateCustomerDTO
from backend_api.api.customer.pipes import validate_create_customer
from backend_api.api.customer.service import create_customer as create_customer_service


@endpoint(methods=("POST",), dto=CreateCustomerDTO, pipes=(validate_create_customer,))
def create_customer(body: CreateCustomerDTO):
	return create_customer_service(body)
