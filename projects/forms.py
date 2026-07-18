from django import forms
from .models import Project
from accounts.models import  User
from .models import ProjectDocument


class ProjectForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        company = kwargs.pop("company", None)

        super().__init__(*args, **kwargs)

    # Company is assigned automatically
        self.fields.pop("company", None)

        if company:
            users = User.objects.filter(
                memberships__company=company
            ).distinct()

            self.fields["owner"].queryset = users
            self.fields["members"].queryset = users

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




class ProjectDocumentForm(forms.ModelForm):

    class Meta:
        model = ProjectDocument
        fields = [
            "title",
            "description",
            "file",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
            "file": forms.FileInput(attrs={
                "class": "form-control"
            }),
        }        