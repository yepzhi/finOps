"""
finops/core/calendar.py — Exchange Trading Calendar & Run-Time Scheduler
========================================================================
Determines trading sessions, market close timestamps, early closes,
and calculates the exact `close + 5 hours` trigger time using `exchange_calendars`.
"""

import pytz
from datetime import datetime, date, timedelta
from typing import Tuple, Optional
import exchange_calendars as xcals


class MarketCalendarService:
    def __init__(self, calendar_code: str = "XNYS", timezone_str: str = "America/New_York"):
        self.calendar_code = calendar_code
        self.tz = pytz.timezone(timezone_str)
        try:
            self.calendar = xcals.get_calendar(calendar_code)
        except Exception:
            # Fallback to standard XNYS
            self.calendar = xcals.get_calendar("XNYS")

    def is_trading_day(self, check_date: Optional[date] = None) -> bool:
        """Check if a given date is an official open trading day."""
        if check_date is None:
            check_date = datetime.now(self.tz).date()
        date_str = check_date.strftime("%Y-%m-%d")
        return self.calendar.is_session(date_str)

    def get_session_times(self, session_date: Optional[date] = None) -> Tuple[datetime, datetime]:
        """
        Returns (market_open_dt, market_close_dt) localized in market timezone.
        Accurately handles early closures (e.g. 13:00 ET before holidays).
        """
        if session_date is None:
            session_date = datetime.now(self.tz).date()

        date_str = session_date.strftime("%Y-%m-%d")
        if not self.calendar.is_session(date_str):
            raise ValueError(f"Date {date_str} is not a valid trading session for {self.calendar_code}")

        open_utc = self.calendar.session_open(date_str)
        close_utc = self.calendar.session_close(date_str)

        open_local = open_utc.astimezone(self.tz)
        close_local = close_utc.astimezone(self.tz)

        return open_local, close_local

    def calculate_run_trigger_time(self, session_date: Optional[date] = None, offset_hours: float = 5.0) -> datetime:
        """
        Calculates `close + offset_hours` (e.g. 16:00 ET + 5h = 21:00 ET).
        For an early close at 13:00 ET, returns 18:00 ET.
        """
        _, close_local = self.get_session_times(session_date)
        trigger_time = close_local + timedelta(hours=offset_hours)
        return trigger_time

    def get_next_trading_session(self, from_date: Optional[date] = None) -> date:
        """Returns the next scheduled trading day (skipping weekends and holidays)."""
        if from_date is None:
            from_date = datetime.now(self.tz).date()
        date_str = from_date.strftime("%Y-%m-%d")
        next_session_ts = self.calendar.next_session(date_str)
        return next_session_ts.date()

    def should_execute_now(self, offset_hours: float = 5.0) -> Tuple[bool, str]:
        """
        Evaluates whether current time has reached or passed `today_close + offset_hours`.
        Returns (can_execute, status_reason).
        """
        now = datetime.now(self.tz)
        today = now.date()

        if not self.is_trading_day(today):
            return False, f"Today ({today}) is a non-trading day (weekend/holiday) on {self.calendar_code}."

        trigger_time = self.calculate_run_trigger_time(today, offset_hours)
        if now < trigger_time:
            diff = trigger_time - now
            minutes_left = int(diff.total_seconds() / 60)
            return False, f"Market close + {offset_hours}h has not arrived yet. Scheduled trigger at {trigger_time.strftime('%Y-%m-%d %H:%M:%S %Z')} (~{minutes_left} min remaining)."

        return True, f"Eligible for execution: current time {now.strftime('%H:%M %Z')} >= trigger time {trigger_time.strftime('%H:%M %Z')}."
