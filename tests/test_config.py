from __future__ import annotations

import textwrap

import pytest

from newsfeed.config import load_config


def test_load_config_with_env_substitution(tmp_path, monkeypatch):
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASS", "pass")
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        textwrap.dedent(
            """
            feeds:
              - id: sample
                name: Sample Feed
                url: https://example.com/rss
            email:
              sender: "Bot <bot@example.com>"
              smtp:
                host: smtp.example.com
                username: ${SMTP_USER}
                password: ${SMTP_PASS}
            deliveries:
              - name: Daily
                recipients: ["editor@example.com"]
            """
        ).strip()
    )

    config = load_config(config_path)
    assert config.email.smtp.username == "user"
    assert config.email.smtp.password == "pass"
    assert config.deliveries[0].name == "Daily"


def test_missing_env_variable_raises(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        textwrap.dedent(
            """
            feeds:
              - id: sample
                name: Sample Feed
                url: https://example.com/rss
            email:
              sender: "Bot <bot@example.com>"
              smtp:
                host: smtp.example.com
                username: ${MISSING}
            deliveries:
              - name: Daily
                recipients: ["editor@example.com"]
            """
        ).strip()
    )

    with pytest.raises(ValueError):
        load_config(config_path)
