from rest_framework import serializers
from .models import Document, DocumentShare,DocumentVersion
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

class DocumentSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'owner', 'version', 'created_at', 'updated_at']
        read_only_fields = ['version', 'created_at', 'updated_at']


class DocumentShareSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    shared_with = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = DocumentShare
        fields = ['id', 'username', 'shared_with', 'permission', 'shared_at']
        read_only_fields = ['shared_at']

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this username does not exist.")
        return value

class DocumentVersionSerializer(serializers.ModelSerializer):
    edited_by = serializers.ReadOnlyField(source='edited_by.username')

    class Meta:
        model = DocumentVersion
        fields = ['id', 'content', 'version_number', 'edited_by', 'created_at']


class DocumentVersionRestoreView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, version_id):
        document = Document.objects.filter(pk=pk).first()
        if not document:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        share = DocumentShare.objects.filter(document=document, user=user).first()
        can_edit = document.owner == user or (share and share.permission == DocumentShare.EDIT)

        if not can_edit:
            return Response({"detail": "You do not have edit access."}, status=status.HTTP_403_FORBIDDEN)

        version = DocumentVersion.objects.filter(pk=version_id, document=document).first()
        if not version:
            return Response({"detail": "Version not found."}, status=status.HTTP_404_NOT_FOUND)

        DocumentVersion.objects.create(
            document=document,
            content=document.content,
            version_number=document.version,
            edited_by=user
        )

        document.content = version.content
        document.version += 1
        document.save()

        return Response(DocumentSerializer(document).data, status=status.HTTP_200_OK)