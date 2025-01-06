from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/<str:window>/', views.dashboard_view, name='dashboard_with_window'),
    path('currencies/currency/<str:search>/<str:window>/', views.currency_view, name='currency_view'),
]