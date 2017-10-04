import ckan.lib.base as base
from ckan import model
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
from ckan.common import c, request, _

import ckan.plugins.toolkit as toolkit
from ckan.controllers.user import UserController as CoreUserController
from ckan.controllers.package import PackageController as CorePackageController

import logging
import ckan.logic as logic
import datetime as dt

log = logging.getLogger(__name__)

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action


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
        def frequency_to_timedelta(frequency):
            frequency_periods = {
                "daily": dt.timedelta(days=2),
                "weekly": dt.timedelta(days=7),
                "fortnightly": dt.timedelta(days=14),
                "monthly": dt.timedelta(days=30),
                "quarterly": dt.timedelta(days=91),
                "annually": dt.timedelta(days=365),
            }
            if not frequency:
                pass
            else:
                return frequency_periods[frequency]

        stale_datasets = []
        if data:
            for pkg in data:
                if 'frequency' in pkg:
                    pkg['metadata_created'] = h.date_str_to_datetime(
                        pkg['metadata_created'])
                    pkg['metadata_modified'] = h.date_str_to_datetime(
                        pkg['metadata_modified'])
                    pkg['frequency'] = pkg.get('frequency', '')
                    if pkg['frequency']:
                        if pkg['frequency'] != 'irregular' and pkg['frequency'] != 'notPlanned':
                            if pkg['metadata_modified'].date() != pkg['metadata_created'].date():
                                now = dt.datetime.now()
                                diff = now - pkg['metadata_modified']
                                if diff > frequency_to_timedelta(pkg['frequency']):
                                    stale_datasets.append(pkg)
        return stale_datasets

    def dashboard_update_notifications(self):
        user = toolkit.get_action('user_show')(
            {}, {'id': toolkit.c.userobj.id, 'include_datasets': True})
        data = user['datasets']
        c.stale_datasets = self._stale_datasets_for_user(data)
        context = {'for_view': True, 'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'user_obj': c.userobj, 'stale_datasets': c.stale_datasets}
        self._setup_template_variables(context, data_dict)
        return toolkit.render('user/dashboard_update.html')


class CustomPackageController(CorePackageController):
    def add_groups(self, id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        data_dict = {'id': id, 'all_fields': True}
        c.group_dict = toolkit.get_action(
            'organization_show')(context, data_dict)
        c.packages = toolkit.get_action(
            'current_package_list_with_resources')(context, data_dict)
        c.groups = toolkit.get_action('group_list')(context, data_dict)

        if request.method == 'POST':
            selected_groups = request.POST.getall('group')
            selected_datasets = request.POST.getall('dataset')
            for group in selected_groups:
                for pkg in selected_datasets:
                    data_dict = {"id": group,
                                 "object": pkg,
                                 "object_type": 'package',
                                 "capacity": 'public'}
                    try:
                        get_action('member_create')(context, data_dict)
                    except NotFound:
                        abort(404, _('Group not found'))
            controller = 'ckanext.opendatani.controller:CustomPackageController'
            url = h.url_for(controller=controller, action='add_groups', id=id)
            h.redirect_to(url)
        return toolkit.render('organization/add_groups.html')
