from django.urls import path
from .views import (
    auto_login_view,
    index_page,
    login_page,
    logout_page,
    main_account,
    profile_setup,
)
urlpatterns = [
    path('',main_account,name='home'),
    path('auto-login/<str:token>/', auto_login_view, name='auto_login'),
    path('dashboard/',index_page,name='index'),
    path('profile/', profile_setup, name='profile_setup'),
    path('login/',login_page,name='login_page'),
    path('logout/',logout_page,name='logout_page'),
]
