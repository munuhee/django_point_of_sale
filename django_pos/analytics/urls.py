from django.urls import path
from .views import analytics_view

app_name = 'analytics'

urlpatterns = [
    path('analytics/', analytics_view, name='analytics_view'),
    # Add more URL patterns if needed
]
