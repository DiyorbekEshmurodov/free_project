from django.urls import path
from .views import *


urlpatterns = [
    path('',user_plan,name='user_plan'),

    path('user_list/',user_list,name='user_list'),
    path('user_create/',user_create,name="user_create"),
    path('user_edit/<int:pk>/',user_edit,name="user_edit"),
    path('user_delete/<int:pk>/',user_delete,name="user_delete"),

    path('reports/',AIReportView.as_view(),name="reports"),
    path('ai_page/', AIPageDetailView.as_view(),name="ai_page"),


]