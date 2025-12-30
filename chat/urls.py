from django.urls import path
from .views import ChatHistoryView

urlpatterns = [
    path('history/<str:username>/', ChatHistoryView.as_view()),
]
