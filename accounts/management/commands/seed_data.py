from django.core.management.base import BaseCommand
from django.utils.text import slugify
from accounts.models import User, Company, CompanyMembership, Group
from projects.models import Project
from tasks.models import TodoList, TodoItem, TodoActivity
from communication.models import MessageBoardPost, Comment

class Command(BaseCommand):
    help = 'Seeds the database with administrative and member data, projects, tasks, and message boards.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting database seeding..."))

        # 1. Create Admin User
        admin_email = "admin@company.com"
        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': 'admin',
                'first_name': 'Sarah',
                'last_name': 'Miller',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('password123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f"Created Admin: {admin_email} (password: password123)"))
        else:
            self.stdout.write(f"Admin already exists: {admin_email}")

        # 2. Create Member User
        member_email = "member@company.com"
        member, created = User.objects.get_or_create(
            email=member_email,
            defaults={
                'username': 'member',
                'first_name': 'David',
                'last_name': 'Wilson',
                'role': User.ROLE_MEMBER
            }
        )
        if created:
            member.set_password('password123')
            member.save()
            self.stdout.write(self.style.SUCCESS(f"Created Member: {member_email} (password: password123)"))
        else:
            self.stdout.write(f"Member already exists: {member_email}")

        # 3. Create Company
        company_name = "Acme Global Solutions"
        company, created = Company.objects.get_or_create(
            name=company_name,
            defaults={'slug': slugify(company_name)}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Company: {company_name}"))

        # 4. Create Memberships
        CompanyMembership.objects.get_or_create(
            company=company,
            user=admin,
            defaults={'role': User.ROLE_ADMIN}
        )
        CompanyMembership.objects.get_or_create(
            company=company,
            user=member,
            defaults={'role': User.ROLE_MEMBER}
        )

        # 5. Create Group
        group, created = Group.objects.get_or_create(
            name="Engineering Team",
            company=company
        )
        if created:
            group.members.add(admin, member)
            self.stdout.write(self.style.SUCCESS("Created Group: Engineering Team"))

        # 6. Create Project
        project, created = Project.objects.get_or_create(
            name="Website Redesign 2026",
            company=company,
            defaults={
                'description': 'Overhauling the company marketing portal, customer dashboard, and styling to match the new branding guidelines.',
                'created_by': admin
            }
        )
        if created:
            project.members.add(admin, member)
            self.stdout.write(self.style.SUCCESS("Created Project: Website Redesign 2026"))

            # 7. Create Todo List & Tasks
            todo_list = TodoList.objects.create(project=project, name="Phase 1: Foundation & Setup")
            self.stdout.write(self.style.SUCCESS("Created Todo List: Phase 1: Foundation & Setup"))

            task1 = TodoItem.objects.create(
                todo_list=todo_list,
                title="Design mockups for customer dashboard",
                description="Create Figma mockups demonstrating glassmorphism aesthetics and light/dark theme schemes.",
                assigned_to=member,
                created_by=admin
            )
            TodoActivity.objects.create(
                todo_item=task1,
                actor=admin,
                activity_type='created',
                description=f"Created task by {admin_email}."
            )

            task2 = TodoItem.objects.create(
                todo_list=todo_list,
                title="Implement Django user authentication",
                description="Configure custom User models with email-based login, role permissions, and user invitation controllers.",
                assigned_to=admin,
                created_by=admin
            )
            TodoActivity.objects.create(
                todo_item=task2,
                actor=admin,
                activity_type='created',
                description=f"Created task by {admin_email}."
            )
            self.stdout.write(self.style.SUCCESS("Added task items and activities."))

            # 8. Create Message Board Post
            post_content = """# Kickoff Meeting Notes

Welcome to the **Website Redesign 2026** workspace! We are officially booting up this project today. Below is a summary of our objectives:

* Introduce dynamic visual aesthetics (glassmorphism details, CSS theme switcher)
* Ensure highly responsive user interfaces on web and mobile devices
* Build secure, performant task reassignments and data backup export endpoints

## Development Architecture

We will implement this project using the following tech stack:

```python
# settings.py configuration details
INSTALLED_APPS = [
    'django.contrib.auth',
    'accounts',
    'projects',
    'tasks',
    'communication',
]
```

Please review the tasks on the Board and pick your assignments! Let's do this!
"""
            post = MessageBoardPost.objects.create(
                project=project,
                title="Project Kickoff Guidelines",
                content=post_content,
                author=admin
            )
            self.stdout.write(self.style.SUCCESS("Published Kickoff Message Board Post."))

            Comment.objects.create(
                post=post,
                content="Looking forward to this project! I have started working on the Figma mockups and will post them here soon.",
                author=member
            )
            self.stdout.write(self.style.SUCCESS("Added member comment to Kickoff post."))

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully! Ready for launch."))
