"""Views for core models."""

from rest_framework import generics

from core.permissions import IsAdminUser

from .models import LabTerminal
from .serializers import LabTerminalSerializer


class LabTerminalListCreateView(generics.ListCreateAPIView):
    """
    List all lab terminals or create a new one.

    This view allows for the retrieval of a list of all lab terminals and the
    creation of new terminals. Access is restricted to admin users.
    """

    queryset = LabTerminal.objects.all().order_by("code")
    serializer_class = LabTerminalSerializer
    permission_classes = [IsAdminUser]


class LabTerminalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a lab terminal.

    This view provides endpoints for retrieving the details of a specific lab
    terminal, as well as updating or deleting it. Access is restricted to
    admin users.
    """

    queryset = LabTerminal.objects.all()
    serializer_class = LabTerminalSerializer
    permission_classes = [IsAdminUser]
