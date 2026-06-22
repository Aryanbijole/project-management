from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views_api import UserViewSet
from projects.views_api import ProjectViewSet
from tasks.views_api import TodoListViewSet, TodoItemViewSet
from communication.views_api import (
    MessageBoardPostViewSet,
    CommentViewSet,
    PrivateMessageViewSet,
)

router = DefaultRouter()

router.register(r'users', UserViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'todolists', TodoListViewSet)
router.register(r'tasks', TodoItemViewSet)
router.register(r'posts', MessageBoardPostViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'messages', PrivateMessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]