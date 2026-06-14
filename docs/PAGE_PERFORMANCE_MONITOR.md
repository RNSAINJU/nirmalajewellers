# Daily page performance monitor

The `check_page_performance` management command checks live page reload time and
sends Slack alerts for HTTP errors, unexpected redirects, request failures, or
pages slower than `PAGE_MONITOR_THRESHOLD_MS`.

## Environment

Configure Slack and monitor settings in `.env`:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
SLACK_CHANNEL=#new-channel
PAGE_MONITOR_BASE_URL=https://nirmalajewellers.net
PAGE_MONITOR_THRESHOLD_MS=3000
PAGE_MONITOR_TIMEOUT_SECONDS=20

# Optional: check authenticated pages too.
MONITOR_USERNAME=monitor-user
MONITOR_PASSWORD=monitor-password

# Optional: override or extend the discovered page list.
PAGE_MONITOR_PATHS=
PAGE_MONITOR_EXTRA_PATHS=/products/1/,/shop/category/2/
PAGE_MONITOR_SKIP_PATHS=
```

Leave `PAGE_MONITOR_PATHS` empty to auto-discover static page URLs from Django.
Use `PAGE_MONITOR_EXTRA_PATHS` for dynamic pages that need real IDs, such as
product detail or category pages.

## Commands

Preview the pages that will be checked:

```bash
python manage.py check_page_performance --list-pages
```

Run the check manually without sending Slack:

```bash
python manage.py check_page_performance --dry-run
```

## Daily cron

Production cron example:

```bash
0 6 * * * cd /home/rnsainju/nirmalajewellers && /home/rnsainju/nirmalajewellers/venv/bin/python manage.py check_page_performance >> /home/rnsainju/nirmalajewellers/page_monitor.log 2>&1
```
