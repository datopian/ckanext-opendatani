import ckan.lib.base as base
from ckan.views.dataset import (
    _get_pkg_template, _get_package_type, _setup_template_variables
)

import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
from ckanext.opendatani import helpers
import logging
import datetime as dt
import requests
import os
import csv
from io import StringIO

import ckan.lib.base as base
from ckan import model
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
from ckan.common import c
   
from flask import Blueprint

user_blueprint = Blueprint('odni_user', __name__, url_prefix=u'/user')


log = logging.getLogger(__name__)

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
ValidationError = logic.ValidationError



def request_reset():
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
            except mailer.MailerException as e:
                h.flash_error(toolkit._('Could not send reset link: %s') %
                                unicode(e))
    return toolkit.render('user/request_reset.html')


def activity(id, offset=0):
    '''Render this user's public activity stream page.'''

    context = {'model': model, 'session': model.Session,
                'user': c.user, 'auth_user_obj': c.userobj,
                'for_view': True}
    data_dict = {'id': id, 'user_obj': c.userobj,
                    'include_num_followers': True}
    try:
        toolkit.check_access('sysadmin', context, data_dict)
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    extra_vars = _setup_template_variables(context, data_dict)

    try:
        c.user_activity_stream = get_action('user_activity_list_html')(
            context, {'id': c.user_dict['id'], 'offset': offset})
    except ValidationError:
        base.abort(400)

    return render('user/activity_stream.html', extra_vars)

user_blueprint.add_url_rule(
    rule='/reset',
    view_func=request_reset,
    methods=[u'GET', u'POST'],
)

user_blueprint.add_url_rule(
    rule='/activity/{id}/{offset}',
    view_func=activity,
    methods=[u'GET', u'POST'],
)

user_blueprint.add_url_rule(
    rule='/activity/{id}',
    view_func=activity,
    methods=[u'GET', u'POST'],
)