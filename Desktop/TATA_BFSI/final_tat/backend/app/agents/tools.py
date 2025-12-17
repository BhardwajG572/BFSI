from app.services.mock_crm import get_customer_by_phone
from app.core.logic import check_initial_eligibility, verify_salary_slip_logic

def tool_lookup_user(phone: str):
    """
    Finds a user in the mock DB.
    """
    user = get_customer_by_phone(phone)
    if user:
        return {"found": True, "data": user}
    return {"found": False, "data": None}

def tool_check_eligibility(amount: float, user_data: dict):
    """
    Runs the strict 2x limit math.
    """
    return check_initial_eligibility(
        requested_amount=float(amount),
        pre_approved_limit=user_data["pre_approved_limit"],
        credit_score=user_data["credit_score"]
    )