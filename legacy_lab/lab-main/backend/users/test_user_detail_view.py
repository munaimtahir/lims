import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from users.views import UserDetailView

User = get_user_model()


@pytest.mark.django_db
def test_user_detail_view_get_uses_user_serializer():
    # create an admin and a normal user
    admin = User.objects.create_user(
        username="admin", password="adminpass", role="ADMIN"
    )
    target = User.objects.create_user(
        username="target", password="targetpass", role="RECEPTION"
    )

    factory = APIRequestFactory()
    request = factory.get(f"/api/users/{target.id}/")

    # authenticate as admin so permission check passes and GET path is used
    force_authenticate(request, user=admin)

    view = UserDetailView.as_view()
    response = view(request, pk=target.id)

    assert response.status_code == 200
    assert response.data["username"] == "target"
