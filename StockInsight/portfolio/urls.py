from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('portfolio/', views.portfolio_view, name='portfolio'),
]
