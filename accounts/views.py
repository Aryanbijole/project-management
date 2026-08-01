from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from accounts.models import User, Company, Group, CompanyMembership, Invitation
from accounts.services import merge_users
from projects.models import Project
from django.conf import settings
from accounts.models import Notification
from projects.models import ProjectActivity
from tasks.models import TodoActivity
from accounts.decorators import (
    company_required,
    company_admin_required,
    platform_admin_required,
)
from audit.utils import create_audit_log
from communication.models import GroupMessage
from .models import Group
from dashboard.permissions import has_company_permission

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = User.ROLE_MEMBER
        if not email or not password or not first_name or not last_name:
            messages.error(request, "All fields are required.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        else:
            username = email.split('@')[0]
            # Ensure username unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=User.ROLE_MEMBER
            )
            # Log the user in
            login(request, user)

            messages.success(request, "Registration successful!")

            from accounts.models import CompanyMembership

            membership = CompanyMembership.objects.filter(
                user=user
            ).exists()

            if membership:
                return redirect("dashboard")

            return redirect("company_setup")
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Email and password are required.")
        else:
            # Authenticate via custom User model
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_merged:
                    messages.error(request, "This account was merged into another user. Please log in with the new account.")
                elif not user.is_active:
                    messages.error(request, "This account is inactive.")
                else:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name}!")
                    return redirect('dashboard')
            else:
                messages.error(request, "Invalid email or password.")

    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


@login_required
@company_required
def dashboard_view(request):
   # Companies available to the logged-in user
    if request.user.is_superuser:
        companies = Company.objects.all().order_by("name")
    else:
        companies = Company.objects.filter(
            memberships__user=request.user
        ).order_by("name")

    # ------------------------------------------
    # Selected company
    # ------------------------------------------

    selected_company = None

    if request.user.is_superuser:

        company_id = request.GET.get("company")

        if company_id:
            selected_company = get_object_or_404(
                Company,
                id=company_id
            )

    elif companies.exists():

        # Company admins / normal users always use their own company
        selected_company = companies.first()    

    company_admin_membership = CompanyMembership.objects.filter(
        user=request.user,
        role=User.ROLE_ADMIN
    ).first()

    is_company_admin = company_admin_membership is not None

    # Projects user belongs to
    if request.user.is_superuser:
        projects = Project.objects.all()

        if selected_company:
            projects = projects.filter(company=selected_company) 

    else:
        projects = Project.objects.filter(
            Q(members=request.user) |
            Q(created_by=request.user) |
            Q(company__in=companies)
        ).distinct()

    # Groups in user's companies
    if request.user.is_superuser:
        groups = Group.objects.all()

        if selected_company:
            groups = groups.filter(company=selected_company)

    else:
        groups = Group.objects.filter(
            company__in=companies
        ).distinct()

    # Users in same companies (for display / chat list / merges)
    if request.user.is_superuser:
        company_users = User.objects.filter(
            is_active=True
        )

        if selected_company:
            company_users = company_users.filter(
                memberships__company=selected_company
            ).distinct()

    else:
        company_users = User.objects.filter(
            memberships__company__in=companies,
            is_active=True
        ).exclude(
            id=request.user.id
        ).distinct()

    # Pending invites
    if request.user.is_superuser:
        sent_invites = Invitation.objects.all()
    else:
        sent_invites = Invitation.objects.filter(
            invited_by=request.user
        )

    if request.user.is_superuser:
        recent_project_activities = ProjectActivity.objects.all()

        if selected_company:
            recent_project_activities = recent_project_activities.filter(
                project__company=selected_company
            )

        recent_project_activities = (
            recent_project_activities
            .select_related(
                "project",
                "user"
            )
           .order_by("-created_at")[:10]
        )


    else:
        recent_project_activities = (
            ProjectActivity.objects
            .filter(project__company__in=companies)
            .select_related(
                "project",
                "user"
            )
            .order_by("-created_at")[:10]
        )
        

    if request.user.is_superuser:
        recent_task_activities = TodoActivity.objects.all()

        if selected_company:
            recent_task_activities = recent_task_activities.filter(
                todo_item__todo_list__project__company=selected_company
            )

        recent_task_activities = (
            recent_task_activities
            .select_related(
                "todo_item",
                "actor",
                "todo_item__todo_list__project"
            )
            .order_by("-created_at")[:10]
        )


    else:
        recent_task_activities = (
            TodoActivity.objects
            .filter(
                todo_item__todo_list__project__company__in=companies
            )
            .select_related(
                "todo_item",
                "actor",
                "todo_item__todo_list__project"
            )
            .order_by("-created_at")[:10]
        )

    # ------------------------------------------
    # Custom Role Permissions
    # ------------------------------------------

    can_create_projects = False
    can_invite_members = False
    can_view_reports = False
    can_view_audit_logs = False

    if selected_company:
        can_create_projects = has_company_permission(
            request.user,
            selected_company,
            "can_create_projects",
        )

        can_invite_members = has_company_permission(
            request.user,
            selected_company,
            "can_invite_members",
        )

        can_view_reports = has_company_permission(
            request.user,
            selected_company,
            "can_view_reports",
        )

        can_view_audit_logs = has_company_permission(
            request.user,
            selected_company,
            "can_view_audit_logs",
        )    

    return render(request, 'accounts/dashboard.html', {
        'companies': companies,
        'projects': projects,
        'groups': groups,
        'company_users': company_users,
        'sent_invites': sent_invites,
        'roles': User.ROLE_CHOICES,
        "recent_project_activities": recent_project_activities,
        "recent_task_activities": recent_task_activities,
        "is_company_admin": is_company_admin,
        "selected_company": selected_company,
        "selected_company_id": (
            selected_company.id
            if selected_company
            else None
        ),
        "can_create_projects": can_create_projects,
        "can_invite_members": can_invite_members,
        "can_view_reports": can_view_reports,
        "can_view_audit_logs": can_view_audit_logs,
    })





@login_required
@company_admin_required
def create_group(request):

    if request.method != "POST":
        return redirect("dashboard")

    name = request.POST.get("name", "").strip()
    company_id = request.POST.get("company_id")
    project_id = request.POST.get("project")
    member_ids = request.POST.getlist("members")

    # -----------------------------------------
    # Determine Company
    # -----------------------------------------
    if request.user.is_superuser:

        company = get_object_or_404(
            Company,
            id=company_id,
        )

    else:

        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                role=User.ROLE_ADMIN,
            )
            .first()
        )

        if membership is None:

            messages.error(
                request,
                "You are not assigned as Company Admin."
            )

            return redirect("dashboard")

        company = membership.company

        if str(company.id) != str(company_id):

            messages.error(
                request,
                "You cannot create groups for another company."
            )

            return redirect("dashboard")

    # -----------------------------------------
    # Validation
    # -----------------------------------------

    if not name:

        messages.error(
            request,
            "Group name cannot be empty."
        )

        return redirect("dashboard")

    if Group.objects.filter(
        company=company,
        name=name,
    ).exists():

        messages.error(
            request,
            "A group with this name already exists."
        )

        return redirect("dashboard")

    # -----------------------------------------
    # Selected Project
    # -----------------------------------------

    project = get_object_or_404(
        Project,
        id=project_id,
        company=company,
    )

    # -----------------------------------------
    # Create Group
    # -----------------------------------------

    group = Group.objects.create(

        name=name,

        company=company,

        project=project,

    )

    # -----------------------------------------
    # Add Selected Members
    # -----------------------------------------

    if member_ids:

        users = User.objects.filter(
            id__in=member_ids,
            memberships__company=company,
        ).distinct()

        group.members.set(users)

    # -----------------------------------------
    # Always add creator
    # -----------------------------------------

    # Automatically add only Company Admin.
    # Superuser is NOT added automatically.

    if not request.user.is_superuser:
        group.members.add(request.user)

    # -----------------------------------------
    # Audit Log
    # -----------------------------------------

    create_audit_log(
        request,
        module="Group",
        action="CREATE",
        description=f"Created group '{group.name}'",
    )

    messages.success(
        request,
        f"Group '{group.name}' created successfully."
    )

    return redirect("dashboard")


@login_required
@company_admin_required
def send_invite(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        company_id = request.POST.get('company_id')
        role = request.POST.get('role', User.ROLE_MEMBER)

        company = get_object_or_404(Company, id=company_id)
        
        # Verify inviter has permissions
        # Platform Superuser can invite to any company
        if request.user.is_superuser:
            membership = None

        else:
            if (
                not request.user.is_superuser
                and company != request.current_company
            ):
                messages.error(
                    request,
                    "You can only invite users to your own company."
                )
                return redirect("dashboard")

        if email:
            # Check if user already exists and is already member
            user_exists = User.objects.filter(email=email).first()
            if user_exists and CompanyMembership.objects.filter(company=company, user=user_exists).exists():
                messages.warning(request, f"User '{email}' is already a member of this organization.")
                return redirect('dashboard')

            # Create invitation
            invitation = Invitation.objects.create(
                email=email,
                company=company,
                role=role,
                invited_by=request.user
            )

            # Build invite URL for template / email
            invite_url = request.build_absolute_uri(
                reverse('accept_invite', kwargs={'token': invitation.token})
            )

            # Log to terminal console (console email backend simulated)
            from django.core.mail import send_mail
            subject = f"Invitation to join {company.name}"
            message = f"You have been invited by {request.user.first_name} to join {company.name} as an {role}.\n\nClick the link below to accept:\n{invite_url}"
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True
            )

            # Display link in success alert for convenience
            messages.success(
                request, 
                f"Invitation sent to {email}! Link: {invite_url}"
            )
        else:
            messages.error(request, "Email address is required.")
    return redirect('dashboard')


def accept_invite(request, token):

    if request.user.is_authenticated:
        messages.warning(
            request,
            f"You are currently logged in as {request.user.email}. "
            "Please log out before accepting this invitation."
        )
        
        return redirect("dashboard")
    invitation = get_object_or_404(Invitation, token=token, is_accepted=False)
    company = invitation.company

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not first_name or not last_name or not password:
            messages.error(request, "All fields are required.")
        elif password != confirm_password:
            messages.error(request, "Passwords do not match.")
        else:
            # Create user
            username = invitation.email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            # Check if user with email exists (e.g. registered separately)
            user = User.objects.filter(email=invitation.email).first()
            if not user:
                user = User.objects.create_user(
                    username=username,
                    email=invitation.email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=invitation.role
                )

            # Create membership
            CompanyMembership.objects.get_or_create(
                company=company,
                user=user,
                defaults={'role': invitation.role}
            )

            # Mark accepted
            invitation.is_accepted = True
            invitation.save()

            # Login and redirect
            login(request, user)
            messages.success(request, f"Welcome to {company.name}!")
            return redirect('dashboard')

    return render(request, 'accounts/accept_invite.html', {
        'invitation': invitation,
        'company': company
    })



@login_required
@company_admin_required
def merge_users_view(request):
    # Only Admins can access user merging
    company = request.current_company

    if request.method == 'POST':
        source_id = request.POST.get('source_user_id')
        target_id = request.POST.get('target_user_id')

        if source_id == target_id:
            messages.error(request, "Source and target users must be different.")
            return redirect('merge_users')

        source_user = get_object_or_404(User, id=source_id, is_active=True)
        target_user = get_object_or_404(User, id=target_id, is_active=True)

        try:
            merge_users(source_user, target_user)
            messages.success(request, f"Successfully merged account {source_user.email} into {target_user.email}!")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error merging users: {str(e)}")

    # Get list of all active users
    users = User.objects.filter(is_active=True)
    return render(request, 'accounts/merge_users.html', {
        'users': users
    })




@login_required
def notifications_view(request):

    notifications = request.user.notifications.all()

    notifications.update(
        is_read=True
    )

    return render(
        request,
        'accounts/notifications.html',
        {
            'notifications': notifications
        }
    )

@login_required

def company_setup(request):

    if CompanyMembership.objects.filter(user=request.user).exists():
        return redirect("dashboard")

    return render(
        request,
        "accounts/company_setup.html"
    )


@login_required
@company_required
def join_company(request):

    messages.info(
        request,
        "Use the invitation link sent by your administrator."
    )

    return render(
        request,
        "accounts/join_company.html"
    )



@login_required
def create_company(request):

    # Prevent users from creating multiple companies
    if (
        not request.user.is_superuser
        and CompanyMembership.objects.filter(
            user=request.user
        ).exists()
    ):
        messages.info(
            request,
            "You already belong to a company."
        )
        return redirect("dashboard")

    if request.method == "POST":

        company_name = request.POST.get("name")

        if not company_name:

            messages.error(
                request,
                "Company name is required."
            )

            return redirect("create_company")

        company = Company.objects.create(

            name=company_name

        )

        # Create membership

        CompanyMembership.objects.create(

            company=company,

            user=request.user,

            role=User.ROLE_ADMIN

        )

        # Make user admin

        membership = CompanyMembership.objects.get(
            company=company,
            user=request.user
        )

        membership.role = User.ROLE_ADMIN
        membership.save()
        messages.success(

            request,

            "Company created successfully."

        )

        return redirect("dashboard")

    return render(

        request,

        "accounts/create_company.html"

    )



@login_required
def group_workspace(request, group_id):

    group = get_object_or_404(
        Group.objects.select_related(
            "company",
            "project",
        ),
        id=group_id,
    )

    # -----------------------------------------
    # PLATFORM SUPERUSER
    # -----------------------------------------

    if request.user.is_superuser:

        has_access = True

    else:

        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                company=group.company,
            )
            .first()
        )

        # -----------------------------------------
        # User does not belong to this company
        # -----------------------------------------

        if membership is None:

            messages.error(
                request,
                "You are not a member of this company."
            )

            return redirect("dashboard")

        # -----------------------------------------
        # Company Admin
        # -----------------------------------------

        if membership.role == User.ROLE_ADMIN:

            has_access = True

        # -----------------------------------------
        # Normal User
        # -----------------------------------------

        else:

            has_access = group.members.filter(
                id=request.user.id
            ).exists()

    # -----------------------------------------
    # Permission Denied
    # -----------------------------------------

    if not has_access:

        messages.error(
            request,
            "You don't have permission to access this group."
        )

        return redirect("dashboard")

    # -----------------------------------------
    # Send Message
    # -----------------------------------------

    if request.method == "POST":

        text = request.POST.get(
            "message",
            ""
        ).strip()

        if text:

            GroupMessage.objects.create(

                group=group,

                project=group.project,

                sender=request.user,

                message=text,

            )

            create_audit_log(

                request,

                module="Group",

                action="MESSAGE",

                description=(
                    f"Sent message in group "
                    f"'{group.name}'"
                ),

            )

        return redirect(
            "group_workspace",
            group.id,
        )

    # -----------------------------------------
    # Load Messages
    # -----------------------------------------

    group_messages = (
        GroupMessage.objects
        .filter(group=group)
        .select_related("sender")
        .order_by("created_at")
    )

    return render(

        request,

        "accounts/group_workspace.html",

        {

            "group": group,

            "messages": group_messages,

        },

    )