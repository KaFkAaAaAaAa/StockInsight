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
    path('market/<str:selected_stock>/<str:window>/', views.market_view, name='market_view'),
    path('market/', views.market_view, name='market_view'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/<str:window>/', views.dashboard_view, name='dashboard_with_window'),
    path('currencies/currency/<str:search>/<str:window>/', views.currency_view, name='currency_view'),

    # jak nie działa to odkomencić
    # path('account/', views.account_view, name='account'),

    # FORUM MODULE
    path('forum/', views.post_list, name='post_list'),
    path('forum/post/<int:pk>/', views.post_detail, name='post_detail'),
    path('forum/post/new/', views.post_new, name='post_new'),
    # -------------
    path('market/', views.market_view, name='market'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)