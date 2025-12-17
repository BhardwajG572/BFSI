from fpdf import FPDF
import os
import random
from datetime import datetime

class PDF(FPDF):
    def header(self):
        # --- COMPANY BRANDING ---
        self.set_font('Arial', 'B', 20)
        self.set_text_color(0, 51, 102) # Tata Blue color (Dark Blue)
        self.cell(0, 10, 'TATA CAPITAL', 0, 1, 'L')
        
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100) # Grey
        self.cell(0, 5, 'Financial Services Limited', 0, 1, 'L')
        
        # Line break
        self.ln(5)
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.5)
        self.line(10, 30, 200, 30)
        self.ln(10)

    def footer(self):
        # --- PROFESSIONAL FOOTER ---
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 5, 'Registered Office: 11th Floor, Tower A, Peninsula Business Park, Ganpatrao Kadam Marg, Lower Parel, Mumbai - 400013', 0, 1, 'C')
        self.cell(0, 5, 'This is a computer-generated document and does not require a physical signature.', 0, 1, 'C')
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'R')

def generate_sanction_letter(user_name: str, phone: str, amount: float, tenure: int, emi: float):
    """
    Generates a Professional Sanction Letter.
    """
    # 1. Setup PDF
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 2. Reference Details
    ref_no = f"TCL/PL/{datetime.now().strftime('%Y%m')}/{random.randint(10000, 99999)}"
    date_str = datetime.now().strftime('%B %d, %Y')
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(100, 6, f"Ref No: {ref_no}", 0, 0)
    pdf.cell(0, 6, f"Date: {date_str}", 0, 1, 'R')
    pdf.ln(5)

    # 3. Applicant Details
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, f"To,", 0, 1)
    pdf.cell(0, 6, f"{user_name}", 0, 1)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 6, f"Registered Mobile: +91-{phone}", 0, 1)
    pdf.ln(8)

    # 4. Subject Line
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230) # Light Grey background
    pdf.cell(0, 8, "Subject: Sanction of Personal Loan Application", 0, 1, 'L', fill=True)
    pdf.ln(5)

    # 5. Salutation & Opening
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, (
        f"Dear {user_name},\n\n"
        "We thank you for choosing Tata Capital Financial Services Limited for your financial needs. "
        "We are pleased to inform you that based on your application and credit appraisal, "
        "we have sanctioned a Personal Loan to you under the following terms and conditions:"
    ))
    pdf.ln(5)

    # 6. The "Deal Sheet" (Table)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(245, 245, 245)
    
    # Table Header
    pdf.cell(95, 8, "Description", 1, 0, 'C', fill=True)
    pdf.cell(95, 8, "Details", 1, 1, 'C', fill=True)
    
    # Table Rows
    def add_row(label, value):
        pdf.set_font("Arial", '', 10)
        pdf.cell(95, 8, f"  {label}", 1, 0)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(95, 8, f"  {value}", 1, 1)

    add_row("Sanctioned Loan Amount", f"Rs. {amount:,.2f}")
    add_row("Loan Tenure", f"{tenure} Months")
    add_row("Rate of Interest (Fixed)", "12.00% p.a.")
    add_row("Equated Monthly Installment (EMI)", f"Rs. {emi:,.2f}")
    add_row("Processing Fee", "Rs. 0.00 (Waived)")
    add_row("Pre-payment Charges", "Nil (After 12 EMIs)")
    
    pdf.ln(8)

    # 7. Terms and Conditions (The "Legal" Look)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "Key Terms and Conditions:", 0, 1)
    
    pdf.set_font("Arial", '', 9)
    terms = [
        "1. The loan shall be disbursed to your salary account linked during the verification process.",
        "2. Interest calculation is based on monthly reducing balance.",
        "3. This sanction is valid for 30 days from the date of issue.",
        "4. Repayment must be made via NACH/e-Mandate on the 5th of every month.",
        "5. Default in payment will attract penal interest @ 2% per month on the overdue amount."
    ]
    
    for term in terms:
        pdf.multi_cell(0, 5, term)
        pdf.ln(1)
    
    pdf.ln(10)

    # 8. Signatory Area
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "For Tata Capital Financial Services Limited,", 0, 1)
    
    # Simulate a Digital Stamp/Signature
    pdf.ln(5)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(60, 15, "[ Digitally Signed by Authorized Officer ]", 1, 1, 'C')
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(2)
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, "Authorized Signatory", 0, 1)

    # 9. Save File
    filename = f"Sanction_Letter_{phone}_{random.randint(10,99)}.pdf"
    save_dir = os.path.join(os.path.dirname(__file__), "../../static")
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, filename)
    pdf.output(file_path)
    
    return file_path