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


def _sanitize_for_json(obj):
    import math
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(v) for v in obj]
    return obj


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

        # Serialize Pydantic model and strictly sanitize NaN/Inf for valid JSON
        report_dict = _sanitize_for_json(report.model_dump(mode="json"))

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

        # Automatically sync to yepzhiweb if repository exists
        self.sync_to_yepzhiweb()

        return json_file

    def sync_to_yepzhiweb(self):
        """
        Synchronizes the web dashboard and report artifacts to yepzhi.com/finOps
        """
        import shutil
        yepzhiweb_root = self.root.parent / "yepzhiweb"
        if not yepzhiweb_root.exists():
            return None

        dest_finops = yepzhiweb_root / "finOps"
        dest_finops.mkdir(parents=True, exist_ok=True)

        web_dir = self.root / "web"
        for item in ["index.html", "css", "js", "webfonts"]:
            src = web_dir / item
            dst = dest_finops / item
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            elif src.is_file():
                shutil.copy2(src, dst)

        dest_reports = dest_finops / "data" / "reports"
        dest_reports.mkdir(parents=True, exist_ok=True)
        for rf in self.reports_dir.glob("latest*.json"):
            shutil.copy2(rf, dest_reports / rf.name)

        logger.info(f"Successfully synced finOps web dashboard and reports to {dest_finops}")
        return dest_finops

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
