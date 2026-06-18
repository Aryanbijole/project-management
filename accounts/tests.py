from django.test import TestCase
from django.conf import settings
from accounts.models import User, Company, Group, CompanyMembership
from projects.models import Project, ProjectTool
from tasks.models import TodoList, TodoItem, TodoActivity
from communication.models import MessageBoardPost, Comment
from accounts.services import merge_users

class UserMergeTestCase(TestCase):
    def setUp(self):
        # Create Users
        self.alice = User.objects.create_user(
            username='alice',
            email='alice@company.com',
            password='password123',
            first_name='Alice',
            last_name='Smith',
            role=User.ROLE_MEMBER
        )
        self.bob = User.objects.create_user(
            username='bob',
            email='bob@company.com',
            password='password123',
            first_name='Bob',
            last_name='Jones',
            role=User.ROLE_MEMBER
        )

        # Create Company & Memberships
        self.company = Company.objects.create(name='Acme Corp')
        CompanyMembership.objects.create(company=self.company, user=self.alice, role=User.ROLE_MEMBER)
        CompanyMembership.objects.create(company=self.company, user=self.bob, role=User.ROLE_MEMBER)

        # Create Group
        self.group = Group.objects.create(name='Engineering', company=self.company)
        self.group.members.add(self.alice)

        # Create Project (Alice is creator and member)
        self.project = Project.objects.create(name='Project Alpha', company=self.company, created_by=self.alice)
        self.project.members.add(self.alice)

        # Create Todo & Tasks
        self.todo_list = TodoList.objects.create(project=self.project, name='Sprint 1')
        self.todo_item = TodoItem.objects.create(
            todo_list=self.todo_list,
            title='Setup server',
            created_by=self.alice,
            assigned_to=self.alice
        )

        # Create Post and Comment
        self.post = MessageBoardPost.objects.create(
            project=self.project,
            title='Welcome Post',
            content='Hello world!',
            author=self.alice
        )
        self.comment = Comment.objects.create(
            post=self.post,
            content='Nice message!',
            author=self.alice
        )

    def test_merge_users_reassigns_access_and_ownership(self):
        # Verify initial states
        self.assertTrue(self.alice.is_active)
        self.assertTrue(self.project.members.filter(id=self.alice.id).exists())
        self.assertFalse(self.project.members.filter(id=self.bob.id).exists())
        self.assertEqual(self.project.created_by, self.alice)
        self.assertEqual(self.todo_item.assigned_to, self.alice)
        
        # Perform merge
        merge_users(self.alice, self.bob)
        
        # Refresh from database
        self.alice.refresh_from_db()
        self.bob.refresh_from_db()
        self.project.refresh_from_db()
        self.todo_item.refresh_from_db()
        self.post.refresh_from_db()
        self.comment.refresh_from_db()

        # 1. Source user is deactivated
        self.assertFalse(self.alice.is_active)
        self.assertTrue(self.alice.is_merged)
        self.assertEqual(self.alice.merged_into, self.bob)

        # 2. Access transferred
        self.assertFalse(self.project.members.filter(id=self.alice.id).exists())
        self.assertTrue(self.project.members.filter(id=self.bob.id).exists())
        self.assertTrue(self.group.members.filter(id=self.bob.id).exists())
        self.assertFalse(self.group.members.filter(id=self.alice.id).exists())

        # 3. Ownership transferred
        self.assertEqual(self.project.created_by, self.bob)

        # 4. Assignments transferred
        self.assertEqual(self.todo_item.assigned_to, self.bob)

        # 5. Not transferred items (remains associated with source user)
        self.assertEqual(self.todo_item.created_by, self.alice)
        self.assertEqual(self.post.author, self.alice)
        self.assertEqual(self.comment.author, self.alice)


class ProjectToolRenameTestCase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Acme Corp')
        
    def test_tool_names_only_affect_local_project(self):
        # Create Project A
        project_a = Project.objects.create(name='Project A', company=self.company)
        
        # Verify A starts with default name for todo list tool
        todo_tool_a = project_a.tools.get(tool_key='todo')
        self.assertEqual(todo_tool_a.name, 'To-Do Lists')
        
        # Rename A's tool
        todo_tool_a.name = 'Card Tables'
        todo_tool_a.save()
        
        # Create Project B
        project_b = Project.objects.create(name='Project B', company=self.company)
        
        # Verify B starts with default name, and does not inherit Project A's custom tool name
        todo_tool_b = project_b.tools.get(tool_key='todo')
        self.assertEqual(todo_tool_b.name, 'To-Do Lists')
        
        # Verify A's tool name remains Card Tables
        todo_tool_a.refresh_from_db()
        self.assertEqual(todo_tool_a.name, 'Card Tables')


class TaskReassignmentTestCase(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(
            username='alice', email='alice@company.com', password='password123', first_name='Alice'
        )
        self.bob = User.objects.create_user(
            username='bob', email='bob@company.com', password='password123', first_name='Bob'
        )
        self.company = Company.objects.create(name='Acme Corp')
        self.project = Project.objects.create(name='Project Alpha', company=self.company)
        self.todo_list = TodoList.objects.create(project=self.project, name='Sprint 1')
        self.todo_item = TodoItem.objects.create(
            todo_list=self.todo_list,
            title='Setup server',
            created_by=self.alice,
            assigned_to=self.alice
        )

    def test_task_reassignment_updates_assignee_and_logs_history(self):
        # Perform reassignment
        self.todo_item.reassign(self.bob, actor=self.alice)
        
        self.todo_item.refresh_from_db()
        self.assertEqual(self.todo_item.assigned_to, self.bob)
        
        # Check history activity logged
        activities = TodoActivity.objects.filter(todo_item=self.todo_item, activity_type='reassigned')
        self.assertEqual(activities.count(), 1)
        self.assertIn("Reassigned from alice@company.com to bob@company.com by alice@company.com", activities.first().description)
