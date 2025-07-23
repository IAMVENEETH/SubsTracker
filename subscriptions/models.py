from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    reminder_days = models.PositiveIntegerField(default=1, help_text='Days before renewal to send reminder email')
    dark_theme = models.BooleanField(default=False, help_text='Enable dark theme')

    def __str__(self):
        return f"Profile for {self.user.username}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()

class Subscription(models.Model):
    """
    Model to track user subscriptions to various services.
    """
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    CATEGORY_CHOICES = [
        ('entertainment', 'Entertainment'),
        ('productivity', 'Productivity'),
        ('education', 'Education'),
        ('health', 'Health & Fitness'),
        ('news', 'News & Media'),
        ('cloud', 'Cloud Storage'),
        ('software', 'Software'),
        ('gaming', 'Gaming'),
        ('music', 'Music'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='subscriptions',
        help_text="The user who owns this subscription"
    )
    
    service_name = models.CharField(
        max_length=100,
        help_text="Name of the subscription service (e.g., Netflix, Spotify)"
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Category of the subscription service"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes about this subscription"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Monthly or yearly price of the subscription"
    )
    
    billing_cycle = models.CharField(
        max_length=10,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly',
        help_text="Billing frequency for the subscription"
    )
    
    renewal_date = models.DateField(
        help_text="Next renewal date for the subscription"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['renewal_date']
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
    
    def __str__(self):
        return f"{self.service_name} - {self.user.username}"
    
    @property
    def annual_cost(self):
        """Calculate the annual cost of the subscription."""
        if self.billing_cycle == 'yearly':
            return self.price
        else:  # monthly
            return self.price * 12
    
    @property
    def monthly_cost(self):
        """Calculate the monthly cost of the subscription."""
        if self.billing_cycle == 'monthly':
            return self.price
        else:  # yearly
            return self.price / 12
    
    def is_due_soon(self, days=7):
        """Check if the subscription is due for renewal within the specified days."""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        due_date = self.renewal_date - timedelta(days=days)
        return today >= due_date
    
    def is_overdue(self):
        """Check if the subscription renewal date has passed."""
        from django.utils import timezone
        
        today = timezone.now().date()
        return today > self.renewal_date
