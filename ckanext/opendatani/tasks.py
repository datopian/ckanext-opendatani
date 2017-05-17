import datetime as dt
import re
import json
import ckan.lib.helpers as h
from ckan.plugins import toolkit
import emailer
from ckan.lib.celery_app import celery
from ckan import model
import ckan.logic as l

import ConfigParser
import os


ckan_ini_filepath = os.environ.get('CKAN_CONFIG')
print ckan_ini_filepath

def load_config(ckan_ini_filepath):
    import paste.deploy
    config_abs_path = os.path.abspath(ckan_ini_filepath)
    conf = paste.deploy.appconfig('config:' + config_abs_path)
    import ckan
    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)

def frequency_to_timedelta(frequency):
    frequency_periods = {
        "daily": dt.timedelta(days=1),
        "weekly": dt.timedelta(days=7),
        "fortnightly": dt.timedelta(days=14),
        "monthly": dt.timedelta(days=30),
        "quarterly": dt.timedelta(days=91),
        "annually": dt.timedelta(days=365),
        # "irregular": "irregular",
        # "notPlanned": "notPlanned",
    }
    return frequency_periods[frequency]


@celery.task(name="opendatani.send_notification")
def send_notification(ckan_ini_filepath):
    load_config(ckan_ini_filepath)
    from ckan.common import config

    context = {
        'site_url': config.get('ckan.site_url'),
        'user': '',
        'apikey': '',
        'api_version': 3,
        'model': model,
        'session': model.Session,
    }

    print 'context: ', context

    data_dict = {}
    data = toolkit.get_action(
        'current_package_list_with_resources')(context, data_dict)

    print data


import uuid
from ckan.lib.celery_app import celery

celery.send_task("opendatani.send_notification", task_id=str(uuid.uuid4()), args=[ckan_ini_filepath,],)
