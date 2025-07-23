from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from .models import Subscription
from .forms import SubscriptionForm, CustomUserCreationForm, UserProfileForm, EditUserForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseRedirect
from django.urls import reverse
import csv
from io import TextIOWrapper
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
import json

# Create your views here.

def login_view(request):
    """Simple login view."""
    if request.user.is_authenticated:
        return redirect('subscriptions:subscription_list')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('subscriptions:subscription_list')
    else:
        form = AuthenticationForm()
    
    return render(request, 'subscriptions/login.html', {'form': form})

def logout_view(request):
    """Simple logout view."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('subscriptions:subscription_list')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('subscriptions:subscription_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'subscriptions/register.html', {'form': form})

def home_view(request):
    return render(request, 'subscriptions/home.html')

def renew_subscription(request, pk):
    from django.utils import timezone
    from datetime import timedelta
    sub = Subscription.objects.get(pk=pk, user=request.user)
    if sub.billing_cycle == 'monthly':
        # Add 1 month (handle month overflow)
        from dateutil.relativedelta import relativedelta
        sub.renewal_date = sub.renewal_date + relativedelta(months=1)
    elif sub.billing_cycle == 'yearly':
        from dateutil.relativedelta import relativedelta
        sub.renewal_date = sub.renewal_date + relativedelta(years=1)
    sub.save()
    messages.success(request, f'Renewal date for {sub.service_name} updated to {sub.renewal_date}.')
    return HttpResponseRedirect(reverse('subscriptions:subscription_list'))

@login_required
def import_subscriptions(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = TextIOWrapper(csv_file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)
        count = 0
        errors = []
        for row in reader:
            try:
                service_name = row['service_name']
                price = float(row['price'])
                billing_cycle = row['billing_cycle'].lower()
                renewal_date = row['renewal_date']
                if billing_cycle not in ['monthly', 'yearly']:
                    raise ValueError('Invalid billing_cycle')
                Subscription.objects.create(
                    user=request.user,
                    service_name=service_name,
                    price=price,
                    billing_cycle=billing_cycle,
                    renewal_date=renewal_date
                )
                count += 1
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {e}")
        if count:
            messages.success(request, f"Imported {count} subscriptions successfully.")
        if errors:
            messages.error(request, "Errors: " + "; ".join(errors))
        return redirect('subscriptions:subscription_list')
    return render(request, 'subscriptions/import_csv.html')

@login_required
def export_subscriptions(request):
    subscriptions = Subscription.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="subscriptions.csv"'
    writer = csv.writer(response)
    writer.writerow(['service_name', 'price', 'billing_cycle', 'renewal_date'])
    for sub in subscriptions:
        writer.writerow([
            sub.service_name,
            sub.price,
            sub.billing_cycle,
            sub.renewal_date.strftime('%Y-%m-%d')
        ])
    return response

@login_required
def profile_settings(request):
    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reminder days updated!')
            return redirect('subscriptions:profile_settings')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'subscriptions/profile_settings.html', {'form': form})

@login_required
def settings_view(request):
    from .models import UserProfile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    section = request.GET.get('section', 'reminder')
    reminder_form = UserProfileForm(instance=profile)
    edit_user_form = EditUserForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    if request.method == 'POST':
        if section == 'reminder':
            reminder_form = UserProfileForm(request.POST, instance=profile)
            if reminder_form.is_valid():
                reminder_form.save()
                messages.success(request, 'Reminder days updated!')
                return redirect(f'{request.path}?section=reminder')
        elif section == 'theme':
            theme_form = UserProfileForm(request.POST, instance=profile)
            if theme_form.is_valid():
                theme_form.save()
                messages.success(request, 'Theme updated!')
                return redirect(f'{request.path}?section=theme')
        elif section == 'profile':
            edit_user_form = EditUserForm(request.POST, instance=request.user)
            if edit_user_form.is_valid():
                edit_user_form.save()
                messages.success(request, 'Profile updated!')
                return redirect(f'{request.path}?section=profile')
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully!')
                return redirect(f'{request.path}?section=profile')
    return render(request, 'subscriptions/settings.html', {
        'section': section,
        'reminder_form': reminder_form,
        'theme_form': UserProfileForm(instance=profile),
        'edit_user_form': edit_user_form,
        'password_form': password_form,
    })

class SubscriptionListView(LoginRequiredMixin, ListView):
    """Display all subscriptions for the logged-in user."""
    model = Subscription
    template_name = 'subscriptions/list.html'
    context_object_name = 'subscriptions'
    paginate_by = 10
    
    def get_queryset(self):
        qs = Subscription.objects.filter(user=self.request.user)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            qs = qs.filter(
                Q(service_name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
            
        billing_cycle = self.request.GET.get('billing_cycle')
        status = self.request.GET.get('status')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        from django.utils import timezone
        today = timezone.now().date()
        # Billing cycle filter
        if billing_cycle in ['monthly', 'yearly']:
            qs = qs.filter(billing_cycle=billing_cycle)
        # Status filter
        if status == 'due_soon':
            from datetime import timedelta
            due_soon_date = today + timedelta(days=7)
            qs = qs.filter(renewal_date__gt=today, renewal_date__lte=due_soon_date)
        elif status == 'overdue':
            qs = qs.filter(renewal_date__lt=today)
        elif status == 'active':
            from datetime import timedelta
            due_soon_date = today + timedelta(days=7)
            qs = qs.filter(renewal_date__gt=due_soon_date)
        # Price range filter
        if min_price:
            try:
                qs = qs.filter(price__gte=float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                qs = qs.filter(price__lte=float(max_price))
            except ValueError:
                pass
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        full_queryset = self.get_queryset()
        total_monthly = sum(sub.monthly_cost for sub in full_queryset)
        total_annual = sum(sub.annual_cost for sub in full_queryset)
        from django.utils import timezone
        from datetime import timedelta
        due_soon_date = timezone.now().date() + timedelta(days=7)
        due_soon = full_queryset.filter(renewal_date__lte=due_soon_date)
        
        # Category breakdown
        category_data = full_queryset.values('category').annotate(
            total=Sum('price'),
            count=Count('id')
        ).order_by('-total')
        
        # Monthly spending trend (last 6 months)
        from datetime import datetime, timedelta
        six_months_ago = datetime.now().date() - timedelta(days=180)
        monthly_trend = []
        for i in range(6):
            month_start = datetime.now().date().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            month_subs = full_queryset.filter(
                renewal_date__gte=month_start,
                renewal_date__lte=month_end
            )
            monthly_total = sum(sub.monthly_cost for sub in month_subs)
            monthly_trend.append({
                'month': month_start.strftime('%b %Y'),
                'total': float(monthly_total)
            })
        monthly_trend.reverse()
        
        # Add current filter values to context for template
        context.update({
            'total_monthly': total_monthly,
            'total_annual': total_annual,
            'due_soon': due_soon,
            'category_data': category_data,
            'monthly_trend_json': json.dumps(monthly_trend),
            'search_query': self.request.GET.get('search', ''),
            'filter_category': self.request.GET.get('category', ''),
            'filter_billing_cycle': self.request.GET.get('billing_cycle', ''),
            'filter_status': self.request.GET.get('status', ''),
            'filter_min_price': self.request.GET.get('min_price', ''),
            'filter_max_price': self.request.GET.get('max_price', ''),
        })
        return context


class SubscriptionCreateView(LoginRequiredMixin, CreateView):
    """Form to create a new subscription."""
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'subscriptions/form.html'
    success_url = reverse_lazy('subscriptions:subscription_list')
    
    def form_valid(self, form):
        """Set the user to the current user before saving."""
        form.instance.user = self.request.user
        form.user = self.request.user  # Pass user to form for validation
        messages.success(self.request, f'Subscription "{form.instance.service_name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add context data for the form."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Subscription'
        context['button_text'] = 'Create Subscription'
        return context


class SubscriptionUpdateView(LoginRequiredMixin, UpdateView):
    """Form to edit an existing subscription."""
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'subscriptions/form.html'
    success_url = reverse_lazy('subscriptions:subscription_list')
    
    def get_queryset(self):
        """Ensure users can only edit their own subscriptions."""
        return Subscription.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        """Show success message after updating."""
        form.user = self.request.user  # Pass user to form for validation
        messages.success(self.request, f'Subscription "{form.instance.service_name}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add context data for the form."""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Subscription'
        context['button_text'] = 'Update Subscription'
        return context


class SubscriptionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete confirmation view for subscriptions."""
    model = Subscription
    template_name = 'subscriptions/confirm_delete.html'
    success_url = reverse_lazy('subscriptions:subscription_list')
    
    def get_queryset(self):
        """Ensure users can only delete their own subscriptions."""
        return Subscription.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """Show success message after deletion."""
        subscription = self.get_object()
        messages.success(request, f'Subscription "{subscription.service_name}" deleted successfully!')
        return super().delete(request, *args, **kwargs)
