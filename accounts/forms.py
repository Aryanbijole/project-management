from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Company, CompanyMembership, Group


class LoginForm(AuthenticationForm):

    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Email"
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password"
        })
    )


class UserRegistrationForm(forms.ModelForm):

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control"
        })
    )

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
        ]

        widgets = {

            "first_name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "last_name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "username": forms.TextInput(attrs={
                "class": "form-control"
            }),

        }

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class CompanyForm(forms.ModelForm):

    class Meta:
        model = Company

        fields = [
            "name",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control"
            })
        }


class CompanyMembershipForm(forms.ModelForm):

    class Meta:
        model = CompanyMembership

        fields = [
            "user",
            "role",
        ]

        widgets = {

            "user": forms.Select(attrs={
                "class": "form-select"
            }),

            "role": forms.Select(attrs={
                "class": "form-select"
            }),
        }


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group

        fields = [
            "name",
            "members",
        ]

        widgets = {

            "name": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "members": forms.SelectMultiple(attrs={
                "class": "form-select"
            }),
        }