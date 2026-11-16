"""Daily billing jobs: fee due/overdue reminders and platform past-due marking.

Idempotent; schedule once a day (cron or a scheduler container):
    python manage.py run_billing_jobs
"""

import logging

from django.core.management.base import BaseCommand

from core.services import fees, subscriptions

logger = logging.getLogger('core.jobs')


class Command(BaseCommand):
    help = 'Send fee reminders to guardians and mark overdue platform subscriptions.'

    def handle(self, *args, **options):
        try:
            reminders = fees.send_due_reminders()
            past_due = subscriptions.mark_overdue_subscriptions()
        except Exception:
            # Logged under "core" so an error alert is sent when alerts are enabled.
            logger.exception('run_billing_jobs failed')
            raise
        self.stdout.write(f'fee reminders processed: {reminders}; subscriptions marked past_due: {past_due}')
