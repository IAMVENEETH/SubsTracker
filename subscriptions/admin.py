from django.contrib import admin
from .models import Subscription

# Register your models here.

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'user', 'price', 'billing_cycle', 'renewal_date', 'is_due_soon', 'is_overdue']
    list_filter = ['billing_cycle', 'renewal_date', 'user']
    search_fields = ['service_name', 'user__username', 'user__email']
    date_hierarchy = 'renewal_date'
    ordering = ['renewal_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'service_name', 'price', 'billing_cycle')
        }),
        ('Renewal Information', {
            'fields': ('renewal_date',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_due_soon(self, obj):
        """Display if subscription is due soon."""
        if obj.is_due_soon():
            return "⚠️ Due Soon"
        return "✅ OK"
    is_due_soon.short_description = "Status"
    
    def is_overdue(self, obj):
        """Display if subscription is overdue."""
        if obj.is_overdue():
            return "🔴 Overdue"
        return "✅ Current"
    is_overdue.short_description = "Overdue"
