"""Digest rendering utilities."""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Dict, Iterable, List

from jinja2 import Environment, PackageLoader, select_autoescape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import logging

from .config import DeliveryContext
from .rss import Article

logger = logging.getLogger(__name__)

_env = Environment(
    loader=PackageLoader("newsfeed", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

_HTML_TEMPLATE = _env.get_template("digest.html.j2")
_TEXT_TEMPLATE = _env.get_template("digest.txt.j2")


def _subject_for(context: DeliveryContext, generated_at: datetime, article_count: int) -> str:
    delivery = context.delivery
    template = delivery.subject_template or "News digest: {{ delivery_name }}"
    compiled = _env.from_string(template)
    tz = _resolve_timezone(context)
    return compiled.render(
        delivery_name=delivery.name,
        window_hours=context.window_hours,
        generated_at=generated_at,
        article_count=article_count,
        tz=tz,
    )


def _resolve_timezone(context: DeliveryContext) -> ZoneInfo:
    tz_name = context.delivery.schedule.timezone if context.delivery.schedule else "UTC"
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        logger.warning("Unknown timezone %s; defaulting to UTC", tz_name)
        return ZoneInfo("UTC")


def _group_articles(articles: Iterable[Article]) -> Dict[str, List[Article]]:
    grouped: "OrderedDict[str, List[Article]]" = OrderedDict()
    for article in articles:
        grouped.setdefault(article.feed_name, []).append(article)
    return grouped


def render_digest(context: DeliveryContext, articles: List[Article]) -> tuple[str, str, str]:
    """Render the subject, HTML, and plain text content for a delivery."""

    generated_at = datetime.now(timezone.utc)
    tz = _resolve_timezone(context)
    subject = _subject_for(context, generated_at, len(articles))
    grouped_articles = _group_articles(articles)
    render_ctx = {
        "subject": subject,
        "generated_at": generated_at,
        "window_hours": context.window_hours,
        "articles": articles,
        "grouped_articles": grouped_articles,
        "tz": tz,
    }
    html_body = _HTML_TEMPLATE.render(**render_ctx)
    text_body = _TEXT_TEMPLATE.render(**render_ctx)
    return subject, html_body, text_body


def build_email(context: DeliveryContext, articles: List[Article]) -> EmailMessage:
    subject, html_body, text_body = render_digest(context, articles)
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = context.config.email.sender
    msg["To"] = ", ".join(context.delivery.recipients)
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


__all__ = ["render_digest", "build_email"]
