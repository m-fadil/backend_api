from backend_api.api.core.exceptions import UnprocessableEntityException


def validate_create_customer(data: dict) -> dict:
	customer_name = data.get("customer_name")
	if not customer_name:
		raise UnprocessableEntityException(
			"customer_name is required",
			code="CUSTOMER_NAME_REQUIRED",
		)

	email = data.get("email")
	if email and "@" not in email:
		raise UnprocessableEntityException("Invalid email", code="INVALID_EMAIL")

	return data
