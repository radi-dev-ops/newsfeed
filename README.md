# Newsfeed Automation

Newsfeed is a configurable RSS aggregation tool that gathers the latest stories from your chosen publications and emails a digest on demand or on a schedule.

## Features

- Load multiple RSS feeds and filter to a configurable look-back window.
- Group headlines by publication and deduplicate repeated links.
- Send rich HTML and plain-text email digests over SMTP.
- Configure multiple delivery schedules with different recipient lists.
- Run interactively for previews or as a long-running scheduler service.

## Quick start

1. **Install dependencies**

   ```bash
   pip install -e .
   ```

2. **Copy the example configuration**

   ```bash
   cp config.example.yml config.yml
   ```

3. **Edit `config.yml`** with your feeds, SMTP settings, recipients, and schedules. Secret values can reference environment variables using the `${VAR_NAME}` syntax.

4. **Preview a digest** without sending email:

   ```bash
   newsfeed preview --config config.yml --delivery "Editorial AM"
   ```

5. **Send immediately**:

   ```bash
   newsfeed send --config config.yml --delivery "Editorial AM"
   ```

6. **Run the scheduler** (blocks in the foreground and triggers deliveries according to their schedules):

   ```bash
   newsfeed run --config config.yml
   ```

## Configuration file

The configuration file is written in YAML. Below is an abbreviated example — see [`config.example.yml`](config.example.yml) for a fully annotated template.

```yaml
feeds:
  - id: happy-mag
    name: Happy Mag
    url: https://happymag.tv/feed/
  - id: abc-music
    name: ABC Music News
    url: https://www.abc.net.au/listen/radio/triplej/musicnews/rss.xml

email:
  sender: "News Bot <bot@example.com>"
  smtp:
    host: smtp.gmail.com
    port: 587
    username: ${SMTP_USERNAME}
    password: ${SMTP_PASSWORD}
    use_tls: true

lookback_hours: 12

deliveries:
  - name: Editorial AM
    feeds: [happy-mag, abc-music]
    recipients:
      - editorial@example.com
      - marketing@example.com
    window_hours: 12
    subject_template: "Editorial digest: {{ window_hours }}h recap"
    schedule:
      cron: "0 8 * * 1-5"
      timezone: "Australia/Sydney"
```

## Scheduling

Deliveries that include a `schedule` block are registered with APScheduler when you run `newsfeed run`. Schedules support either a five-field cron expression (`minute hour day-of-month month day-of-week`) or a simple interval.

```yaml
schedule:
  cron: "0 8,16 * * 1-5"   # twice per weekday
  timezone: "Australia/Sydney"
```

or

```yaml
schedule:
  every_minutes: 720        # every 12 hours
  timezone: "UTC"
```

## Email templates

The default subject is `"News digest: {delivery_name}"`. You can override this per delivery using Jinja2 templates that have access to:

- `delivery_name`
- `window_hours`
- `generated_at` (timezone-aware `datetime`)
- `article_count`

The HTML and plain-text bodies are generated automatically with grouping by feed. See `newsfeed/templates` for the base templates.

## Running in the cloud

The CLI is suitable for running on a small VM, a serverless worker, or a container orchestrated service. Example options:

- **GitHub Actions**: run on a schedule using `cron` and set secrets for SMTP credentials.
- **Fly.io / Render / Railway**: deploy the package with a process command `newsfeed run --config /app/config.yml`.
- **AWS Lambda**: invoke `newsfeed send` on a schedule via EventBridge (wrap the CLI in a handler).

## Development

Run the automated tests with:

```bash
pytest
```

Contributions are welcome via pull requests.
