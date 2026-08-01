from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config

User = get_user_model()


class Command(BaseCommand):
    help = "Create superuser automatically if it doesn't exist"

    def handle(self, *args, **kwargs):

        username = config("DJANGO_SUPERUSER_USERNAME")
        email = config("DJANGO_SUPERUSER_EMAIL")
        password = config("DJANGO_SUPERUSER_PASSWORD")

        if not User.objects.filter(username=username).exists():

            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )

            self.stdout.write(
                self.style.SUCCESS("Superuser created successfully.")
            )

        else:
            self.stdout.write(
                self.style.WARNING("Superuser already exists.")
            )