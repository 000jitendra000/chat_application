from django.urls import path
from .views import login_view, chat_view, register_view

urlpatterns = [
    path('', login_view, name='login'),
    path('chat/', chat_view, name='chat'),
    path('register/', register_view, name='register'),
]
