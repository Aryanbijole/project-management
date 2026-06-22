from rest_framework.permissions import BasePermission


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