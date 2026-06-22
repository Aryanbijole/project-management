from rest_framework import serializers
from .models import Project, ProjectTool


class ProjectToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTool
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    tools = ProjectToolSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'company',
            'created_by',
            'members',
            'created_at',
            'tools'
        ]