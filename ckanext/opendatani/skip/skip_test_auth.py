import nose
from routes import url_for

from ckan.tests import helpers, factories
from ckan.plugins import toolkit

from ckanext.opendatani.plugin import WRONG_PASSWORD_MESSAGE

assert_raises = nose.tools.assert_raises
assert_equal = nose.tools.assert_equal

submit_and_follow = helpers.submit_and_follow
webtest_submit = helpers.webtest_submit


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


class TestPasswordValidator(object):

    @classmethod
    def setup_class(cls):
        helpers.reset_db()

    @classmethod
    def teardown_class(cls):
        helpers.reset_db()

    def test_ok(self):

        factories.User(
            password='8charsOneUpperCaseandanumber'
        )

    def test_length(self):

        assert_raises(toolkit.ValidationError,
                      factories.User, password='Short7')

    def test_upper_case(self):

        assert_raises(toolkit.ValidationError,
                      factories.User, password='loweronly6')

    def test_number(self):

        assert_raises(toolkit.ValidationError,
                      factories.User, password='Lettersonly')


class TestPasswordFunctional(helpers.FunctionalTestBase):

    @classmethod
    def setup_class(cls):
        super(cls, cls).setup_class()
        helpers.reset_db()

    @classmethod
    def teardown_class(cls):
        super(cls, cls).teardown_class()
        helpers.reset_db()

    def test_create_user_ok(self):
        app = self._get_test_app()
        env = {}

        response = app.get(
            url=url_for(controller='user', action='register'),
        )

        form = response.forms[1]
        form['name'] = 'new-name'
        form['fullname'] = 'new full name'
        form['email'] = 'new@example.com'
        form['password1'] = '8charsOneUpperCaseandanumber'
        form['password2'] = '8charsOneUpperCaseandanumber'

        response = submit_and_follow(app, form, env, 'save')

        assert WRONG_PASSWORD_MESSAGE not in response.body

        response = app.get('/user/logout')

    def test_create_user_short(self):
        app = self._get_test_app()
        env = {}

        response = app.get(
            url=url_for(controller='user', action='register'),
        )

        form = response.forms[1]
        form['name'] = 'new-name'
        form['fullname'] = 'new full name'
        form['email'] = 'new@example.com'
        form['password1'] = 'Short7'
        form['password2'] = 'Short7'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert WRONG_PASSWORD_MESSAGE in response.body

    def test_create_user_lower_only(self):
        app = self._get_test_app()
        env = {}

        response = app.get(
            url=url_for(controller='user', action='register'),
        )

        form = response.forms[1]
        form['name'] = 'new-name'
        form['fullname'] = 'new full name'
        form['email'] = 'new@example.com'
        form['password1'] = 'loweronly3'
        form['password2'] = 'loweronly3'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert WRONG_PASSWORD_MESSAGE in response.body

    def test_create_user_letters_only(self):
        app = self._get_test_app()
        env = {}

        response = app.get(
            url=url_for(controller='user', action='register'),
        )

        form = response.forms[1]
        form['name'] = 'new-name'
        form['fullname'] = 'new full name'
        form['email'] = 'new@example.com'
        form['password1'] = 'NoNumbers'
        form['password2'] = 'NoNumbers'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert WRONG_PASSWORD_MESSAGE in response.body

    def test_create_user_passwords_dont_match(self):
        app = self._get_test_app()
        env = {}

        response = app.get(
            url=url_for(controller='user', action='register'),
        )

        form = response.forms[1]
        form['name'] = 'new-name'
        form['fullname'] = 'new full name'
        form['email'] = 'new@example.com'
        form['password1'] = '8charsOneUpperCaseandanumber'
        form['password2'] = '8charsOneUpperCaseandanumber22'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert 'The passwords you entered do not match' in response.body

    def test_create_user_passwords_required(self):
        app = self._get_test_app()
        env = {}

        response = app.get(
            url=url_for(controller='user', action='register'),
        )

        form = response.forms[1]
        form['name'] = 'new-name'
        form['fullname'] = 'new full name'
        form['email'] = 'new@example.com'
        form['password1'] = ''
        form['password2'] = ''

        response = webtest_submit(form, extra_environ=env, name='save')

        assert 'Please enter both passwords' in response.body

    def test_edit_user_ok(self):
        password = '8charsOneUpperCaseandanumber'
        user = factories.User(password=password)
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']
        assert_equal(form['name'].value, user['name'])

        form['old_password'] = password
        form['password1'] = password + 'new'
        form['password2'] = password + 'new'

        response = submit_and_follow(app, form, env, 'save')

        assert WRONG_PASSWORD_MESSAGE not in response.body

    def test_edit_user_short(self):
        password = '8charsOneUpperCaseandanumber'
        user = factories.User(password=password)
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']
        assert_equal(form['name'].value, user['name'])

        form['old_password'] = password
        form['password1'] = 'Short7'
        form['password2'] = 'Short7'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert WRONG_PASSWORD_MESSAGE in response.body

    def test_edit_user_lower_only(self):
        password = '8charsOneUpperCaseandanumber'
        user = factories.User(password=password)
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']
        assert_equal(form['name'].value, user['name'])

        form['old_password'] = password
        form['password1'] = 'loweronly3'
        form['password2'] = 'loweronly3'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert WRONG_PASSWORD_MESSAGE in response.body

    def test_edit_user_letters_only(self):
        password = '8charsOneUpperCaseandanumber'
        user = factories.User(password=password)
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']
        assert_equal(form['name'].value, user['name'])

        form['old_password'] = password
        form['password1'] = 'NoNumbers'
        form['password2'] = 'NoNumbers'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert WRONG_PASSWORD_MESSAGE in response.body

    def test_edit_user_passwords_dont_match(self):
        password = '8charsOneUpperCaseandanumber'
        user = factories.User(password=password)
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']
        assert_equal(form['name'].value, user['name'])

        form['old_password'] = password
        form['password1'] = '8charsOneUpperCaseandanumber'
        form['password2'] = '8charsOneUpperCaseandanumber22'

        response = webtest_submit(form, extra_environ=env, name='save')

        assert 'The passwords you entered do not match' in response.body

    def test_edit_user_passwords_required(self):
        password = '8charsOneUpperCaseandanumber'
        user = factories.User(password=password)
        app = self._get_test_app()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        response = app.get(
            url=url_for(controller='user', action='edit'),
            extra_environ=env,
        )

        form = response.forms['user-edit-form']
        assert_equal(form['name'].value, user['name'])

        form['old_password'] = password
        form['password1'] = password
        form['password2'] = ''

        response = webtest_submit(form, extra_environ=env, name='save')

        assert 'The passwords you entered do not match' in response.body
