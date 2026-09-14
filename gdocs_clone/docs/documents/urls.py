from django.urls import path
from .views import (
    DocumentListCreateView, DocumentDetailView, DocumentShareView,
    DocumentVersionListView, DocumentVersionRestoreView
)
from .views import DocumentListCreateView, DocumentDetailView, DocumentShareView

urlpatterns = [
    path('', DocumentListCreateView.as_view(), name='document-list-create'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<int:pk>/share/', DocumentShareView.as_view(), name='document-share'),
    path('<int:pk>/versions/', DocumentVersionListView.as_view(), name='document-versions'),
    path('<int:pk>/versions/<int:version_id>/restore/', DocumentVersionRestoreView.as_view(), name='document-version-restore'),
]