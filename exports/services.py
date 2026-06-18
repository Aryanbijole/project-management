import os
import json
import zipfile
import threading
from django.utils import timezone
from django.core.files.base import ContentFile
from django.conf import settings
from exports.models import DataExport
from projects.models import Project
from tasks.models import TodoList, TodoItem, TodoActivity
from communication.models import MessageBoardPost, Comment
from integrations.models import ExternalTool

def run_project_export_async(data_export_id):
    """
    Spawns a thread to process the export in the background.
    """
    thread = threading.Thread(target=process_project_export, args=(data_export_id,))
    thread.daemon = True
    thread.start()

def process_project_export(data_export_id):
    """
    Assembles project data, writes it to a JSON, and packages it into a ZIP file.
    """
    try:
        data_export = DataExport.objects.get(id=data_export_id)
        data_export.status = 'processing'
        data_export.save()

        project = data_export.project

        # 1. Compile project data
        export_data = {
            'project_info': {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'company': project.company.name,
                'created_by': project.created_by.email if project.created_by else None,
                'created_at': project.created_at.isoformat(),
                'members': [m.email for m in project.members.all()]
            },
            'tools': [
                {
                    'tool_key': tool.tool_key,
                    'name': tool.name,
                    'is_enabled': tool.is_enabled
                } for tool in project.tools.all()
            ],
            'todo_lists': [],
            'message_board_posts': [],
            'external_tools': []
        }

        # 2. Add Todo Lists and Todo Items
        todo_lists = TodoList.objects.filter(project=project)
        for tlist in todo_lists:
            list_data = {
                'id': tlist.id,
                'name': tlist.name,
                'created_at': tlist.created_at.isoformat(),
                'items': []
            }
            items = TodoItem.objects.filter(todo_list=tlist)
            for item in items:
                item_data = {
                    'id': item.id,
                    'title': item.title,
                    'description': item.description,
                    'is_completed': item.is_completed,
                    'created_by': item.created_by.email if item.created_by else None,
                    'assigned_to': item.assigned_to.email if item.assigned_to else None,
                    'due_date': item.due_date.isoformat() if item.due_date else None,
                    'created_at': item.created_at.isoformat(),
                    'history': [
                        {
                            'actor': act.actor.email if act.actor else 'System',
                            'activity_type': act.activity_type,
                            'description': act.description,
                            'created_at': act.created_at.isoformat()
                        } for act in item.activities.all()
                    ]
                }
                list_data['items'].append(item_data)
            export_data['todo_lists'].append(list_data)

        # 3. Add Message Board Posts and Comments
        posts = MessageBoardPost.objects.filter(project=project)
        for post in posts:
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author': post.author.email if post.author else None,
                'created_at': post.created_at.isoformat(),
                'comments': [
                    {
                        'author': comment.author.email if comment.author else None,
                        'content': comment.content,
                        'created_at': comment.created_at.isoformat()
                    } for comment in post.comments.all()
                ]
            }
            export_data['message_board_posts'].append(post_data)

        # 4. Add External Tools
        ext_tools = ExternalTool.objects.filter(project=project)
        for etool in ext_tools:
            export_data['external_tools'].append({
                'name': etool.name,
                'url': etool.url,
                'created_at': etool.created_at.isoformat()
            })

        # Convert to formatted JSON bytes
        json_bytes = json.dumps(export_data, indent=2).encode('utf-8')

        # 5. Create a ZIP file containing the JSON and potentially other files
        zip_filename = f"project_{project.id}_export_{int(timezone.now().timestamp())}.zip"
        
        # Create an in-memory or temp file to save the ZIP
        temp_dir = os.path.join(settings.BASE_DIR, 'tmp')
        os.makedirs(temp_dir, exist_ok=True)
        temp_zip_path = os.path.join(temp_dir, zip_filename)

        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the JSON data
            zip_file.writestr('project_data.json', json_bytes)
            # We can also add dummy/simulated uploaded documents or files if any exist
            zip_file.writestr('README.txt', f"Export package for Project: {project.name}.\nGenerated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Read zip back and save to FileField
        with open(temp_zip_path, 'rb') as f:
            data_export.export_file.save(zip_filename, ContentFile(f.read()))

        # Clean up temporary zip file
        try:
            os.remove(temp_zip_path)
        except OSError:
            pass

        data_export.status = 'completed'
        data_export.completed_at = timezone.now()
        data_export.save()

    except Exception as e:
        # If there's an error, mark export as failed
        try:
            data_export = DataExport.objects.get(id=data_export_id)
            data_export.status = 'failed'
            data_export.save()
        except Exception:
            pass
        # Log error in console/logs
        print(f"Export failed: {str(e)}")
