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


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role', User.ROLE_MEMBER)

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
                role=role
            )
            # Log the user in
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')

    return render(request, 'accounts/register.html', {
        'roles': User.ROLE_CHOICES
    })


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


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


@login_required
def dashboard_view(request):
    # Get user companies as QuerySet
    companies = Company.objects.filter(memberships__user=request.user)

    # Projects user belongs to
    projects = Project.objects.filter(Q(members=request.user) | Q(created_by=request.user) | Q(company__in=companies)).distinct()

    # Groups in user's companies
    groups = Group.objects.filter(company__in=companies).distinct()

    # Users in same companies (for display / chat list / merges)
    company_users = User.objects.filter(
        memberships__company__in=companies, 
        is_active=True
    ).exclude(id=request.user.id).distinct()

    # Pending invites
    sent_invites = Invitation.objects.filter(invited_by=request.user)

    return render(request, 'accounts/dashboard.html', {
        'companies': companies,
        'projects': projects,
        'groups': groups,
        'company_users': company_users,
        'sent_invites': sent_invites,
        'roles': User.ROLE_CHOICES,
    })



@login_required
def create_company(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            company = Company.objects.create(name=name)
            # Create membership as ADMIN
            CompanyMembership.objects.create(
                company=company,
                user=request.user,
                role=User.ROLE_ADMIN
            )
            messages.success(request, f"Company '{name}' created successfully!")
        else:
            messages.error(request, "Company name cannot be empty.")
    return redirect('dashboard')


@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        company_id = request.POST.get('company_id')
        member_ids = request.POST.getlist('members')

        company = get_object_or_404(Company, id=company_id)
        
        # Check permissions: user must be admin in company
        membership = CompanyMembership.objects.filter(company=company, user=request.user).first()
        if not membership or membership.role != User.ROLE_ADMIN:
            messages.error(request, "You are not authorized to create groups for this company.")
            return redirect('dashboard')

        if name:
            group = Group.objects.create(name=name, company=company)
            if member_ids:
                users = User.objects.filter(id__in=member_ids)
                group.members.set(users)
            messages.success(request, f"Group '{name}' created successfully!")
        else:
            messages.error(request, "Group name cannot be empty.")
    return redirect('dashboard')


@login_required
def send_invite(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        company_id = request.POST.get('company_id')
        role = request.POST.get('role', User.ROLE_MEMBER)

        company = get_object_or_404(Company, id=company_id)
        
        # Verify inviter has permissions
        membership = CompanyMembership.objects.filter(company=company, user=request.user).first()
        if not membership or membership.role != User.ROLE_ADMIN:
            messages.error(request, "Only organization administrators can invite users.")
            return redirect('dashboard')

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
def merge_users_view(request):
    # Only Admins can access user merging
    if request.user.role != User.ROLE_ADMIN:
        messages.error(request, "Only system administrators can merge accounts.")
        return redirect('dashboard')

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
