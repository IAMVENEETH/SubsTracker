from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from subscriptions.models import Subscription, UserProfile
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Send email reminders for subscriptions due soon, using user-specific reminder_days.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        count = 0
        for user in User.objects.filter(is_active=True):
            if not hasattr(user, 'profile') or not user.email:
                continue
            reminder_days = user.profile.reminder_days
            due_date = today + timezone.timedelta(days=reminder_days)
            due_subs = Subscription.objects.filter(user=user, renewal_date=due_date)
            for sub in due_subs:
                subject = f'Reminder: {sub.service_name} subscription renews in {reminder_days} day(s)!'
                message = (
                    f'Hi {user.username},\n\n'
                    f'This is a reminder that your subscription to "{sub.service_name}" '
                    f'will renew on {sub.renewal_date}.\n\n'
                    f'Amount: ${sub.price} ({sub.get_billing_cycle_display()})\n\n'
                    'If you wish to make changes, please log in to SubTrack.\n\n'
                    'Thank you!\nSubTrack Team'
                )
                send_mail(
                    subject,
                    message,
                    None,  # Use DEFAULT_FROM_EMAIL
                    [user.email],
                    fail_silently=False,
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Sent reminder to {user.email} for {sub.service_name}'))
        if count == 0:
            self.stdout.write('No reminders to send today.') 