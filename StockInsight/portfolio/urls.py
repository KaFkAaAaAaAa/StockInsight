from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('account/edit/', views.account_edit_view, name='account_edit'),
    path('account/history/', views.account_history_view, name='account_history'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/<str:window>/', views.dashboard_view, name='dashboard_with_window'),
    path('currencies/currency/<str:search>/<str:window>/', views.currency_view, name='currency_view'),
    path('market/', views.market_view, name='market'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)