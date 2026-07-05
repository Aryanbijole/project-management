from django import forms
from .models import Project
from accounts.models import Company, User


class ProjectForm(forms.ModelForm):

    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Project

        fields = [
            "name",
            "description",
            "company",
            "owner",
            "members",
            "visibility",
            "status",
            "is_archived",
        ]

        widgets = {

            "name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

            "company": forms.Select(attrs={
                "class": "form-select"
            }),

            "owner": forms.Select(attrs={
                "class": "form-select"
            }),

            "visibility": forms.Select(attrs={
                "class": "form-select"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

            "is_archived": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

        }