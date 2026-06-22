from rest_framework import viewsets
from .models import MessageBoardPost, Comment, PrivateMessage
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    MessageBoardPostSerializer,
    CommentSerializer,
    PrivateMessageSerializer,
)


class MessageBoardPostViewSet(viewsets.ModelViewSet):
    queryset = MessageBoardPost.objects.all()
    serializer_class = MessageBoardPostSerializer
    permission_classes = [IsAuthenticated]


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


class PrivateMessageViewSet(viewsets.ModelViewSet):
    queryset = PrivateMessage.objects.all()
    serializer_class = PrivateMessageSerializer
    permission_classes = [IsAuthenticated]