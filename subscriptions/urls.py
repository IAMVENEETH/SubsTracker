from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.SubscriptionListView.as_view(), name='subscription_list'),
    path('add/', views.SubscriptionCreateView.as_view(), name='subscription_create'),
    path('edit/<int:pk>/', views.SubscriptionUpdateView.as_view(), name='subscription_update'),
    path('delete/<int:pk>/', views.SubscriptionDeleteView.as_view(), name='subscription_delete'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('renew/<int:pk>/', views.renew_subscription, name='subscription_renew'),
    path('import-csv/', views.import_subscriptions, name='import_csv'),
    path('export-csv/', views.export_subscriptions, name='export_csv'),
    path('profile/', views.profile_settings, name='profile_settings'),
    path('settings/', views.settings_view, name='settings'),
] 