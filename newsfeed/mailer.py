"""SMTP email sending utilities."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

from .config import AppConfig

logger = logging.getLogger(__name__)


def send_message(config: AppConfig, message: EmailMessage) -> None:
    smtp_config = config.email.smtp
    recipients: Iterable[str] = message.get_all("To", [])

    if smtp_config.use_ssl:
        server: smtplib.SMTP = smtplib.SMTP_SSL(smtp_config.host, smtp_config.port, timeout=30)
    else:
        server = smtplib.SMTP(smtp_config.host, smtp_config.port, timeout=30)

    with server:
        if smtp_config.use_tls and not smtp_config.use_ssl:
            server.starttls()
        if smtp_config.username and smtp_config.password:
            server.login(smtp_config.username, smtp_config.password)
        logger.info("Sending email to %s", recipients)
        server.send_message(message)


__all__ = ["send_message"]
