import ckan.lib.base as base
from ckan.views.dataset import (
    _get_pkg_template, _get_package_type, _setup_template_variables
)
from ckan.views.user import _extra_template_variables

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


log = logging.getLogger(__name__)

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
ValidationError = logic.ValidationError

dashboard_blueprint = Blueprint('odni_dashboard', __name__, url_prefix=u'/dashboard')

def _stale_datasets_for_user(data):
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

def dashboard_update_notifications():
    user = toolkit.get_action('user_show')(
        {}, {'id': toolkit.c.userobj.id, 'include_datasets': True})
    data = user['datasets']
    c.stale_datasets = _stale_datasets_for_user(data)
    context = {'for_view': True, 'user': c.user,
                'auth_user_obj': c.userobj}
    data_dict = {'user_obj': c.userobj, 'stale_datasets': c.stale_datasets}
    extra_vars = _extra_template_variables(context, data_dict)
    return toolkit.render('user/dashboard_update.html', extra_vars)


dashboard_blueprint.add_url_rule(
    rule='/update_notifications',
    view_func=dashboard_update_notifications,
    methods=[u'GET', u'POST'],
)