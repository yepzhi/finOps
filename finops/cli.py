"""
finops/cli.py — Command-Line Interface for finOps Quant Engine
==============================================================
Provides commands for running daily scans, testing exchange schedules,
and launching the interactive cyber-glass web dashboard.
"""

import sys
import logging
import click
from datetime import datetime
from finops.core.engine import ScanPipeline
from finops.core.calendar import MarketCalendarService
from finops.core.config import Settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("finops.cli")


@click.group()
def cli():
    """🦅 finOps — Daily Stock Opportunities Platform (Top 20)."""
    pass


@cli.command()
@click.option("--market", default="all", help="Target market: 'us', 'cn', 'mx', or 'all'")
@click.option("--limit", default=None, type=int, help="Optional limit per market for testing (e.g. 5)")
@click.option("--force", is_flag=True, help="Force scan execution regardless of schedule")
def scan(market: str, limit: int, force: bool):
    """Executes the daily market scanning, factor scoring, and overnight trade planning."""
    click.echo("=================================================================")
    click.echo("🚀 finOps — Launching Multi-Market Daily Scan & Ranking Pipeline")
    click.echo("=================================================================")

    target_markets = None
    if market != "all":
        target_markets = [m.strip().lower() for m in market.split(",")]

    pipeline = ScanPipeline()
    report = pipeline.run_daily_scan(
        target_markets=target_markets,
        candidate_limit_per_market=limit,
        force_run=force
    )

    click.echo("\n🏆 TOP OPPORTUNITIES SUMMARY:")
    click.echo(f"Run ID: {report.run_id} | Session: {report.target_trade_session}")
    click.echo("-" * 75)
    click.echo(f"{'Rank':<5} {'Ticker':<8} {'Market':<6} {'Score':<7} {'Action':<6} {'Price':<12} {'R:R':<6} {'Stop Loss':<10} {'Target 1'}")
    click.echo("-" * 75)
    for opp in report.top_20[:10]:
        p = opp.trade_plan
        click.echo(f"#{opp.rank:<4} {opp.ticker:<8} {opp.market.upper():<6} {opp.scores.composite_score:<7.1f} {p.action:<6} {opp.currency} {opp.current_price:<7.2f} {p.risk_reward_ratio:<6.1f}x {p.stop_loss:<10.2f} {p.target_1:.2f}")

    if len(report.top_20) > 10:
        click.echo(f"... and {len(report.top_20) - 10} more top opportunities (view full report in data/reports/)")

    click.echo("\n✅ Scan complete! Artifacts archived at data/reports/scan_" + report.scan_date + ".md")


@cli.command()
@click.option("--offset", default=5.0, type=float, help="Hours after exchange close (default: 5.0)")
def schedule(offset: float):
    """Calculates and verifies the exchange calendar run trigger time."""
    calendar = MarketCalendarService()
    today = datetime.now(calendar.tz).date()

    is_open = calendar.is_trading_day(today)
    click.echo(f"📅 Today: {today} | Exchange: {calendar.calendar_code}")
    click.echo(f"📈 Is Open Trading Day: {'YES' if is_open else 'NO (Weekend / Holiday)'}")

    if is_open:
        open_dt, close_dt = calendar.get_session_times(today)
        trigger_dt = calendar.calculate_run_trigger_time(today, offset_hours=offset)
        can_run, reason = calendar.should_execute_now(offset_hours=offset)

        click.echo(f"🕒 Regular Session Open:  {open_dt.strftime('%H:%M:%S %Z')}")
        click.echo(f"🕒 Regular Session Close: {close_dt.strftime('%H:%M:%S %Z')}")
        click.echo(f"⏰ Scan Trigger Time (+{offset}h): {trigger_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        click.echo(f"⚡ Schedule Status: {reason}")
    else:
        next_session = calendar.get_next_trading_session()
        click.echo(f"⏭️ Next Scheduled Session: {next_session}")


@cli.command()
@click.option("--port", default=8080, type=int, help="Port to serve the web dashboard on (default: 8080)")
def serve(port: int):
    """Starts a local HTTP server hosting the cyber-glass web dashboard."""
    import http.server
    import socketserver
    from finops.core.config import get_project_root

    root = get_project_root()
    web_dir = root / "web"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(web_dir), **kwargs)

    click.echo(f"🌐 Starting finOps Web Dashboard at http://localhost:{port} (Serving {web_dir})")
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nShutting down server.")


if __name__ == "__main__":
    cli()
