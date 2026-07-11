from django import forms
from .models import (
    TodoList,
    TodoItem,
    ChecklistItem,
    TaskComment,
    TaskAttachment,
    TimeEntry,
)
from accounts.models import User


class TodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ["name"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Todo List Name"
            })
        }


class TodoItemForm(forms.ModelForm):

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)

        if company:
            self.fields["assigned_to"].queryset = User.objects.filter(
                memberships__company=company
            ).distinct()

    class Meta:
        model = TodoItem

        fields = [
            "title",
            "description",
            "assigned_to",
            "priority",
            "status",
            "due_date",
            "estimated_hours",
            "is_recurring",
            "repeat_days",
        ]

        widgets = {

            "title": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

            "assigned_to": forms.Select(attrs={
                "class": "form-select"
            }),

            "priority": forms.Select(attrs={
                "class": "form-select"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "estimated_hours": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.25",
                "min": "0"
            }),

            "is_recurring": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

            "repeat_days": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1
            }),
        }


class ChecklistItemForm(forms.ModelForm):

    class Meta:
        model = ChecklistItem

        fields = [
            "title"
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Checklist item"
            })
        }


class TaskCommentForm(forms.ModelForm):

    class Meta:
        model = TaskComment

        fields = [
            "content"
        ]

        widgets = {
            "content": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Write a comment..."
            })
        }


class TaskAttachmentForm(forms.ModelForm):

    class Meta:
        model = TaskAttachment

        fields = [
            "file"
        ]

        widgets = {
            "file": forms.FileInput(attrs={
                "class": "form-control"
            })
        }


class TimeEntryForm(forms.ModelForm):

    class Meta:
        model = TimeEntry

        fields = [
            "hours",
            "note",
        ]

        widgets = {

            "hours": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.25",
                "min": "0"
            }),

            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
        }