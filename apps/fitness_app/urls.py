from django.urls import path
from .views import *
from accounts.views import main_account

urlpatterns = [
    path('',user_plan,name='user_plan'),

    path('user_list/',plan_list,name='user_list'),
    path('user_create/',plan_create,name="user_create"),
    path('user_edit/<int:pk>/',plan_edit,name="user_edit"),
    path('user_delete/<int:pk>/',plan_delete,name="user_delete"),

    path('reports/',AIReportView.as_view(),name="reports"),
    path('ai_page/', AIPageDetailView.as_view(),name="ai_page"),

    # path('', main_account, name='main_account'),
]