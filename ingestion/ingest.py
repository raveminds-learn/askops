"""
ingestion/ingest.py
Populates LanceDB with mock log data from all 5 trade scenarios.
Run once: python ingestion/ingest.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mock_data import DATADOG_LOGS
from storage.lancedb_store import ingest_logs


def run():
    print("Starting ingestion...")
    all_logs = []

    for trade_id, logs in DATADOG_LOGS.items():
        for log in logs:
            all_logs.append({**log, "trade_id": trade_id, "source": "datadog"})

    inserted = ingest_logs(all_logs)
    print(f"Done. Inserted {inserted} new log entries into LanceDB.")


if __name__ == "__main__":
    run()
