import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','deadline_api.settings')
import django
django.setup()
from django.test import RequestFactory
from workspaces.models import Workspace
from artifacts.views import TagViewSet
# Ensure a workspace exists
ws, _ = Workspace.objects.get_or_create(name='Test WS', description='test', owner_uid='user123')
factory = RequestFactory()
view = TagViewSet.as_view({'post':'create'})
request = factory.post(f'/api/v1/workspaces/{ws.id}/artifacts/tags/', data={'name':'newtag'}, content_type='application/json')
class FakeUser:
    is_authenticated = True
    def __init__(self, uid):
        self.uid = uid
request.user = FakeUser('user123')
response = view(request, workspace_id=ws.id)
print('Status:', response.status_code)
try:
    print('Data:', response.data)
except Exception as e:
    print('No data; repr:', repr(response))
