from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import MessageSerializer

User = get_user_model()

class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            other_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=404)

        user1, user2 = request.user, other_user
        if user1.id > user2.id:
            user1, user2 = user2, user1

        try:
            conversation = Conversation.objects.get(user1=user1, user2=user2)
        except Conversation.DoesNotExist:
            return Response([], status=200)

        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
