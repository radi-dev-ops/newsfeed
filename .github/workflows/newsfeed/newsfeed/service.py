diff --git a/newsfeed/service.py b/newsfeed/service.py
new file mode 100644
index 0000000000000000000000000000000000000000..61ad47778602b756b0a56f392402022c19edad9f
--- /dev/null
+++ b/newsfeed/service.py
@@ -0,0 +1,58 @@
+"""Core delivery workflow."""
+from __future__ import annotations
+
+import logging
+from datetime import timedelta
+from email.message import EmailMessage
+from typing import Callable
+
+from .config import AppConfig, DeliveryContext
+from .digest import build_email
+from .mailer import send_message
+from .rss import Article, collect_articles
+
+logger = logging.getLogger(__name__)
+
+
+def resolve_delivery(config: AppConfig, name: str) -> DeliveryContext:
+    for delivery in config.deliveries:
+        if delivery.name == name:
+            return DeliveryContext(config=config, delivery=delivery)
+    raise KeyError(f"Delivery named '{name}' not found")
+
+
+def gather_articles(context: DeliveryContext) -> list[Article]:
+    lookback = timedelta(hours=context.window_hours)
+    articles = collect_articles(context.feeds(), lookback=lookback)
+    logger.info(
+        "Found %d articles for delivery %s within %d hours",
+        len(articles),
+        context.delivery.name,
+        context.window_hours,
+    )
+    return articles
+
+
+def prepare_email(context: DeliveryContext, articles: list[Article]) -> EmailMessage:
+    return build_email(context, articles)
+
+
+def deliver(
+    context: DeliveryContext,
+    *,
+    send_func: Callable[[AppConfig, "EmailMessage"], None] | None = None,
+) -> tuple[int, EmailMessage]:
+    articles = gather_articles(context)
+    message = prepare_email(context, articles)
+    sender = send_func or send_message
+    sender(context.config, message)
+    logger.info(
+        "Delivered %d articles for %s to %s",
+        len(articles),
+        context.delivery.name,
+        ", ".join(context.delivery.recipients),
+    )
+    return len(articles), message
+
+
+__all__ = ["deliver", "gather_articles", "prepare_email", "resolve_delivery"]
