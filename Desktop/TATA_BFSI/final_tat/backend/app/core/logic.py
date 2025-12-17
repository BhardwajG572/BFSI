def calculate_emi(principal: float, rate_pa: float, tenure_years: int) -> float:
    """
    Calculates EMI using standard formula.
    Rate is per annum, converted to monthly.
    """
    if principal <= 0 or tenure_years <= 0:
        return 0.0
    
    monthly_rate = rate_pa / (12 * 100)
    months = tenure_years * 12
    
    emi = (principal * monthly_rate * ((1 + monthly_rate) ** months)) / \
          (((1 + monthly_rate) ** months) - 1)
    
    return round(emi, 2)

def check_initial_eligibility(requested_amount: float, 
                              pre_approved_limit: float, 
                              credit_score: int) -> dict:
    """
    Stage 1 Check: Based on Limits and Score ONLY.
    """
    # [cite_start]Rule: Reject if credit score < 700 [cite: 1, 14, 27]
    if credit_score < 700:
        return {
            "status": "REJECTED",
            "reason": "Credit Score below 700 threshold."
        }

    # [cite_start]Rule: Reject if > 2x pre-approved limit [cite: 27]
    if requested_amount > (2 * pre_approved_limit):
        return {
            "status": "REJECTED",
            "reason": f"Requested amount {requested_amount} exceeds 2x limit of {pre_approved_limit}."
        }

    # [cite_start]Rule: If <= Limit, Approve Instantly [cite: 27]
    if requested_amount <= pre_approved_limit:
        return {
            "status": "APPROVED_INSTANT",
            "reason": "Within pre-approved limit."
        }

    # [cite_start]Rule: If > Limit but <= 2x Limit, Request Salary Slip [cite: 27]
    return {
        "status": "REQUIRES_SALARY_SLIP",
        "reason": "Amount exceeds pre-approved limit but is within 2x multiplier."
    }

def verify_salary_slip_logic(requested_amount: float, 
                             salary: float, 
                             tenure_years: int = 3, 
                             interest_rate: float = 12.0) -> dict:
    """
    Stage 2 Check: Only called if status was 'REQUIRES_SALARY_SLIP'.
    [cite_start]Rule: Approve only if expected EMI <= 50% of salary [cite: 27]
    """
    emi = calculate_emi(requested_amount, interest_rate, tenure_years)
    
    if emi <= (0.5 * salary):
        return {
            "status": "APPROVED_WITH_DOCS",
            "emi": emi,
            "reason": f"EMI ({emi}) is within 50% of salary ({salary})."
        }
    else:
        return {
            "status": "REJECTED",
            "emi": emi,
            "reason": f"EMI ({emi}) exceeds 50% of monthly salary."
        }

def get_emi_options_table(amount: float) -> str:
    """
    Generates a Markdown table with dynamic tenure options.
    - Small loans: 12, 24, 36 months
    - Large loans (> 5 Lakhs): 36, 48, 60 months
    """
    rate = 12.0
    
    # --- SMART LOGIC: Tenure selection based on Amount ---
    if amount >= 500000:
        tenures = [36, 48, 60]
        title_suffix = "(Long Tenure for Low EMI)"
    else:
        tenures = [12, 24, 36]
        title_suffix = "(Standard Plans)"
    
    # Calculate EMIs
    emi_1 = calculate_emi(amount, rate, tenures[0]/12)
    emi_2 = calculate_emi(amount, rate, tenures[1]/12)
    emi_3 = calculate_emi(amount, rate, tenures[2]/12)
    
    # Create Table
    table = f"""
    **Loan Offer for ₹{amount:,.0f} {title_suffix}**
    
    | Tenure | Monthly EMI | Total Interest |
    | :--- | :--- | :--- |
    | **{tenures[0]} Months** | ₹{emi_1:,.0f} | ₹{(emi_1*tenures[0])-amount:,.0f} |
    | **{tenures[1]} Months** | ₹{emi_2:,.0f} | ₹{(emi_2*tenures[1])-amount:,.0f} |
    | **{tenures[2]} Months** | ₹{emi_3:,.0f} | ₹{(emi_3*tenures[2])-amount:,.0f} |
    
    *Please type '{tenures[0]}', '{tenures[1]}', or '{tenures[2]}' to proceed.*
    """
    return table