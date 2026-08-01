import cloudinary
import cloudinary.uploader

from django.core.files.storage import Storage


class CloudinaryStorage(Storage):

    def _save(self, name, content):
        content.seek(0)

        result = cloudinary.uploader.upload(
            content,
            folder="project-management",
            public_id=name,
            overwrite=True,
            resource_type="auto",
        )

        return result["public_id"]

    def exists(self, name):
        return False

    def url(self, name):
        return cloudinary.CloudinaryImage(name).build_url()

    def delete(self, name):
        cloudinary.uploader.destroy(name, invalidate=True)

    def size(self, name):
        return 0


from django.core.files.storage import Storage
import cloudinary.uploader


class CloudinaryStorage(Storage):

    def _save(self, name, content):
        result = cloudinary.uploader.upload(
            content,
            public_id=name,
            overwrite=True,
            resource_type="auto",
        )
        return result["secure_url"]

    def save(self, name, content, max_length=None):
        return self._save(name, content)

    def exists(self, name):
        return False

    def url(self, name):
        return name

    def open(self, name, mode="rb"):
        raise NotImplementedError("Cloudinary files are accessed by URL.")

    def size(self, name):
        return 0    

import os
import cloudinary.uploader
from django.core.files.storage import Storage


class CloudinaryStorage(Storage):

    def _save(self, name, content):
        # Convert Windows paths to Cloudinary paths
        name = name.replace("\\", "/")

        # Remove spaces if desired
        name = name.replace(" ", "_")

        result = cloudinary.uploader.upload(
            content,
            public_id=os.path.splitext(name)[0],   # remove extension
            resource_type="auto",
            overwrite=True,
        )

        return result["secure_url"]

    def exists(self, name):
        return False

    def url(self, name):
        return name    