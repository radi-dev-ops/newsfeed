diff --git a/newsfeed/scheduler.py b/newsfeed/scheduler.py
new file mode 100644
index 0000000000000000000000000000000000000000..cfa29c76e40d2597bc819ef8b61bf256373d26d1
--- /dev/null
+++ b/newsfeed/scheduler.py
@@ -0,0 +1,53 @@
+"""Scheduler integration."""
+from __future__ import annotations
+
+import logging
+
+from apscheduler.schedulers.blocking import BlockingScheduler
+from apscheduler.triggers.cron import CronTrigger
+from apscheduler.triggers.interval import IntervalTrigger
+from zoneinfo import ZoneInfo
+
+from .config import AppConfig, DeliveryContext
+from .service import deliver
+
+logger = logging.getLogger(__name__)
+
+
+def _make_job(context: DeliveryContext):
+    def _job() -> None:
+        logger.info("Running scheduled delivery %s", context.delivery.name)
+        deliver(context)
+
+    return _job
+
+
+def run_scheduler(config: AppConfig) -> None:
+    scheduler = BlockingScheduler()
+    for delivery in config.deliveries:
+        if not delivery.schedule:
+            continue
+        tz = ZoneInfo(delivery.schedule.timezone)
+        if delivery.schedule.cron:
+            trigger = CronTrigger.from_crontab(delivery.schedule.cron, timezone=tz)
+        else:
+            trigger = IntervalTrigger(minutes=delivery.schedule.every_minutes, timezone=tz)
+        context = DeliveryContext(config=config, delivery=delivery)
+        scheduler.add_job(
+            _make_job(context),
+            trigger=trigger,
+            id=f"delivery-{delivery.name}",
+            name=f"Delivery: {delivery.name}",
+            replace_existing=True,
+        )
+        logger.info("Scheduled %s with trigger %s", delivery.name, trigger)
+
+    if not scheduler.get_jobs():
+        logger.warning("No scheduled deliveries configured; scheduler will exit")
+        return
+
+    logger.info("Starting scheduler")
+    scheduler.start()
+
+
+__all__ = ["run_scheduler"]
