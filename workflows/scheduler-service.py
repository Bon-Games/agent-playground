#!/usr/bin/env python3
"""
Scheduler service — container entrypoint.
Fires the daily triage workflow at the configured time via the Anthropic API.
Configure via env vars: TRIAGE_HOUR (0-23), TRIAGE_DAYS (comma-separated: mon,tue,wed,thu,fri)
"""
import logging
import os
import time

import schedule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run_triage_job():
    log.info("Starting scheduled triage...")
    try:
        import triage_runner
        triage_runner.run_triage()
        log.info("Triage run complete.")
    except Exception as e:
        log.error("Triage run failed: %s", e, exc_info=True)
        try:
            from notify import send_notification
            send_notification(
                summary=f"Scheduled triage FAILED\n\n```\n{e}\n```",
                channel="telegram",
            )
        except Exception as notify_err:
            log.error("Could not send failure notification: %s", notify_err)


def main():
    hour = int(os.environ.get("TRIAGE_HOUR", "8"))
    days_raw = os.environ.get("TRIAGE_DAYS", "mon,tue,wed,thu,fri")
    days = [d.strip().lower() for d in days_raw.split(",") if d.strip()]

    time_str = f"{hour:02d}:00"
    registered = []
    for day in days:
        day_scheduler = getattr(schedule.every(), day, None)
        if day_scheduler is None:
            log.warning("Unknown day '%s' — skipping.", day)
            continue
        day_scheduler.at(time_str).do(run_triage_job)
        registered.append(day)

    if not registered:
        log.error("No valid days configured. Set TRIAGE_DAYS to e.g. mon,tue,wed,thu,fri")
        return

    log.info("Triage scheduled: %s at %s UTC", ", ".join(registered), time_str)
    log.info("Scheduler running. Sleeping 30s between checks...")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
