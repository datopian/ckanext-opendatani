from routes import url_for

from ckan.tests import helpers, factories


class TestUserList(helpers.FunctionalTestBase):

    @classmethod
    def teardown_class(cls):
        super(TestUserList, cls).teardown_class()
        helpers.reset_db()

    def test_not_logged_in(self):

        app = self._get_test_app()
        app.get(
            url=url_for(controller='user', action='index'),
            status=[302],
        )

    def test_normal_user(self):
        user = factories.User()

        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        app.get(
            url=url_for(controller='user', action='index'),
            extra_environ=env,
            status=[401],
        )

    def test_sysadmin(self):
        user = factories.Sysadmin()

        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        app.get(
            url=url_for(controller='user', action='index'),
            extra_environ=env,
        )
