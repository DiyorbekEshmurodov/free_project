from django.urls import path
from .views import *
urlpatterns = [
    path('',main_account,name='home'),
    path('auto-login/<int:telegram_id>/', auto_login_view, name='auto_login'),
    path('dashboard/',index_page,name='index'),
    path('profile/', profile_setup, name='profile_setup'),
    path('login/',login_page,name='login_page'),
    path('logout/',logout_page,name='logout_page'),
]
