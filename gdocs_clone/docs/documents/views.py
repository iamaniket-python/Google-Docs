from rest_framework import generics, permissions
from .models import Document, DocumentShare,DocumentVersion
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import status
from django.db.models import Q
from .serializers import DocumentSerializer, DocumentShareSerializer, DocumentVersionSerializer
from django.shortcuts import render

class DocumentPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True

        share = DocumentShare.objects.filter(document=obj, user=request.user).first()
        if not share:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return share.permission == DocumentShare.EDIT
class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Document.objects.filter(
            Q(owner=user) | Q(shares__user=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, DocumentPermission]
    queryset = Document.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        expected_version = request.data.get('expected_version')

        if expected_version is not None and int(expected_version) != instance.version:
            return Response(
                {
                    "detail": "Conflict: this document has been modified by someone else since you loaded it.",
                    "current_version": instance.version,
                    "current_content": instance.content,
                },
                status=status.HTTP_409_CONFLICT
            )

        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance

        DocumentVersion.objects.create(
            document=instance,
            content=instance.content,
            version_number=instance.version,
            edited_by=self.request.user
        )

        serializer.save(version=instance.version + 1)

class DocumentShareView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        if document.owner != request.user:
            return Response({"detail": "Only the owner can share this document."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DocumentShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user = User.objects.get(username=serializer.validated_data['username'])

        if target_user == request.user:
            return Response({"detail": "You cannot share a document with yourself."}, status=status.HTTP_400_BAD_REQUEST)

        share, created = DocumentShare.objects.update_or_create(
            document=document,
            user=target_user,
            defaults={'permission': serializer.validated_data['permission']}
        )

        result_serializer = DocumentShareSerializer(share)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DocumentVersionListView(generics.ListAPIView):
    serializer_class = DocumentVersionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        document_id = self.kwargs['pk']
        document = Document.objects.filter(pk=document_id).first()

        if not document:
            return DocumentVersion.objects.none()

        user = self.request.user
        has_access = document.owner == user or DocumentShare.objects.filter(document=document, user=user).exists()

        if not has_access:
            return DocumentVersion.objects.none()

        return DocumentVersion.objects.filter(document=document)


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


def login_page(request):
    return render(request, 'login.html')

def documents_page(request):
    return render(request, 'documents_list.html')

def document_editor_page(request, document_id):
    return render(request, 'document_editor.html')

def register_page(request):
    return render(request, 'register.html')