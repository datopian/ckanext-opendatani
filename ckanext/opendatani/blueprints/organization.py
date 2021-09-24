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
   
from flask import Blueprint


log = logging.getLogger(__name__)

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
ValidationError = logic.ValidationError

organization_blueprint = Blueprint('odni_organization', __name__, url_prefix=u'/organization')


def add_groups(id):
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


organization_blueprint.add_url_rule(
    rule='/add_groups/{id}',
    view_func=add_groups,
    methods=[u'GET', u'POST'],
)