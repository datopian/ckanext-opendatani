import ckan.lib.base as base
from ckan import model
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer

import ckan.plugins.toolkit as toolkit
from ckan.controllers.user import UserController as CoreUserController


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
