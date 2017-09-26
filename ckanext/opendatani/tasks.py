import datetime as dt
import os
import uuid
from celery.task import periodic_task
from celery.schedules import crontab

from ckan.lib.celery_app import celery
import ckan.lib.helpers as h
from ckan.plugins import toolkit
import emailer
from ckan import model


ckan_ini_filepath = os.environ.get('CKAN_CONFIG')


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
    }
    if not frequency:
        pass
    else:
        return frequency_periods[frequency]


@periodic_task(run_every=(crontab(minute=0, hour=2)	), name="opendatani.send_notification", ignore_result=True)
def send_notification(ckan_ini_filepath):

    load_config(ckan_ini_filepath)
    from ckan.common import config

    context = {
        'site_url': config.get('ckan.site_url'),
        'user': 'ni_admin',
        'apikey': '5a53e818-d3d9-410c-b738-4952cf23b64f',
        'api_version': 3,
        'model': model,
        'session': model.Session,
    }
    if not context['site_url']:
        raise Exception('You have to set the "ckan.site_url" property in the '
                        'config file')
        return False
    if not context['user']:
        raise Exception('You have to set the "opendatani.admin_user.name" property '
                        'in the config file')
        return False
    if not context['apikey']:
        raise Exception('You have to set the "opendatani.admin_user.api_key" '
                        'property in the config file')
        return False

    data = toolkit.get_action(
        'current_package_list_with_resources')(context, {})

    for pkg in data:
        if 'frequency' in pkg:
            pkg['metadata_created'] = h.date_str_to_datetime(
                pkg['metadata_created'])
            pkg['metadata_modified'] = h.date_str_to_datetime(
                pkg['metadata_modified'])
            pkg['frequency'] = pkg.get('frequency', '')
            diff = pkg['metadata_modified'] - pkg['metadata_created']
            if pkg['frequency'] and ('irregular' or 'notPlanned') not in pkg['frequency']:
                if diff > frequency_to_timedelta(pkg['frequency']):
                    content = "Dataset " + pkg['name'] + " needs updating."
                    to = pkg['contact_email']
                    subject = "Update data notification"
                    emailer.send_email(content, to, subject)


celery.send_task("opendatani.send_notification", task_id=str(
    uuid.uuid4()), args=[ckan_ini_filepath, ],)
