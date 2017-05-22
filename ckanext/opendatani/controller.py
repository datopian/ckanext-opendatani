import ckan.lib.base as base
from ckan import model
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
from ckan.common import c

import ckan.plugins.toolkit as toolkit
from ckan.controllers.user import UserController as CoreUserController
import tasks


class StaticController(base.BaseController):

    def cookies(self):
        return base.render('static/cookies.html')

    def codeofconduct(self):
        return base.render('static/codeofconduct.html')

    def termsandconditions(self):
        return base.render('static/termsandconditions.html')

    def privacy(self):
        return base.render('static/privacy.html')


class CustomUserController(CoreUserController):
    def request_reset(self):
        context = {'model': model, 'session': model.Session,
                   'user': toolkit.c.user,
                   'auth_user_obj': toolkit.c.userobj}
        data_dict = {'id': toolkit.request.params.get('user')}
        try:
            toolkit.check_access('request_reset', context)
        except toolkit.NotAuthorized:
            toolkit.abort(401,
                          toolkit._('Unauthorized to request reset password.'))

        if toolkit.request.method == 'POST':
            id = toolkit.request.params.get('user')

            context = {'model': model,
                       'user': toolkit.c.user}

            data_dict = {'id': id}
            user_obj = None
            try:
                toolkit.get_action('user_show')(context, data_dict)
                user_obj = context['user_obj']
            except toolkit.ObjectNotFound:
                h.flash_error(toolkit._('No such user: %s') % id)

            if user_obj:
                try:
                    mailer.send_reset_link(user_obj)
                    h.flash_success(toolkit._('Please check your inbox for '
                                              'a reset code.'))
                    h.redirect_to('/')
                except mailer.MailerException, e:
                    h.flash_error(toolkit._('Could not send reset link: %s') %
                                  unicode(e))
        return toolkit.render('user/request_reset.html')

    def _stale_datasets_for_user(self, data):
        stale_datasets = []

        for pkg in data:
            pkg['metadata_created'] = h.date_str_to_datetime(
                pkg['metadata_created'])
            pkg['metadata_modified'] = h.date_str_to_datetime(
                pkg['metadata_modified'])

            diff = pkg['metadata_modified'] - pkg['metadata_created']

            if pkg['frequency'] and ('irregular' or 'notPlanned') not in pkg['frequency']:
                if diff > tasks.frequency_to_timedelta(pkg['frequency']):
                    stale_datasets.append(pkg)
        return stale_datasets

    def dashboard_update_notifications(self):
        data = toolkit.get_action(
            'current_package_list_with_resources')({}, {})

        data = [pkg for pkg in data if pkg['creator_user_id'] == c.userobj.id]
        c.stale_datasets = self._stale_datasets_for_user(data)

        context = {'for_view': True, 'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'user_obj': c.userobj, 'stale_datasets': c.stale_datasets}
        self._setup_template_variables(context, data_dict)
        return toolkit.render('user/dashboard_update.html')
