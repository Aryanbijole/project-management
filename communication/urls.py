from django.urls import path
from communication import views

urlpatterns = [
    path('projects/<int:project_id>/message-board/', views.message_board_view, name='message_board'),
    path('projects/<int:project_id>/message-board/create/', views.create_post_view, name='create_post'),
    path('projects/<int:project_id>/message-board/<int:post_id>/', views.post_detail_view, name='post_detail'),
    path('projects/<int:project_id>/message-board/<int:post_id>/comment/', views.add_comment_view, name='add_comment'),
    path('chat/', views.chat_hub_view, name='chat_hub'),
    path('chat/<int:user_id>/', views.chat_hub_view, name='chat_user'),
    path('chat/<int:user_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/<int:user_id>/messages/', views.get_chat_messages, name='get_chat_messages'),
]
