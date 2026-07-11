from rest_framework.permissions import BasePermission
from accounts.models import CompanyMembership, User



class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsMember(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'member'
        )


class IsClient(BasePermission):
        def has_permission(self, request, view):
            return (
                request.user.is_authenticated
                and request.user.role == 'client'
            )


class IsCollaborator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'collaborator'
        )

def is_company_admin(user):
    if not user.is_authenticated:
        return False

    membership = user.memberships.first()

    if membership is None:
        return False

    return membership.role == User.ROLE_ADMIN