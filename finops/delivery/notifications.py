"""
finops/delivery/notifications.py — Multi-Channel Alert & Notification Dispatcher
==================================================================================
Inspired by daily_stock_analysis:
Dispatches daily Top 20 overnight trade reports to:
- Telegram Bot API
- SMTP Email
- Discord / Slack / Generic Webhook
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import urllib.request
import urllib.parse

from finops.core.models import ScanReport
from finops.core.config import Settings

logger = logging.getLogger("finops.delivery.notifications")


class NotificationDispatcher:
    def __init__(self):
        self.settings = Settings.get()

    def dispatch_report(self, report: ScanReport, markdown_content: str) -> Dict[str, bool]:
        """
        Dispatches report to all configured channels (Telegram, Email, Webhook).
        Returns status dictionary of results.
        """
        results = {
            "telegram": False,
            "email": False,
            "webhook": False
        }

        # 1. Telegram Dispatch
        tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if tg_token and tg_chat_id:
            results["telegram"] = self.send_telegram(report, tg_token, tg_chat_id)
        else:
            logger.debug("Telegram credentials not configured; skipping Telegram notification.")

        # 2. Email Dispatch
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        recipient = os.environ.get("ALERT_EMAIL_RECIPIENT")
        if smtp_host and smtp_user and smtp_pass and recipient:
            results["email"] = self.send_email(report, markdown_content, smtp_host, smtp_user, smtp_pass, recipient)
        else:
            logger.debug("SMTP email credentials not configured; skipping Email notification.")

        # 3. Webhook Dispatch (Discord / Slack)
        webhook_url = os.environ.get("ALERT_WEBHOOK_URL")
        if webhook_url:
            results["webhook"] = self.send_webhook(report, webhook_url)
        else:
            logger.debug("ALERT_WEBHOOK_URL not configured; skipping Webhook notification.")

        return results

    def send_telegram(self, report: ScanReport, token: str, chat_id: str) -> bool:
        """
        Sends formatted executive summary to Telegram chat/channel.
        """
        try:
            horizon_tag = report.horizon.upper()
            top_3 = report.top_20[:3]
            lines = [
                f"🦅 *finOps Opportunities Report [{horizon_tag}]*",
                f"📅 *Session:* {report.target_trade_session}",
                f"🔬 *Universe:* {report.scanned_universe_size} stocks scanned\n",
                "*🏆 Top Ranked Opportunities:*"
            ]
            for opp in top_3:
                p = opp.trade_plan
                lines.append(
                    f"• *#{opp.rank} {opp.ticker}* ({opp.market.upper()}) — *Score: {opp.scores.composite_score:.1f}*\n"
                    f"  Action: `{p.action}` | Limit: `{opp.currency} {p.entry_zone_low:.2f} - {p.entry_zone_high:.2f}`\n"
                    f"  Stop: `{opp.currency} {p.stop_loss:.2f}` | Target: `{opp.currency} {p.target_1:.2f}` ({p.risk_reward_ratio:.1f}x)\n"
                )
            lines.append("🌐 View full interactive dashboard at https://yepzhi.com/finOps")

            msg = "\n".join(lines)
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = json.dumps({
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown"
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def send_email(self, report: ScanReport, markdown_content: str, host: str, user: str, password: str, recipient: str) -> bool:
        """
        Sends complete report via SMTP email.
        """
        try:
            port = int(os.environ.get("SMTP_PORT", 587))
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🦅 finOps Daily Stock Opportunities [{report.horizon.upper()}] — {report.target_trade_session}"
            msg["From"] = user
            msg["To"] = recipient

            text_part = MIMEText(markdown_content, "plain", "utf-8")
            msg.attach(text_part)

            with smtplib.SMTP(host, port, timeout=15) as server:
                server.starttls()
                server.login(user, password)
                server.sendmail(user, [recipient], msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Failed to send SMTP email: {e}")
            return False

    def send_webhook(self, report: ScanReport, webhook_url: str) -> bool:
        """
        Sends webhook payload compatible with Discord/Slack.
        """
        try:
            horizon_tag = report.horizon.upper()
            payload = {
                "content": f"🦅 **finOps Stock Opportunities [{horizon_tag}]** — Ready for {report.target_trade_session}\nTop Pick: **{report.top_20[0].ticker}** (Score {report.top_20[0].scores.composite_score:.1f})\nDashboard: https://yepzhi.com/finOps"
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json", "User-Agent": "finOps-Bot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status in (200, 204)
        except Exception as e:
            logger.error(f"Failed to send Webhook notification: {e}")
            return False
