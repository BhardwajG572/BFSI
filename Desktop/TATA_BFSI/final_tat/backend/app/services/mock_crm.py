import json
import os
from typing import Optional, Dict

# --- PATH CALCULATION FIX ---
# Current file location: .../backend/app/services/mock_crm.py
# Your target file:      .../backend/app/data/customers.json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go UP one level (to 'app'), then DOWN into 'data'
DATA_FILE_PATH = os.path.join(CURRENT_DIR, "..", "data", "customers.json")

# Clean up the path (resolves the '..')
DATA_FILE_PATH = os.path.normpath(DATA_FILE_PATH)

def get_customer_by_phone(phone: str) -> Optional[Dict]:
    """
    Simulates fetching KYC details from a CRM server.
    """
    print(f"DEBUG: Reading DB from: {DATA_FILE_PATH}")
    
    if not os.path.exists(DATA_FILE_PATH):
        print("❌ Error: customers.json NOT found. Check the path above!")
        return None

    try:
        with open(DATA_FILE_PATH, "r") as f:
            customers = json.load(f)
            
        for cust in customers:
            if cust["phone"] == phone:
                return cust
        return None
    except Exception as e:
        print(f"❌ Error reading DB: {e}")
        return None