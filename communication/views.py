from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from projects.models import Project
from communication.models import MessageBoardPost, Comment, PrivateMessage
from accounts.models import User
from accounts.decorators import company_required

@login_required
@company_required
def message_board_view(request, project_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )
    posts = MessageBoardPost.objects.filter(project=project).order_by('-created_at')

    return render(request, 'communication/message_board.html', {
        'project': project,
        'posts': posts
    })


@login_required
@company_required
def create_post_view(request, project_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        if title and content:
            post = MessageBoardPost.objects.create(
                project=project,
                title=title,
                content=content,
                author=request.user
            )
            messages.success(request, f"Post '{title}' created successfully!")
            return redirect('message_board', project_id=project.id)
        else:
            messages.error(request, "Title and content are required.")

    return render(request, 'communication/create_post.html', {
        'project': project
    })


@login_required
@company_required
def post_detail_view(request, project_id, post_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )
    post = get_object_or_404(MessageBoardPost, id=post_id, project=project)
    comments = post.comments.all().order_by('created_at')

    return render(request, 'communication/post_detail.html', {
        'project': project,
        'post': post,
        'comments': comments
    })


@login_required
@company_required
def add_comment_view(request, project_id, post_id):
    company = request.user.memberships.first().company

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company
    )
    post = get_object_or_404(MessageBoardPost, id=post_id, project=project)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                post=post,
                content=content,
                author=request.user
            )
            messages.success(request, "Comment added successfully!")
        else:
            messages.error(request, "Comment content cannot be empty.")

    return redirect('post_detail', project_id=project.id, post_id=post.id)


@login_required
@company_required
def chat_hub_view(request, user_id=None):
    # Get active users that the current user can chat with
    # (users in the same companies/organizations)
    user_companies = request.user.memberships.values_list('company_id', flat=True)
    chat_users = User.objects.filter(
        memberships__company_id__in=user_companies, 
        is_active=True
    ).exclude(id=request.user.id).distinct()

    active_chat_user = None
    chat_messages = []

    if user_id:

        active_chat_user = get_object_or_404(
            User,
            id=user_id,
            memberships__company__in=request.user.memberships.values("company"),
            is_active=True
        )
        # Fetch conversation
        chat_messages = PrivateMessage.objects.filter(
            Q(sender=request.user, receiver=active_chat_user) |
            Q(sender=active_chat_user, receiver=request.user)
        ).order_by('created_at')

    return render(request, 'communication/chat.html', {
        'chat_users': chat_users,
        'active_chat_user': active_chat_user,
        'chat_messages': chat_messages
    })


@login_required
@company_required
def send_chat_message(request, user_id):
    receiver = get_object_or_404(
        User,
        id=user_id,
        memberships__company__in=request.user.memberships.values("company"),
        is_active=True
    )
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            msg = PrivateMessage.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': msg.id,
                    'content': msg.content,
                    'sender_email': msg.sender.email,
                    'sender_name': msg.sender.first_name,
                    'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        return JsonResponse({'status': 'error', 'message': 'Empty message content.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
@company_required
def get_chat_messages(request, user_id):
    receiver = get_object_or_404(
        User,
        id=user_id,
        memberships__company__in=request.user.memberships.values("company"),
        is_active=True
    )
    messages_query = PrivateMessage.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user)
    ).order_by('created_at')

    data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.first_name,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages_query]

    return JsonResponse({'status': 'success', 'messages': data})
