from django.urls import path
from . import views

urlpatterns = [
    path('edit/<slug:problemID>',views.problem_edit, name='problem_edit'),
    path('<slug:problemID>', views.problem,  name='problem'),
    path('',views.problem_index, name='problem_index')
]