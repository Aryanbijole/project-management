from django.db import transaction
from django.db.models import Q
from accounts.models import User, CompanyMembership, Group
from projects.models import Project
from tasks.models import TodoItem

def merge_users(source_user, target_user):
    """
    Merges source_user into target_user according to SRS:
    Transferred:
      - Project access
      - Assignments
      - Subscriptions (if any)
      - Ownership-related information
    Not transferred:
      - Posted messages
      - Comments
      - Historical activity records
      - Previously created to-do items
    """
    if source_user == target_user:
        raise ValueError("Cannot merge a user into themselves.")

    with transaction.atomic():
        # 1. Transfer Company Access
        source_memberships = CompanyMembership.objects.filter(user=source_user)
        for membership in source_memberships:
            # Check if target already is a member in this company
            target_exists = CompanyMembership.objects.filter(
                company=membership.company, 
                user=target_user
            ).exists()
            if not target_exists:
                # Reassign membership to target
                membership.user = target_user
                membership.save()
            else:
                # Target is already a member, remove source membership to avoid duplicates
                membership.delete()

        # 2. Transfer Project Access (Many-to-Many on Project.members)
        projects_with_source = Project.objects.filter(members=source_user)
        for project in projects_with_source:
            project.members.add(target_user)
            project.members.remove(source_user)

        # 3. Transfer Group Memberships (Many-to-Many on Group.members)
        groups_with_source = Group.objects.filter(members=source_user)
        for group in groups_with_source:
            group.members.add(target_user)
            group.members.remove(source_user)

        # 4. Transfer Assignments (TodoItem.assigned_to)
        TodoItem.objects.filter(assigned_to=source_user).update(assigned_to=target_user)

        # 5. Transfer Ownership-related information (Project.created_by)
        Project.objects.filter(created_by=source_user).update(created_by=target_user)

        # 6. Deactivate source user and link them to target
        source_user.is_merged = True
        source_user.merged_into = target_user
        source_user.is_active = False
        source_user.save()

    return target_user
