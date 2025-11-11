"""Configuration models and loader for the newsfeed application."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import os
import re

import yaml
from pydantic import BaseModel, EmailStr, Field, HttpUrl, PositiveInt, model_validator

ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _substitute_env(value: str) -> str:
    """Substitute `${VAR}` expressions using environment variables."""

    def replacer(match: re.Match[str]) -> str:
        var = match.group(1)
        if var not in os.environ:
            raise ValueError(f"Environment variable '{var}' referenced in config but not set")
        return os.environ[var]

    return ENV_VAR_PATTERN.sub(replacer, value)


class FeedConfig(BaseModel):
    """Configuration for a single RSS feed."""

    id: str
    name: str
    url: HttpUrl
    tags: List[str] = Field(default_factory=list)


class SMTPConfig(BaseModel):
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False

    @model_validator(mode="after")
    def _check_tls(self) -> "SMTPConfig":
        if self.use_ssl and self.use_tls:
            raise ValueError("Specify only one of use_ssl or use_tls")
        return self


class EmailConfig(BaseModel):
    sender: str
    smtp: SMTPConfig


class DeliverySchedule(BaseModel):
    cron: Optional[str] = None
    every_minutes: Optional[PositiveInt] = Field(default=None, description="Interval in minutes")
    timezone: str = "UTC"

    @model_validator(mode="after")
    def _check_schedule(self) -> "DeliverySchedule":
        if bool(self.cron) == bool(self.every_minutes):
            raise ValueError("Provide exactly one of cron or every_minutes for a schedule")
        return self


class DeliveryConfig(BaseModel):
    name: str
    feeds: Optional[List[str]] = None
    recipients: List[EmailStr]
    window_hours: Optional[PositiveInt] = None
    subject_template: Optional[str] = None
    schedule: Optional[DeliverySchedule] = None


class AppConfig(BaseModel):
    feeds: List[FeedConfig]
    email: EmailConfig
    deliveries: List[DeliveryConfig]
    lookback_hours: PositiveInt = 12

    @model_validator(mode="after")
    def _check_unique_feeds(self) -> "AppConfig":
        ids = [feed.id for feed in self.feeds]
        if len(ids) != len(set(ids)):
            raise ValueError("Feed ids must be unique")
        return self

    def feed_by_id(self, feed_id: str) -> FeedConfig:
        for feed in self.feeds:
            if feed.id == feed_id:
                return feed
        raise KeyError(f"Unknown feed id '{feed_id}' in configuration")

    def feeds_for_delivery(self, delivery: DeliveryConfig) -> List[FeedConfig]:
        if delivery.feeds:
            return [self.feed_by_id(fid) for fid in delivery.feeds]
        return list(self.feeds)


def load_config(path: str | os.PathLike[str]) -> AppConfig:
    """Load configuration from a YAML file."""

    data_path = Path(path)
    if not data_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {data_path}")

    raw = data_path.read_text()
    substituted = _substitute_env(raw)
    payload = yaml.safe_load(substituted) or {}
    return AppConfig.model_validate(payload)


@dataclass(slots=True)
class DeliveryContext:
    """Resolved delivery configuration."""

    config: AppConfig
    delivery: DeliveryConfig

    @property
    def window_hours(self) -> int:
        return self.delivery.window_hours or self.config.lookback_hours

    def feeds(self) -> Iterable[FeedConfig]:
        return self.config.feeds_for_delivery(self.delivery)


__all__ = [
    "AppConfig",
    "DeliveryConfig",
    "DeliveryContext",
    "FeedConfig",
    "load_config",
]
