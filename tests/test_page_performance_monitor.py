from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from main.management.commands.check_page_performance import Command
from main.services.slack import send_slack_message


class FakeResponse:
    def __init__(self, status_code=200, text="", headers=None, url="https://example.com/"):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class PagePerformanceCommandTests(SimpleTestCase):
    def test_check_page_flags_slow_response(self):
        session = Mock()
        session.get.return_value = FakeResponse(status_code=200)
        command = Command()

        with patch("main.management.commands.check_page_performance.time.perf_counter", side_effect=[1.0, 4.5]):
            result = command._check_page(
                session=session,
                base_url="https://example.com",
                path="/shop/",
                threshold_ms=3000,
                timeout=5,
                cache_bust=False,
            )

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.duration_ms, 3500)
        self.assertEqual(result.problem, "slow response above 3000ms threshold")

    def test_check_page_flags_redirect(self):
        session = Mock()
        session.get.return_value = FakeResponse(status_code=302, headers={"Location": "/accounts/login/"})
        command = Command()

        with patch("main.management.commands.check_page_performance.time.perf_counter", side_effect=[1.0, 1.2]):
            result = command._check_page(
                session=session,
                base_url="https://example.com",
                path="/admin-dashboard/",
                threshold_ms=3000,
                timeout=5,
                cache_bust=False,
            )

        self.assertEqual(result.problem, "unexpected redirect to /accounts/login/")

    @override_settings(ROOT_URLCONF="mysite.urls")
    def test_public_only_without_credentials(self):
        command = Command()

        paths = command._paths_to_check(
            configured_paths="/,/shop/,/admin-dashboard/",
            extra_paths="",
            skip_paths="",
            include_authenticated=False,
        )

        self.assertEqual(paths, ["/", "/shop/"])

    @patch("main.management.commands.check_page_performance.requests.Session")
    @patch("main.management.commands.check_page_performance.send_slack_message")
    def test_command_sends_slack_when_issue_found(self, send_slack_mock, session_mock):
        session = Mock()
        session.headers = {}
        session.get.return_value = FakeResponse(status_code=500)
        session_mock.return_value = session
        send_slack_mock.return_value = (True, None)

        with self.assertRaises(CommandError):
            call_command(
                "check_page_performance",
                "--base-url=https://example.com",
                "--paths=/",
                "--threshold-ms=3000",
            )

        send_slack_mock.assert_called_once()
        self.assertIn("Page performance check found 1 issue", send_slack_mock.call_args.args[0])


class SlackServiceTests(SimpleTestCase):
    def test_send_slack_message_requires_webhook(self):
        with patch.dict("os.environ", {"SLACK_WEBHOOK_URL": ""}):
            success, error = send_slack_message("hello")

        self.assertFalse(success)
        self.assertEqual(error, "SLACK_WEBHOOK_URL is not configured")

    @patch("main.services.slack.requests.post")
    def test_send_slack_message_posts_payload(self, post_mock):
        post_mock.return_value = FakeResponse(status_code=200, text="ok")

        success, error = send_slack_message("hello", webhook_url="https://hooks.slack.test/abc")

        self.assertTrue(success)
        self.assertIsNone(error)
        post_mock.assert_called_once_with(
            "https://hooks.slack.test/abc",
            json={"text": "hello"},
            timeout=15,
        )
