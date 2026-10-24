"""Warehouse asset maintenance registry.

Registers machines, records service dates, raises alerts for overdue
inspections and exports a report to ``maintenance.json``.
"""
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"

# Shared registry state. Module-level on purpose, but only ever mutated in
# place (never rebound), so no ``global`` statement is needed.
assets = {}
settings = {"service_interval_days": 90}

def register_asset(asset_id, machine_type):
    """Register a new asset, serviced today. Return True on success."""
    if not asset_id or not asset_id.strip():
        logging.warning("Rejected registration: asset id must not be empty")
        return False
    if asset_id in assets:
        logging.warning("Rejected registration: %s already exists", asset_id)
        return False
    assets[asset_id] = {"type": machine_type, "last_service": datetime.now().strftime(DATE_FORMAT)}
    print("Registered", asset_id, "- total assets:", len(assets))
    return True

def update_service_date(asset_id, date):
    """Set an asset's last service date (YYYY-MM-DD). Return True on success."""
    if asset_id not in assets:
        logging.warning("Could not update %s: unknown asset", asset_id)
        return False
    try:
        datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        logging.warning("Could not update %s: invalid date %r", asset_id, date)
        return False
    assets[asset_id]["last_service"] = date
    return True

def due_for_inspection():
    """Return the ids of assets whose last service is past the interval."""
    now = datetime.now()
    interval = timedelta(days=settings["service_interval_days"])
    return [
        asset_id
        for asset_id, info in assets.items()
        if now - datetime.strptime(info["last_service"], DATE_FORMAT) > interval
    ]

def change_interval(days):
    """Set the service interval in days (must be a positive integer)."""
    if not isinstance(days, int) or days <= 0:
        logging.warning("Rejected interval %r: must be a positive integer", days)
        return False
    settings["service_interval_days"] = days
    return True

def export_service_report(file="maintenance.json"):
    """Write the asset registry to a JSON report file."""
    with open(file, "w", encoding="utf-8") as report:
        json.dump(assets, report, indent=2)
    print("Report written to " + file)

def write_scratch_copy():
    """Write a scratch copy of the registry to a secure temporary file."""
    file_descriptor, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as scratch:
        json.dump(assets, scratch)
    print("Scratch copy at", path)

def print_alerts():
    """Print an alert for every asset that is overdue for inspection."""
    for asset_id in due_for_inspection():
        print("ALERT: inspection overdue for", asset_id, assets[asset_id]["type"])

def main():
    """Run the demo workflow."""
    register_asset("FL-01", "Forklift")
    register_asset("CV-07", "Conveyor")
    register_asset("", "Pallet Jack")
    register_asset("FL-01", "Crane")
    update_service_date("FL-01", "2025-01-15")
    update_service_date("XX-99", "2025-02-01")
    change_interval(-30)
    try:
        date = input("Last service date for CV-07 (YYYY-MM-DD, Enter to skip): ")
    except EOFError:
        date = ""
    if date:
        update_service_date("CV-07", date)
    if not assets:
        logging.error("No assets registered; nothing to report")
        return
    print_alerts()
    export_service_report()
    write_scratch_copy()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
