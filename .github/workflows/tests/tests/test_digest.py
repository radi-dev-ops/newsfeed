diff --git a/tests/test_digest.py b/tests/test_digest.py
new file mode 100644
index 0000000000000000000000000000000000000000..a793bd6b0c8497bd8688349a0994317d93829f5c
--- /dev/null
+++ b/tests/test_digest.py
@@ -0,0 +1,59 @@
+from __future__ import annotations
+
+from datetime import datetime, timezone
+
+from newsfeed.config import (
+    AppConfig,
+    DeliveryConfig,
+    DeliveryContext,
+    DeliverySchedule,
+    EmailConfig,
+    FeedConfig,
+    SMTPConfig,
+)
+from newsfeed.digest import build_email, render_digest
+from newsfeed.rss import Article
+
+
+def make_context() -> DeliveryContext:
+    config = AppConfig(
+        feeds=[FeedConfig(id="sample", name="Sample Feed", url="https://example.com/rss")],
+        email=EmailConfig(sender="Bot <bot@example.com>", smtp=SMTPConfig(host="smtp.example.com")),
+        deliveries=[
+            DeliveryConfig(
+                name="Daily",
+                recipients=["editor@example.com"],
+                schedule=DeliverySchedule(every_minutes=60, timezone="UTC"),
+            )
+        ],
+    )
+    return DeliveryContext(config=config, delivery=config.deliveries[0])
+
+
+def test_render_digest_contains_feed_names():
+    context = make_context()
+    articles = [
+        Article(
+            feed_id="sample",
+            feed_name="Sample Feed",
+            title="Test Article",
+            link="https://example.com/1",
+            summary="Summary",
+            published=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
+        )
+    ]
+
+    subject, html, text = render_digest(context, articles)
+    assert "News digest" in subject
+    assert "Sample Feed" in html
+    assert "https://example.com/1" in text
+
+
+def test_build_email_includes_plain_and_html_bodies():
+    context = make_context()
+    articles = []
+
+    message = build_email(context, articles)
+    assert message["Subject"]
+    assert message.get_body(preferencelist=("plain",)) is not None
+    assert message.get_body(preferencelist=("html",)) is not None
