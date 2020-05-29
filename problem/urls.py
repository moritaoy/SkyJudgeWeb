from django.urls import path
from . import views
app_name="problem"
urlpatterns = [
    path('edit/<slug:problemID>',views.problem_edit, name='problem_edit'),
    path('create/',views.problem_create, name='problem_create'),
    path('<slug:problemID>', views.problem,  name='problem'),
    path('',views.problem_index, name='problem_index')
]