from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from projects.models import Project
from communication.models import MessageBoardPost, Comment, PrivateMessage
from accounts.models import User
from accounts.decorators import company_required
from django.utils import timezone

@login_required
@company_required
def message_board_view(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to access this message board."
                )
                return redirect("dashboard")

    # -----------------------------------------
    # Fetch Posts
    # -----------------------------------------

    posts = MessageBoardPost.objects.filter(
        project=project
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "communication/message_board.html",
        {
            "project": project,
            "posts": posts,
        },
    )

@login_required
@company_required
def create_post_view(request, project_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to create posts in this project."
                )
                return redirect("dashboard")

    # -----------------------------------------
    # Create Post
    # -----------------------------------------

    if request.method == "POST":

        title = request.POST.get("title")
        content = request.POST.get("content")

        if title and content:

            MessageBoardPost.objects.create(
                project=project,
                title=title,
                content=content,
                author=request.user,
            )

            messages.success(
                request,
                f"Post '{title}' created successfully!"
            )

            return redirect(
                "message_board",
                project_id=project.id,
            )

        messages.error(
            request,
            "Title and content are required."
        )

    return render(
        request,
        "communication/create_post.html",
        {
            "project": project,
        },
    )


@login_required
@company_required
def post_detail_view(request, project_id, post_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to view this discussion."
                )
                return redirect("dashboard")

    # -----------------------------------------
    # Fetch Post
    # -----------------------------------------

    post = get_object_or_404(
        MessageBoardPost,
        id=post_id,
        project=project,
    )

    comments = post.comments.all().order_by(
        "created_at"
    )

    return render(
        request,
        "communication/post_detail.html",
        {
            "project": project,
            "post": post,
            "comments": comments,
        },
    )


@login_required
@company_required
def add_comment_view(request, project_id, post_id):

    project = get_object_or_404(
        Project,
        id=project_id,
    )

    # -----------------------------------------
    # Permission Check
    # -----------------------------------------

    if not request.user.is_superuser:

        membership = request.user.memberships.filter(
            company=project.company
        ).first()

        # User does not belong to this company
        if not membership:
            messages.error(
                request,
                "Access denied."
            )
            return redirect("dashboard")

        # Company Admin can access every project
        if membership.role != User.ROLE_ADMIN:

            # Members can access only assigned projects
            if not project.members.filter(id=request.user.id).exists():
                messages.error(
                    request,
                    "You are not authorized to comment on this discussion."
                )
                return redirect("dashboard")

    # -----------------------------------------
    # Fetch Post
    # -----------------------------------------

    post = get_object_or_404(
        MessageBoardPost,
        id=post_id,
        project=project,
    )

    # -----------------------------------------
    # Add Comment
    # -----------------------------------------

    if request.method == "POST":

        content = request.POST.get("content")

        if content:

            Comment.objects.create(
                post=post,
                content=content,
                author=request.user,
            )

            messages.success(
                request,
                "Comment added successfully!"
            )

        else:

            messages.error(
                request,
                "Comment content cannot be empty."
            )

    return redirect(
        "post_detail",
        project_id=project.id,
        post_id=post.id,
    )

@login_required
@company_required
def chat_hub_view(request, user_id=None):

    # --------------------------------------------------
    # Superuser
    # --------------------------------------------------

    if request.user.is_superuser:

        chat_users = User.objects.filter(
            is_active=True
        ).exclude(
            id=request.user.id
        ).prefetch_related(
            "memberships__company"
        )

    # --------------------------------------------------
    # Company Users
    # --------------------------------------------------

    else:

        company = request.current_company

        chat_users = User.objects.filter(
            memberships__company=company,
            is_active=True,
        ).exclude(
            id=request.user.id
        ).distinct()

    active_chat_user = None
    chat_messages = []

    if user_id:

        # -----------------------------------------
        # Superuser
        # -----------------------------------------

        if request.user.is_superuser:

            active_chat_user = get_object_or_404(
                User,
                id=user_id,
                is_active=True,
            )

        # -----------------------------------------
        # Company Users
        # -----------------------------------------

        else:

            active_chat_user = get_object_or_404(
                User,
                id=user_id,
                memberships__company=request.current_company,
                is_active=True,
            )

        # -----------------------------------------
        # Conversation
        # -----------------------------------------

        chat_messages = PrivateMessage.objects.filter(
            Q(sender=request.user, receiver=active_chat_user) |
            Q(sender=active_chat_user, receiver=request.user)
        ).order_by(
            "created_at"
        )

    return render(
        request,
        "communication/chat.html",
        {
            "chat_users": chat_users,
            "active_chat_user": active_chat_user,
            "chat_messages": chat_messages,
        },
    )


@login_required
@company_required
def send_chat_message(request, user_id):
    if request.user.is_superuser:

        receiver = get_object_or_404(
            User,
            id=user_id,
            is_active=True,
        )

    else:

        receiver = get_object_or_404(
            User,
            id=user_id,
            is_active=True,
        )

        if (
            not receiver.is_superuser and
            not receiver.memberships.filter(
                company=request.current_company
            ).exists()
        ):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Access denied."
                },
                status=403,
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
                    'created_at': timezone.localtime(
                         msg.created_at
                    ).strftime('%d %b %Y • %I:%M %p'),
                    'is_seen': msg.is_seen,
                }
            })
        return JsonResponse({'status': 'error', 'message': 'Empty message content.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


@login_required
@company_required
def get_chat_messages(request, user_id):
    if request.user.is_superuser:

        receiver = get_object_or_404(
            User,
            id=user_id,
            is_active=True,
        )

    else:

        receiver = get_object_or_404(
            User,
            id=user_id,
            is_active=True,
        )

        if (
            not receiver.is_superuser and
            not receiver.memberships.filter(
                company=request.current_company
            ).exists()
        ):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Access denied."
                },
                status=403,
            )

    PrivateMessage.objects.filter(
        sender=receiver,
        receiver=request.user,
        is_seen=False,
    ).update(
        is_seen=True,
        seen_at=timezone.now(),
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
        'created_at': timezone.localtime(
            msg.created_at
        ).strftime('%d %b %Y • %I:%M %p'),
        "is_seen": msg.is_seen,
    } for msg in messages_query]

    return JsonResponse({'status': 'success', 'messages': data})
