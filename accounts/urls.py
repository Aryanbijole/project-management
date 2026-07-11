from django.urls import path
from accounts import views
from accounts import admin_views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('company/create/', views.create_company, name='create_company'),
    path('group/create/', views.create_group, name='create_group'),
    path('invite/send/', views.send_invite, name='send_invite'),
    path('invite/accept/<str:token>/', views.accept_invite, name='accept_invite'),
    path('users/merge/', views.merge_users_view, name='merge_users'),
    path(
    'notifications/',
    views.notifications_view,
    name='notifications'
    ),

    path(
    "company/setup/",
    views.company_setup,
    name="company_setup",
    ),


    path(
    "company/join/",
    views.join_company,
    name="join_company",
    ),

    path(
    "administration/users/",
    admin_views.admin_users,
    name="admin_users",
    ),

    path(
    "administration/organization-members/",
    admin_views.organization_members,
    name="organization_members",
    ),

    path(
    "administration/",
    admin_views.administration_dashboard,
    name="administration_dashboard",
    ),

    path(
    "administration/users/",
    views.admin_users,
    name="admin_users",
    ),

    
]
