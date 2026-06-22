from django.contrib import admin
from .models import (
    User,
    Company,
    CompanyMembership,
    Group,
    Invitation
)

admin.site.register(User)
admin.site.register(Company)
admin.site.register(CompanyMembership)
admin.site.register(Group)
admin.site.register(Invitation)
# Register your models here.
