from django.urls import path
from . import views

urlpatterns = [
    path('<slug:judgeID>/', views.judge,  name='judge'),
    path('',views.judge_index, name='judge_index')
]