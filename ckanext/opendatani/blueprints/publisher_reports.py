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

publisher_blueprint = Blueprint('odni_publisher', __name__, url_prefix=u'/publisher-reports')


def prepare_report(org):
    """
    Creates a CSV publisher report and returns it as a string
    :param org: organization
    :type org: string
    :return: a CSV string
    :rtype: string
    """

    try:
        data_dict = {'org_name': org}

        if org == '@complete':
            data_dict = {}
            # Use 'complete' in the file name for full reports
            org = org[1:]
        else:
            # Use 'org-' in the file name for per org reports
            org = 'org-' + org

        resource = toolkit.get_action(
            'report_resources_by_organization')({}, data_dict)

        # We need this in case no datasets exist for the given organization
        # or the organization doesn't exist
        if not resource:
            toolkit.abort(404, _('Either the organization does not exist, \
                                    or it has no datasets.'))

        csvout = StringIO()
        csvwriter = csv.writer(
            csvout,
            dialect='excel',
            quoting=csv.QUOTE_NONNUMERIC
        )

        fields = resource[0].keys()
        csvwriter.writerow(fields)

        for data in resource:
            # We need to encode here due to unicode errors
            csvwriter.writerow(
                [unicode(d).encode('utf-8') for d in data.values()])

        csvout.seek(0)
        filename = 'publisher-report-{0}-{1}.csv'.format(org,
                                                            dt.date.today())
        toolkit.response.headers['Content-Type'] = 'application/csv'
        toolkit.response.headers['Content-Disposition'] = \
            'attachment; filename={0}'.format(filename)

        return csvout.read()

    except Exception as ex:
        error = 'Preparing the CSV report failed. Error: {0}'.format(ex)
        log.error(error)
        h.flash_error(error)
        raise


publisher_blueprint.add_url_rule(
    rule='/publisher-report-{org}.csv',
    view_func=prepare_report,
    methods=[u'GET', u'POST'],
)