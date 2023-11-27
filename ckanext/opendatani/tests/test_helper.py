import nose
from routes import url_for
import httpretty
import os

from ckan.tests import helpers, factories
from ckan.plugins import toolkit

from ckanext.opendatani import helpers as ni_helpers
from ckanext.opendatani.tests import factories as ni_factories


def _get_file_contents(file_name):
    path = os.path.join(os.path.dirname(__file__),
                        '..', file_name)
    with open(path, 'r') as f:
        return f.read()


class TestHelpers(helpers.FunctionalTestBase):

    @classmethod
    def setup_class(cls):
        # Mock the licenses file
        licenses_file = _get_file_contents('public/licenses.json')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET,
                               'http://test.ckan.net/licenses.json',
                               body=licenses_file)

    def setup(self):
        self.sysadmin = factories.Sysadmin(password='Password12345')
        self.org_admin = factories.User(password='Password12345')
        self.org = factories.Organization(users=[{'name': self.sysadmin['name'], 'capacity': 'admin'}])
        
        self.COMMON_ACTIVITY = {
            'user_id': self.org_admin['id'],
            'timestamp': '2019-03-07T11:38:10.801967',
            'is_new': True,
            'object_id': 'object-id',
            'revision_id': 'revision-id',
            'data': {
                'package': ni_factories.Dataset(owner_org=self.org['id'])
            },
            'id': 'activity-id',
            'activity_type': 'changed package'
        }


    def test_get_snippet_actor(self):
        user = factories.User()
        user_id = user.id
        COMMON_ACTIVITY['user_id'] = user_id
        result = ni_helpers.get_snippet_actor(COMMON_ACTIVITY, None)
        assert user['name'] == result
