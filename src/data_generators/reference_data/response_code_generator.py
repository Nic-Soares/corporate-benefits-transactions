import polars as pl
from datetime import datetime


def generate_response_codes():
    """Generate response codes for transaction processing"""
    response_codes = [
        {"code": "00", "description": "Approved", "category": "success"},
        {"code": "51", "description": "Insufficient funds", "category": "balance"},
        {"code": "14", "description": "Invalid card number", "category": "card"},
        {"code": "55", "description": "Incorrect PIN", "category": "password"},
        {"code": "96", "description": "System error", "category": "network"},
        {"code": "30", "description": "Format error", "category": "network"},
        {"code": "12", "description": "Invalid transaction", "category": "establishment"},
        {"code": "43", "description": "Stolen card", "category": "card"}
    ]
    
    codes_list = [
        {
            "response_code_id": f"RESP_{idx}",
            "response_code": code_info["code"],
            "response_description": code_info["description"],
            "response_category": code_info["category"],
            "created_at": datetime.now()
        }
        for idx, code_info in enumerate(response_codes, start=1)
    ]
    
    return pl.DataFrame(codes_list)


def generate_capture_technologies(business_data):
    """Generate capture technologies from business_data['transaction_technologies']"""
    capture_tech_list = []
    for idx, tech in enumerate(business_data['transaction_technologies'], start=1):
        capture_tech = {
            "technology_id": f"TECH_{idx:03d}",
            "technology_code": tech["code"],
            "technology_category": tech["category"],
            "technology_name": tech["name"],
            "requires_physical_card": tech["requires_physical_card"],
            "created_at": datetime.now()
        }
        capture_tech_list.append(capture_tech)

    return pl.DataFrame(capture_tech_list)
