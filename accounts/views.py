from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# JWT Login View
class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from rest_framework.response import Response

User = get_user_model()


class UserListView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        users = User.objects.exclude(id=request.user.id).values_list('username', flat=True)
        return Response(list(users))