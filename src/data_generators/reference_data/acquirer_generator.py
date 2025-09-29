import polars as pl
from datetime import datetime


def generate_acquirers(config_files_updated):
    """Generates DataFrame for Acquirers based on business rules"""
    acquirers = []
    for idx, name in enumerate(config_files_updated['acquirers'], start=1):
        acquirer = {
            "acquirer_id": f"ACQ_{idx}",
            "name": name,
            "active": True,
            "created_at": datetime.now()
        }
        acquirers.append(acquirer)
    return pl.DataFrame(acquirers)
