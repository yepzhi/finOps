"""
finops/delivery/storage.py — Daily Scan Persistence & Report Archiving
======================================================================
Stores structured ScanReport JSON artifacts and Markdown summaries.
Keeps `data/reports/latest.json` synchronized for web dashboard live feeds.
"""

import json
import logging
from pathlib import Path
from finops.core.models import ScanReport
from finops.core.config import get_project_root

logger = logging.getLogger("finops.delivery.storage")


class ReportStorage:
    def __init__(self):
        self.root = get_project_root()
        self.reports_dir = self.root / "data" / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_scan_report(self, report: ScanReport, markdown_content: str) -> Path:
        """
        Saves both JSON and Markdown artifacts for the daily run.
        """
        date_str = report.scan_date
        horizon = report.horizon or "daily"
        
        json_file = self.reports_dir / f"scan_{date_str}_{horizon}.json"
        md_file = self.reports_dir / f"scan_{date_str}_{horizon}.md"
        latest_horizon_file = self.reports_dir / f"latest_{horizon}.json"
        latest_file = self.reports_dir / "latest.json"

        # Serialize Pydantic model
        report_dict = report.model_dump(mode="json")

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        with open(latest_horizon_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        # Update latest.json
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Daily [{horizon.upper()}] scan artifacts saved to {json_file} and {md_file}")
        return json_file

    def load_latest_report(self, horizon: str = None) -> ScanReport:
        if horizon:
            target = self.reports_dir / f"latest_{horizon}.json"
            if target.exists():
                with open(target, "r", encoding="utf-8") as f:
                    return ScanReport(**json.load(f))
        latest_file = self.reports_dir / "latest.json"
        if not latest_file.exists():
            raise FileNotFoundError(f"No latest report found at {latest_file}")
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ScanReport(**data)
