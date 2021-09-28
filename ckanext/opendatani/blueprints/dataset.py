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


log = logging.getLogger(__name__)

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
ValidationError = logic.ValidationError

dataset_blueprint = Blueprint('odni_dataset', __name__, url_prefix=u'/dataset')


def resource_read(id, resource_id):
    context = {'model': model, 'session': model.Session,
                'user': c.user,
                'auth_user_obj': c.userobj,
                'for_view': True}

    try:
        c.package = get_action('package_show')(context, {'id': id})
    except (NotFound, NotAuthorized):
        abort(404, _('Dataset not found'))

    for resource in c.package.get('resources', []):
        if resource['id'] == resource_id:
            c.resource = resource
            break
    if not c.resource:
        abort(404, _('Resource not found'))

    # required for nav menu
    c.pkg = context['package']
    c.pkg_dict = c.package
    dataset_type = c.pkg.type or 'dataset'

    # get package license info
    license_id = c.package.get('license_id')
    try:
        c.package['isopen'] = model.Package.\
            get_license_register()[license_id].isopen()
    except KeyError:
        c.package['isopen'] = False

    # TODO: find a nicer way of doing this
    c.datastore_api = '%s/api/action' % \
        config.get('ckan.site_url', '').rstrip('/')

    # c.resource['can_be_previewed'] = self._resource_preview(
    #     {'resource': c.resource, 'package': c.package})

    resource_views = get_action('resource_view_list')(
        context, {'id': resource_id})
    c.resource['has_views'] = len(resource_views) > 0

    current_resource_view = None
    view_id = request.GET.get('view_id')
    if c.resource['can_be_previewed'] and not view_id:
        current_resource_view = None
    elif c.resource['has_views']:
        if view_id:
            current_resource_view = [rv for rv in resource_views
                                        if rv['id'] == view_id]
            if len(current_resource_view) == 1:
                current_resource_view = current_resource_view[0]
            else:
                abort(404, _('Resource view not found'))
        else:
            current_resource_view = resource_views[0]

    vars = {'resource_views': resource_views,
            'current_resource_view': current_resource_view,
            'dataset_type': dataset_type}
    print(MAX_FILE_SIZE)
    if c.resource['url_type'] != 'upload':
        try:
            r = requests.head(c.resource['url'])
            if r.status_code not in (400, 403, 405) and r.ok:
                size = r.headers.get('content-length')
                if size and int(size) > MAX_FILE_SIZE:
                    h.flash_error('Sorry, this file is too large to be able to display in the browser, please download the data resource to examine it further.')
        except Exception as e:
            print(e)
            h.flash_error('Unable to get resource')
    template = _get_pkg_template(dataset_type)
    return render(template, extra_vars=vars)


dataset_blueprint.add_url_rule(
    rule='/{id}/resource/{resource_id}',
    view_func=resource_read,
    methods=[u'GET', u'POST'],
)