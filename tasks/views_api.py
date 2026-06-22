from rest_framework import viewsets
from .models import TodoList, TodoItem
from .serializers import TodoListSerializer, TodoItemSerializer
from rest_framework.permissions import IsAuthenticated


class TodoListViewSet(viewsets.ModelViewSet):
    queryset = TodoList.objects.all()
    serializer_class = TodoListSerializer
    permission_classes = [IsAuthenticated]


class TodoItemViewSet(viewsets.ModelViewSet):
    queryset = TodoItem.objects.all()
    serializer_class = TodoItemSerializer
    permission_classes = [IsAuthenticated]