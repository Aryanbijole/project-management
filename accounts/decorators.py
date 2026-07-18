from functools import wraps
from django.shortcuts import redirect
from accounts.models import CompanyMembership


def company_required(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        # Global Superuser never requires a company
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Normal users must belong to a company
        if CompanyMembership.objects.filter(user=request.user).exists():
            return view_func(request, *args, **kwargs)

        return redirect("company_setup")

    return wrapper