from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Optional

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from main.models import CampaignMessageLog, CustomerCampaignContact, DailyRate
from main.services.messaging import send_message
from order.models import Order


def _clean_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    return "".join(ch for ch in str(phone) if ch.isdigit())


class Command(BaseCommand):
    help = "Send automated WhatsApp/SMS campaigns: order_ready, due_payment, rate_alert, birthday."

    def add_arguments(self, parser):
        parser.add_argument("--campaign", choices=["order_ready", "due_payment", "rate_alert", "birthday", "all"], default="all")
        parser.add_argument("--channel", choices=["sms", "whatsapp"], default="sms")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--limit", type=int, default=0, help="Max messages to send for this run (0 = no limit)")

    def handle(self, *args, **options):
        campaign = options["campaign"]
        channel = options["channel"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        campaigns: List[str]
        if campaign == "all":
            campaigns = ["order_ready", "due_payment", "rate_alert", "birthday"]
        else:
            campaigns = [campaign]

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for c in campaigns:
            recipients = self._collect_recipients(c, channel)
            if limit > 0:
                recipients = recipients[:limit]

            self.stdout.write(self.style.NOTICE(f"Campaign {c}: {len(recipients)} recipients"))
            for item in recipients:
                recipient_phone = item["phone"]
                recipient_name = item.get("name")
                message_text = item["message"]
                related_order = item.get("order")

                if self._already_sent_today(c, channel, recipient_phone, related_order):
                    CampaignMessageLog.objects.create(
                        campaign_type=c,
                        channel=channel,
                        recipient_name=recipient_name,
                        recipient_phone=recipient_phone,
                        message_body=message_text,
                        status="skipped",
                        related_order=related_order,
                        error_message="Duplicate suppressed (already sent today).",
                    )
                    skipped_count += 1
                    continue

                if dry_run:
                    CampaignMessageLog.objects.create(
                        campaign_type=c,
                        channel=channel,
                        recipient_name=recipient_name,
                        recipient_phone=recipient_phone,
                        message_body=message_text,
                        status="queued",
                        related_order=related_order,
                    )
                    self.stdout.write(f"[DRY RUN] {c} -> {recipient_phone}: {message_text[:80]}")
                    skipped_count += 1
                    continue

                success, provider_id, error_message = send_message(channel, recipient_phone, message_text)
                CampaignMessageLog.objects.create(
                    campaign_type=c,
                    channel=channel,
                    recipient_name=recipient_name,
                    recipient_phone=recipient_phone,
                    message_body=message_text,
                    status="sent" if success else "failed",
                    provider_message_id=provider_id,
                    error_message=error_message,
                    related_order=related_order,
                    sent_at=timezone.now() if success else None,
                )
                if success:
                    sent_count += 1
                else:
                    failed_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Completed. Sent={sent_count}, Skipped={skipped_count}, Failed={failed_count}"
        ))

    def _already_sent_today(self, campaign: str, channel: str, phone: str, order: Optional[Order]) -> bool:
        today = timezone.localdate()
        q = CampaignMessageLog.objects.filter(
            campaign_type=campaign,
            channel=channel,
            recipient_phone=phone,
            status="sent",
            created_at__date=today,
        )
        if order is not None:
            q = q.filter(related_order=order)
        return q.exists()

    def _collect_recipients(self, campaign: str, channel: str) -> List[Dict]:
        if campaign == "order_ready":
            return self._collect_order_ready(channel)
        if campaign == "due_payment":
            return self._collect_due_payment(channel)
        if campaign == "rate_alert":
            return self._collect_rate_alert(channel)
        if campaign == "birthday":
            return self._collect_birthday(channel)
        return []

    def _collect_order_ready(self, channel: str) -> List[Dict]:
        rows: List[Dict] = []
        qs = Order.objects.filter(status="completed").order_by("-updated_at")
        for order in qs:
            phone = _clean_phone(order.phone_number)
            if not phone:
                continue
            message_text = (
                f"Namaste {order.customer_name}, your order #{order.sn} is ready for pickup. "
                f"Total: रु{order.total:.2f}, Remaining: रु{order.remaining_amount:.2f}."
            )
            rows.append({"phone": phone, "name": order.customer_name, "message": message_text, "order": order})
        return rows

    def _collect_due_payment(self, channel: str) -> List[Dict]:
        rows: List[Dict] = []
        qs = Order.objects.filter(remaining_amount__gt=0).order_by("-updated_at")
        for order in qs:
            phone = _clean_phone(order.phone_number)
            if not phone:
                continue
            message_text = (
                f"Namaste {order.customer_name}, payment reminder for order #{order.sn}. "
                f"Pending amount: रु{order.remaining_amount:.2f}. Please visit Nirmala Jewellers."
            )
            rows.append({"phone": phone, "name": order.customer_name, "message": message_text, "order": order})
        return rows

    def _collect_rate_alert(self, channel: str) -> List[Dict]:
        latest_rate = DailyRate.objects.order_by("-created_at").first()
        if not latest_rate:
            return []

        recipients: Dict[str, Dict] = {}

        # Manual campaign contacts
        contacts = CustomerCampaignContact.objects.filter(is_active=True)
        if channel == "sms":
            contacts = contacts.filter(sms_opt_in=True)
        else:
            contacts = contacts.filter(whatsapp_opt_in=True)

        for contact in contacts:
            phone = _clean_phone(contact.phone_number)
            if not phone:
                continue
            recipients[phone] = {"phone": phone, "name": contact.name}

        # Add order customers as fallback audience
        for order in Order.objects.exclude(phone_number__isnull=True).exclude(phone_number=""):
            phone = _clean_phone(order.phone_number)
            if not phone:
                continue
            if phone not in recipients:
                recipients[phone] = {"phone": phone, "name": order.customer_name}

        rows: List[Dict] = []
        for item in recipients.values():
            message_text = (
                f"Rate Alert ({latest_rate.bs_date}): Gold रु{latest_rate.gold_rate:.2f}/tola, "
                f"Silver रु{latest_rate.silver_rate:.2f}/tola."
            )
            rows.append({"phone": item["phone"], "name": item.get("name"), "message": message_text, "order": None})
        return rows

    def _collect_birthday(self, channel: str) -> List[Dict]:
        today = date.today()
        rows: List[Dict] = []
        contacts = CustomerCampaignContact.objects.filter(
            is_active=True,
            birthday__month=today.month,
            birthday__day=today.day,
        )
        if channel == "sms":
            contacts = contacts.filter(sms_opt_in=True)
        else:
            contacts = contacts.filter(whatsapp_opt_in=True)

        for contact in contacts:
            phone = _clean_phone(contact.phone_number)
            if not phone:
                continue
            message_text = (
                f"Happy Birthday {contact.name}! Wishing you joy and prosperity from Nirmala Jewellers. "
                f"Visit us for your special birthday offer."
            )
            rows.append({"phone": phone, "name": contact.name, "message": message_text, "order": None})
        return rows
