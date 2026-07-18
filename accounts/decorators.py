from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from accounts.models import CompanyMembership, User


from functools import wraps
from django.shortcuts import redirect
from .models import CompanyMembership


def company_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        # Platform Admin
        if request.user.is_superuser:
            request.current_company = None
            return view_func(request, *args, **kwargs)

        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(user=request.user)
            .first()
        )

        if not membership:
            return redirect("company_setup")

        # Make company available everywhere
        request.current_company = membership.company
        request.current_membership = membership

        return view_func(request, *args, **kwargs)

    return wrapper

def platform_admin_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if not request.user.is_superuser:
            return HttpResponseForbidden(
                "Platform administrator access required."
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def company_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        # Platform Admin always allowed
        if request.user.is_superuser:
            request.current_company = None
            request.current_membership = None
            return view_func(request, *args, **kwargs)
        
        
        membership = (
            CompanyMembership.objects
            .select_related("company")
            .filter(
                user=request.user,
                role=User.ROLE_ADMIN
            )
            .first()
        )

        if membership:
            request.company = membership.company
            request.membership = membership
            return view_func(request, *args, **kwargs)

        return HttpResponseForbidden("Access denied.")

    return wrapper