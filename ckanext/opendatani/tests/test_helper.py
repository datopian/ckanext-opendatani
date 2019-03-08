import nose
from routes import url_for
import httpretty

from ckan.tests import helpers, factories
from ckan.plugins import toolkit

from ckanext.opendatani import helpers as ni_helpers
from ckanext.opendatani.tests import factories as ni_factories

class TestHelpers(helpers.FunctionalTestBase):

    COMMON_ACTIVITY = {
        'user_id': 'user',
        'timestamp': '2019-03-07T11:38:10.801967',
        'is_new': True,
        'object_id': 'object-id',
        'revision_id': 'revision-id',
        'data': {
            'package': ni_factories.Dataset()
        },
        'id': 'activity-id',
        'activity_type': 'changed package'
    }

    @classmethod
    def setup_class(cls):
        # Mock the licenses file
        licenses_file = _get_file_contents('public/licenses.json')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET,
                               'http://test.ckan.net/licenses.json',
                               body=licenses_file)

    @classmethod
    def teardown_class(cls):
        super(TestHelpers, cls).teardown_class()
        httpretty.disable()

    def setup(self):
        licenses_file = _get_file_contents('public/licenses.json')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET,
                               'http://test.ckan.net/licenses.json',
                               body=licenses_file)

    def teardown(self):
        httpretty.disable()
        helpers.reset_db()


    def test_get_snippet_actor(self):
        user = factories.User()
        user_id = user.id
        COMMON_ACTIVITY['user_id'] = user_id
        result = ni_helpers.get_snippet_actor(COMMON_ACTIVITY, None)
        assert user['name'] == result
