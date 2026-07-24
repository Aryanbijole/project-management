import cloudinary.uploader
from django.core.files.storage import Storage


class CloudinaryStorage(Storage):

    def _save(self, name, content):
        result = cloudinary.uploader.upload(
            content,
            public_id=name,
            overwrite=True,
            resource_type="auto",
        )
        return result["secure_url"]

    def exists(self, name):
        return False

    def url(self, name):
        return name