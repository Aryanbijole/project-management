from rest_framework import serializers
from .models import (
    TodoList,
    TodoItem,
    TodoActivity,
    TaskAttachment,
    ChecklistItem
)


class TodoActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TodoActivity
        fields = '__all__'


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = '__all__'


class TaskAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAttachment
        fields = '__all__'


class TodoItemSerializer(serializers.ModelSerializer):
    activities = TodoActivitySerializer(many=True, read_only=True)

    class Meta:
        model = TodoItem
        fields = '__all__'


class TodoListSerializer(serializers.ModelSerializer):
    items = TodoItemSerializer(many=True, read_only=True)

    class Meta:
        model = TodoList
        fields = '__all__'