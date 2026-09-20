from django.urls import path
from .views import *
from accounts.views import index_page

urlpatterns = [

    path('dashboard/',index_page,name='index'),
    path('<str:section_name>/', cards_list_view, name='cards_list'),
    path('<str:section_name>/<str:question_id>/', card_detail_view, name='card_detail')
,
]