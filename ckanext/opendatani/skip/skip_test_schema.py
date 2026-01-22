import os

import httpretty

from nose.tools import assert_true, assert_raises, assert_false, assert_equals
from ckan.tests import helpers, factories


default_dataset = {
    'title': 'Test dataset',
    'notes': 'Some notes',
    'topic_category': ['farming', 'biota'],
    'tags': [{'name': 'tag 1'}, {'name': 'tag 2'}],
    'lineage': 'Info about lineage',
    'frequency': 'daily',
    'license_id': 'uk-ogl',
    'contact_name': 'Some Guy',
    'contact_email': 'guy@example.com',
    'private': True,
    'additional_info': 'Some additional info',
    'resources': [{
        'url': 'http://example.com/file.csv'
    }]
}


def _get_file_contents(file_name):
    path = os.path.join(os.path.dirname(__file__),
                        '..', file_name)
    with open(path, 'r') as f:
        return f.read()


class TestPrivateField(object):

    @classmethod
    def setup_class(cls):

        # Mock the licenses file
        licenses_file = _get_file_contents('public/licenses.json')
        httpretty.enable()
        httpretty.register_uri(httpretty.GET,
                               'http://test.ckan.net/licenses.json',
                               body=licenses_file)

    def setup(self):
        self.sysadmin = factories.Sysadmin()

        self.org_admin = factories.User()

        self.org = factories.Organization(
            users=[{'name': self.org_admin['name'], 'capacity': 'admin'}])

        default_dataset['owner_org'] = self.org['id']

    def teardown(self):
        helpers.reset_db()

    def test_default_behaviour(self):

        context = {'user': self.org_admin['name']}

        private_dataset = default_dataset.copy()
        private_dataset['name'] = 'private-dataset'

        helpers.call_action('package_create', context=context,
                            **private_dataset)

        dataset = helpers.call_action('package_show',
                                      id=private_dataset['name'])

        assert_true(dataset['private'])

        public_dataset = default_dataset.copy()
        public_dataset['name'] = 'public-dataset'
        public_dataset['private'] = False

        helpers.call_action('package_create', context=context,
                            **public_dataset)

        dataset = helpers.call_action('package_show',
                                      id=public_dataset['name'])

        assert_false(dataset['private'])

    @helpers.change_config('ckanext.opendatani.only_sysadmins_make_datasets_public', True)
    def test_restricted_behaviour_sysadmin(self):

        context = {'user': self.sysadmin['name']}

        private_dataset = default_dataset.copy()
        private_dataset['name'] = 'private-dataset'

        helpers.call_action('package_create', context=context,
                            **private_dataset)

        dataset = helpers.call_action('package_show',
                                      id=private_dataset['name'])

        assert_true(dataset['private'])

        public_dataset = default_dataset.copy()
        public_dataset['name'] = 'public-dataset'
        public_dataset['private'] = False

        helpers.call_action('package_create', context=context,
                            **public_dataset)

        dataset = helpers.call_action('package_show',
                                      id=public_dataset['name'])

        assert_false(dataset['private'])

    @helpers.change_config('ckanext.opendatani.only_sysadmins_make_datasets_public', True)
    def test_restricted_behaviour_org_admin(self):

        context = {'user': self.org_admin['name']}

        private_dataset = default_dataset.copy()
        private_dataset['name'] = 'private-dataset'

        helpers.call_action('package_create', context=context,
                            **private_dataset)

        dataset = helpers.call_action('package_show',
                                      id=private_dataset['name'])

        assert_true(dataset['private'])

        public_dataset = default_dataset.copy()
        public_dataset['name'] = 'public-dataset'
        public_dataset['private'] = False

        helpers.call_action('package_create', context=context,
                            **public_dataset)

        dataset = helpers.call_action('package_show',
                                      id=public_dataset['name'])

        assert_true(dataset['private'])
