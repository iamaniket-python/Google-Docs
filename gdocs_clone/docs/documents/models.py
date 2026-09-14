from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DocumentShare(models.Model):
    VIEW = 'view'
    EDIT = 'edit'
    PERMISSION_CHOICES = [
        (VIEW, 'View Only'),
        (EDIT, 'Can Edit'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_documents')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default=VIEW)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('document', 'user')

    def __str__(self):
        return f"{self.document.title} shared with {self.user.username} ({self.permission})"


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    version_number = models.PositiveIntegerField()
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='edits')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"