from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.utils import alerts


class AlertRobustnessTests(unittest.TestCase):
    """Tests for numeric normalization, cross-process dedup, and history pruning."""

    def setUp(self) -> None:
        self.original_path = alerts.ALERTS_PATH
        alerts._last_persisted_alert.clear()

    def tearDown(self) -> None:
        alerts.ALERTS_PATH = self.original_path
        alerts._last_persisted_alert.clear()

    def test_numeric_normalization_deduplicates_jittery_latency(self) -> None:
        """Latency values bucketed into 200ms bins should dedup minor jitter."""
        alert_base = {
            "type": "service_latency",
            "severity": "warning",
            "message": "test",
            "metric": "latency.p95_ms",
            "threshold": 300,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            alerts.ALERTS_PATH = Path(tmpdir) / "alerts.jsonl"
            alerts._last_persisted_alert.clear()

            alert1 = {**alert_base, "value": 325.0}
            alert2 = {**alert_base, "value": 355.0}
            alert3 = {**alert_base, "value": 520.0}

            out1 = alerts.persist_alerts([alert1], throttle_minutes=60)
            self.assertIsNotNone(out1)

            out2 = alerts.persist_alerts([alert2], throttle_minutes=60)
            self.assertIsNone(out2, "Alert with latency 325->355 (same 200ms bucket) should not persist")

            out3 = alerts.persist_alerts([alert3], throttle_minutes=60)
            self.assertIsNotNone(out3, "Alert with latency 520 (different bucket) should persist")

            out_path = Path(str(out1))
            lines = out_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)

    def test_alert_history_pruning_by_age(self) -> None:
        """Alerts older than ALERTS_RETENTION_DAYS should be pruned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            alerts.ALERTS_PATH = Path(tmpdir) / "alerts.jsonl"
            alerts._last_persisted_alert.clear()

            alerts.ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)

            cutoff = datetime.now(timezone.utc) - timedelta(days=alerts.ALERTS_RETENTION_DAYS)
            old_ts = (cutoff - timedelta(hours=1)).isoformat()
            recent_ts = datetime.now(timezone.utc).isoformat()

            records = [
                {"type": "test_old", "message": "old", "timestamp": old_ts},
                {"type": "test_recent", "message": "recent", "timestamp": recent_ts},
            ]

            with alerts.ALERTS_PATH.open("w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")

            alerts._prune_alert_history()

            remaining = alerts.ALERTS_PATH.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(remaining), 1)
            self.assertIn("test_recent", remaining[0])

    def test_alert_history_pruning_by_record_count(self) -> None:
        """Keeping only ALERTS_MAX_RECORDS most recent alerts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            alerts.ALERTS_PATH = Path(tmpdir) / "alerts.jsonl"
            alerts._last_persisted_alert.clear()

            alerts.ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)

            now = datetime.now(timezone.utc)
            with alerts.ALERTS_PATH.open("w", encoding="utf-8") as f:
                for i in range(alerts.ALERTS_MAX_RECORDS + 100):
                    ts = (now - timedelta(seconds=i)).isoformat()
                    record = {"type": "test", "index": i, "timestamp": ts}
                    f.write(json.dumps(record) + "\n")

            alerts._prune_alert_history()

            remaining = alerts.ALERTS_PATH.read_text(encoding="utf-8").strip().splitlines()
            self.assertLessEqual(len(remaining), alerts.ALERTS_MAX_RECORDS)

    def test_malformed_records_are_retained_on_prune(self) -> None:
        """Records without timestamp or malformed JSON should not be dropped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            alerts.ALERTS_PATH = Path(tmpdir) / "alerts.jsonl"
            alerts._last_persisted_alert.clear()

            alerts.ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)

            records = [
                {"type": "valid", "message": "has timestamp", "timestamp": datetime.now(timezone.utc).isoformat()},
                {"type": "no_ts", "message": "no timestamp field"},
                "not_json_at_all",
            ]

            with alerts.ALERTS_PATH.open("w", encoding="utf-8") as f:
                for record in records:
                    if isinstance(record, dict):
                        f.write(json.dumps(record) + "\n")
                    else:
                        f.write(record + "\n")

            alerts._prune_alert_history()

            remaining = alerts.ALERTS_PATH.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(remaining), 3, "All records should be retained (all recent and all valid or malformed)")

    def test_cross_process_dedup_finds_last_alert_by_type(self) -> None:
        """Cross-process dedup should look at last record of the same alert type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            alerts.ALERTS_PATH = Path(tmpdir) / "alerts.jsonl"
            alerts._last_persisted_alert.clear()

            alerts.ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)

            ts = datetime.now(timezone.utc).isoformat()

            drift_alert = {
                "timestamp": ts,
                "type": "drift_stub",
                "metric": "drift.distance",
                "value": 0.15,
                "threshold": 0.1,
            }
            latency_alert = {
                "timestamp": ts,
                "type": "service_latency",
                "metric": "latency.p95_ms",
                "value": 350,
                "threshold": 300,
            }

            with alerts.ALERTS_PATH.open("w", encoding="utf-8") as f:
                f.write(json.dumps(drift_alert) + "\n")
                f.write(json.dumps(latency_alert) + "\n")

            ts_prev = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            old_drift = {
                "timestamp": ts_prev,
                "type": "drift_stub",
                "metric": "drift.distance",
                "value": 0.18,
                "threshold": 0.1,
            }

            with alerts.ALERTS_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(old_drift) + "\n")

            last_record, last_time = alerts._find_last_record_for_type("service_latency")
            self.assertIsNotNone(last_record)
            self.assertEqual(last_record["type"], "service_latency")
            self.assertEqual(last_record["value"], 350)


if __name__ == "__main__":
    unittest.main()
