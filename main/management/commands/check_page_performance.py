from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

import requests
from django.core.management.base import BaseCommand, CommandError
from django.urls import URLPattern, URLResolver, get_resolver

from main.services.slack import send_slack_message


DEFAULT_BASE_URL = "https://nirmalajewellers.net"
DEFAULT_THRESHOLD_MS = 3000
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_LOGIN_PATH = "/accounts/login/"

PUBLIC_PATHS = {
    "/",
    "/accounts/login/",
    "/accounts/password_reset/",
    "/accounts/password_reset/done/",
}
PUBLIC_PREFIXES = (
    "/api/products/",
    "/api/ornament-chat/",
    "/ornament/api/chat/",
    "/shop",
    "/products/",
)
NON_PAGE_MARKERS = (
    "/api/",
    "/ajax/",
    "barcode-scanner/detect",
    "/delete",
    "/destroy",
    "/download",
    "/export",
    "/fetch",
    "/import",
    "/logout",
    "/mark-",
    "/print",
    "/process",
    "/toggle",
    "/track-",
    "/undo-",
)


@dataclass
class PageCheckResult:
    path: str
    url: str
    status_code: Optional[int]
    duration_ms: Optional[int]
    problem: Optional[str] = None


class Command(BaseCommand):
    help = (
        "Check live page reload times and send Slack alerts when pages error, "
        "redirect unexpectedly, or exceed the configured threshold."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=os.getenv("PAGE_MONITOR_BASE_URL", DEFAULT_BASE_URL),
            help="Production base URL to check.",
        )
        parser.add_argument(
            "--threshold-ms",
            type=int,
            default=int(os.getenv("PAGE_MONITOR_THRESHOLD_MS", DEFAULT_THRESHOLD_MS)),
            help="Alert when a page takes longer than this many milliseconds.",
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=float(os.getenv("PAGE_MONITOR_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
            help="HTTP timeout per page in seconds.",
        )
        parser.add_argument(
            "--paths",
            default=os.getenv("PAGE_MONITOR_PATHS", ""),
            help="Comma-separated paths or full URLs to check. Defaults to discovered static pages.",
        )
        parser.add_argument(
            "--extra-paths",
            default=os.getenv("PAGE_MONITOR_EXTRA_PATHS", ""),
            help="Additional comma-separated paths, useful for dynamic pages with real IDs.",
        )
        parser.add_argument(
            "--skip-paths",
            default=os.getenv("PAGE_MONITOR_SKIP_PATHS", ""),
            help="Comma-separated paths to exclude from checks.",
        )
        parser.add_argument(
            "--username",
            default=os.getenv("MONITOR_USERNAME", ""),
            help="Optional Django username for checking authenticated pages.",
        )
        parser.add_argument(
            "--password",
            default=os.getenv("MONITOR_PASSWORD", ""),
            help="Optional Django password for checking authenticated pages.",
        )
        parser.add_argument(
            "--login-path",
            default=os.getenv("PAGE_MONITOR_LOGIN_PATH", DEFAULT_LOGIN_PATH),
            help="Login path used when MONITOR_USERNAME and MONITOR_PASSWORD are configured.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run checks and print the Slack message without sending it.",
        )
        parser.add_argument(
            "--list-pages",
            action="store_true",
            help="Print the pages that would be checked and exit.",
        )
        parser.add_argument(
            "--notify-on-success",
            action="store_true",
            default=os.getenv("PAGE_MONITOR_NOTIFY_ON_SUCCESS", "False") == "True",
            help="Send a Slack summary even when all pages pass.",
        )
        parser.add_argument(
            "--no-cache-bust",
            action="store_true",
            help="Do not append a cache-busting query parameter to page checks.",
        )

    def handle(self, *args, **options):
        base_url = options["base_url"].strip().rstrip("/")
        threshold_ms = options["threshold_ms"]
        timeout = options["timeout"]
        username = options["username"].strip()
        password = options["password"].strip()
        has_auth = bool(username and password)

        paths = self._paths_to_check(
            configured_paths=options["paths"],
            extra_paths=options["extra_paths"],
            skip_paths=options["skip_paths"],
            include_authenticated=has_auth,
        )

        if options["list_pages"]:
            for path in paths:
                self.stdout.write(path)
            return

        if not paths:
            raise CommandError("No page paths were found to check.")

        session = requests.Session()
        session.headers.update(
            {
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "User-Agent": "NirmalaJewellersPageMonitor/1.0",
            }
        )

        auth_problem = None
        if has_auth:
            auth_problem = self._login(session, base_url, options["login_path"], username, password, timeout)
            if auth_problem:
                self.stdout.write(self.style.ERROR(auth_problem))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "MONITOR_USERNAME and MONITOR_PASSWORD are not configured; checking public pages only."
                )
            )

        results: List[PageCheckResult] = []
        if auth_problem:
            results.append(
                PageCheckResult(
                    path=options["login_path"],
                    url=self._absolute_url(base_url, options["login_path"]),
                    status_code=None,
                    duration_ms=None,
                    problem=auth_problem,
                )
            )

        cache_bust = not options["no_cache_bust"]
        for path in paths:
            result = self._check_page(session, base_url, path, threshold_ms, timeout, cache_bust)
            results.append(result)
            status = result.status_code if result.status_code is not None else "ERR"
            duration = f"{result.duration_ms}ms" if result.duration_ms is not None else "n/a"
            if result.problem:
                self.stdout.write(self.style.ERROR(f"{path} -> {status} in {duration}: {result.problem}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"{path} -> {status} in {duration}"))

        issues = [result for result in results if result.problem]
        if issues:
            message = self._build_issue_message(base_url, issues, len(results), threshold_ms)
            if options["dry_run"]:
                self.stdout.write(message)
            else:
                sent, error = send_slack_message(message)
                if not sent:
                    self.stdout.write(self.style.ERROR(f"Could not send Slack alert: {error}"))
            raise CommandError(f"Page performance check found {len(issues)} issue(s).")

        if options["notify_on_success"]:
            message = self._build_success_message(base_url, results, threshold_ms)
            if options["dry_run"]:
                self.stdout.write(message)
            else:
                sent, error = send_slack_message(message)
                if not sent:
                    raise CommandError(f"Could not send Slack success message: {error}")

        self.stdout.write(self.style.SUCCESS(f"All {len(results)} page checks passed."))

    def _paths_to_check(
        self,
        configured_paths: str,
        extra_paths: str,
        skip_paths: str,
        include_authenticated: bool,
    ) -> List[str]:
        if configured_paths.strip():
            paths = self._parse_csv(configured_paths)
        else:
            paths = self._discover_static_page_paths()
            paths.append(DEFAULT_LOGIN_PATH)

        paths.extend(self._parse_csv(extra_paths))
        paths = self._dedupe_paths(paths)

        skipped = set(self._normalize_path(path) for path in self._parse_csv(skip_paths))
        paths = [path for path in paths if self._normalize_path(path) not in skipped]

        if not include_authenticated:
            paths = [path for path in paths if self._is_public_path(path)]

        return paths

    def _discover_static_page_paths(self) -> List[str]:
        paths: List[str] = []
        self._collect_static_paths(get_resolver().url_patterns, "", paths)
        return self._dedupe_paths(paths)

    def _collect_static_paths(self, patterns: Sequence[object], prefix: str, paths: List[str]) -> None:
        for entry in patterns:
            route = self._route_for_pattern(getattr(entry, "pattern", None))
            combined = f"{prefix}{route}"

            if isinstance(entry, URLResolver):
                if self._is_non_page_path(combined):
                    continue
                self._collect_static_paths(entry.url_patterns, combined, paths)
                continue

            if not isinstance(entry, URLPattern):
                continue
            if not combined or "<" in combined or self._is_non_page_path(combined):
                if combined == "":
                    paths.append("/")
                continue
            paths.append(self._normalize_path(combined))

    def _route_for_pattern(self, pattern) -> str:
        route = getattr(pattern, "_route", None)
        if route is None:
            return ""
        return route

    def _is_non_page_path(self, path: str) -> bool:
        normalized = self._normalize_path(path).lower()
        return any(marker in normalized for marker in NON_PAGE_MARKERS)

    def _is_public_path(self, path: str) -> bool:
        normalized = self._normalize_path(path)
        return normalized in PUBLIC_PATHS or any(normalized.startswith(prefix) for prefix in PUBLIC_PREFIXES)

    def _check_page(
        self,
        session: requests.Session,
        base_url: str,
        path: str,
        threshold_ms: int,
        timeout: float,
        cache_bust: bool,
    ) -> PageCheckResult:
        url = self._absolute_url(base_url, path)
        if cache_bust:
            url = self._with_cache_buster(url)

        started = time.perf_counter()
        try:
            response = session.get(url, timeout=timeout, allow_redirects=False)
            duration_ms = int(round((time.perf_counter() - started) * 1000))
        except requests.RequestException as exc:
            duration_ms = int(round((time.perf_counter() - started) * 1000))
            return PageCheckResult(path=path, url=url, status_code=None, duration_ms=duration_ms, problem=str(exc))

        problem = self._response_problem(response, duration_ms, threshold_ms)
        return PageCheckResult(
            path=path,
            url=url,
            status_code=response.status_code,
            duration_ms=duration_ms,
            problem=problem,
        )

    def _response_problem(self, response: requests.Response, duration_ms: int, threshold_ms: int) -> Optional[str]:
        status_code = response.status_code
        if 300 <= status_code < 400:
            location = response.headers.get("Location", "")
            return f"unexpected redirect to {location or 'unknown location'}"
        if status_code != 200:
            return f"unexpected HTTP status {status_code}"
        if duration_ms > threshold_ms:
            return f"slow response above {threshold_ms}ms threshold"
        return None

    def _login(
        self,
        session: requests.Session,
        base_url: str,
        login_path: str,
        username: str,
        password: str,
        timeout: float,
    ) -> Optional[str]:
        login_url = self._absolute_url(base_url, login_path)
        try:
            login_page = session.get(login_url, timeout=timeout, allow_redirects=True)
            login_page.raise_for_status()
            csrf_token = session.cookies.get("csrftoken") or self._extract_csrf_token(login_page.text)
            data = {"username": username, "password": password}
            headers = {"Referer": login_url}
            if csrf_token:
                data["csrfmiddlewaretoken"] = csrf_token
                headers["X-CSRFToken"] = csrf_token

            response = session.post(login_url, data=data, headers=headers, timeout=timeout, allow_redirects=True)
            if response.status_code >= 400:
                return f"monitor login failed with HTTP {response.status_code}"

            final_path = urlparse(response.url).path
            if final_path.rstrip("/") == self._normalize_path(login_path).rstrip("/") and "sessionid" not in session.cookies:
                return "monitor login failed; still on login page"
        except requests.RequestException as exc:
            return f"monitor login failed: {exc}"
        return None

    def _extract_csrf_token(self, html: str) -> Optional[str]:
        match = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrfmiddlewaretoken["\']', html)
        if match:
            return match.group(1)
        return None

    def _absolute_url(self, base_url: str, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))

    def _with_cache_buster(self, url: str) -> str:
        parsed = urlparse(url)
        query = parse_qsl(parsed.query, keep_blank_values=True)
        query.append(("_page_monitor", str(int(time.time()))))
        return urlunparse(parsed._replace(query=urlencode(query)))

    def _build_issue_message(
        self,
        base_url: str,
        issues: Sequence[PageCheckResult],
        total_checks: int,
        threshold_ms: int,
    ) -> str:
        lines = [
            f"Page performance check found {len(issues)} issue(s) on {base_url}.",
            f"Checked {total_checks} page(s). Slow threshold: {threshold_ms}ms.",
        ]
        for result in issues[:20]:
            status = f"HTTP {result.status_code}" if result.status_code is not None else "request error"
            duration = f"{result.duration_ms}ms" if result.duration_ms is not None else "n/a"
            lines.append(f"- {result.path}: {result.problem} ({status}, {duration})")
        if len(issues) > 20:
            lines.append(f"- ...and {len(issues) - 20} more issue(s).")
        lines.append("Check server load, database queries, redirects, and third-party dependencies for slowdown.")
        return "\n".join(lines)

    def _build_success_message(self, base_url: str, results: Sequence[PageCheckResult], threshold_ms: int) -> str:
        slowest = max(results, key=lambda result: result.duration_ms or 0)
        return (
            f"Page performance check passed on {base_url}. "
            f"Checked {len(results)} page(s); slowest was {slowest.path} at {slowest.duration_ms}ms "
            f"(threshold {threshold_ms}ms)."
        )

    def _parse_csv(self, value: str) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def _dedupe_paths(self, paths: Iterable[str]) -> List[str]:
        seen = set()
        result = []
        for path in paths:
            normalized = self._normalize_path(path)
            if normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result

    def _normalize_path(self, path: str) -> str:
        path = path.strip()
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return path
