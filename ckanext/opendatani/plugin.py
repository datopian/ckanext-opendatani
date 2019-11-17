import datetime
from pylons import config
import routes.mapper

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.dictization_functions import Missing
from ckan.logic.schema import default_user_schema, default_update_user_schema
from ckan.logic.action.create import user_create as core_user_create
from ckan.logic.action.update import user_update as core_user_update
import ckan.lib.helpers as h
import datetime as dt
from ckanext.opendatani.controller import CustomUserController
from ckanext.opendatani import helpers
from ckan.lib.base import abort

from collections import OrderedDict
import logging


_ = toolkit._


class OpendataniPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)



    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'opendatani')

        # Set fixed config values for this extension
        config_['scheming.dataset_schemas'] = \
            'ckanext.opendatani:dataset_schema.json'
        config_['scheming.dataset_fallback'] = True

        config_['licenses_group_url'] = '{0}/licenses.json'.format(
            config_['ckan.site_url'].rstrip('/'))

    # IValidators
    def get_validators(self):
        return {
            'at_least_n_choices': at_least_n_choices,
            'at_least_n_tags': at_least_n_tags,
            'opendatani_private_datasets': opendatani_private_datasets,
        }

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'create_all_datasets_private': create_all_datasets_private,
            'user_is_sysadmin': user_is_sysadmin,
            'user_registered_within_last_day': user_registered_within_last_day,
            'get_resource_count': get_resource_count,
            'get_user_num_stale_datasets': get_user_num_stale_datasets,
            'group_list': group_list,
            'package_list': package_list,
            'ni_activity_list_to_text': helpers.activity_list_to_text,
        }

    # IRoutes
    def before_map(self, map):
        controller = 'ckanext.opendatani.controller:StaticController'
        with routes.mapper.SubMapper(map, controller=controller) as m:
            m.connect('privacy', '/privacy', action='privacy')
            m.connect('termsandconditions', '/terms-and-conditions',
                      action='termsandconditions')
            m.connect('cookies', '/cookies', action='cookies')
            m.connect('codeofconduct', '/code-of-conduct',
                      action='codeofconduct')
            m.connect('privacy_notice_reg', '/privacy_notice_reg', action='privacy_notice_reg')

        controller = 'ckanext.opendatani.controller:CustomUserController'
        with routes.mapper.SubMapper(map, controller=controller) as m:
            m.connect('/user/reset', action='request_reset')
            m.connect('dashboard_update_notifications', '/dashboard/update_notifications',
                      action='dashboard_update_notifications', ckan_icon='file')
            m.connect('add_groups', '/dashboard/update_notifications',
                      action='dashboard_update_notifications', ckan_icon='file')
            m.connect('/user/activity/{id}/{offset}', action='activity')
            m.connect('user_activity_stream', '/user/activity/{id}',
                      action='activity', ckan_icon='time')

        controller = 'ckanext.opendatani.controller:CustomPackageController'
        with routes.mapper.SubMapper(map, controller=controller) as m:
            m.connect('add_groups', '/organization/add_groups/{id}',
                      action='add_groups', ckan_icon='file')
            m.connect('/dataset/{id}/resource/{resource_id}',
                      action='resource_read')
            m.connect('resource_report', '/resource_report/{org}', action='retrieve_report')

        return map

    def after_map(self, map):
        return map

    # IAuthFunctions
    def get_auth_functions(self):

        return {
            'user_list': custom_user_list_auth
        }

    # IActions
    def get_actions(self):

        return {
            'user_create': custom_user_create,
            'user_update': custom_user_update,
            'report_resources_by_organization': report_resources_by_organization,
        }


# Custom auth

@toolkit.auth_allow_anonymous_access
def custom_user_list_auth(context, data_dict):
    # Only sysadmins should be able to see the user list
    return {'success': False}


# Custom actions

def custom_user_create(context, data_dict):

    context['schema'] = custom_create_user_schema(
        form_schema='password1' in context.get('schema', {}))

    # If user is pending (is an invite), adhere to the password requirements,
    # as the random password created by CKAN core won't pass them
    if data_dict.get('state') == 'pending':
        data_dict['password'] = data_dict['password'].rjust(8, 'a') + 'A1'

    return core_user_create(context, data_dict)


def custom_user_update(context, data_dict):

    context['schema'] = custom_update_user_schema(
        form_schema='password1' in context.get('schema', {}))

    return core_user_update(context, data_dict)


@toolkit.side_effect_free
def report_resources_by_organization(context, data_dict):

    if not user_is_sysadmin():
        abort(403, _('You are not authorized to access this report'))

    data_dict['include_private'] = True

    #logging.warn(data_dict)

    results = toolkit.get_action('package_search')(context, data_dict)

    # For testing
    # results = json.loads(requests.get(
    # 'https://www.opendatani.gov.uk/api/3/action/package_search').content).get('result')
    # return results
    report = []

    if results.get('count') == 0:
        abort(404, _('There are no resources available to generate this report'))

    for item in results['results']:
        resources = item['resources']
        organization = item['organization']

        for resource in resources:

            # resource_view_count depends on tracking_summary, which
            # doesn't seem to be enabled. Once it's enabled,
            # resource_view_count will come from
            # resource.get('tracking_summary').get('total')
            # For now, there's a shortened version to avoid errors.

            # resource_download_count will also need to be looked into
            # when tracking_summary is enabled.

            report.append(OrderedDict([
                ('dataset_name', item.get('title')),
                ('dataset_url', (
                    'https://www.opendatani.gov.uk/dataset/{0}'
                    .format(item.get('name')))),
                ('resource_name', resource.get('name')),
                ('resource_url', resource.get('url')),
                ('dataset_organization', organization.get('name')),
                ('dataset_organization_url', (
                    'https://www.opendatani.gov.uk/organization/{0}'
                    .format(organization.get('name')))),
                ('resource_created', resource.get('created')),
                ('resource_last_modified', resource.get('last_modified')),
                ('resource_view_count', resource.get('tracking_summary', 0)),
                ('resource_download_count', resource.get('downloads', 0))]))

    resource_data = sorted(report, key=lambda x: x['resource_last_modified'], reverse=True)

    return resource_data


# Custom schemas

def custom_create_user_schema(form_schema=False):

    schema = default_user_schema()

    schema['password'] = [custom_user_password_validator,
                          toolkit.get_validator('user_password_not_empty'),
                          toolkit.get_validator('ignore_missing'),
                          unicode]

    if form_schema:
        schema['password1'] = [toolkit.get_validator('user_both_passwords_entered'),
                               custom_user_password_validator,
                               toolkit.get_validator('user_passwords_match'),
                               unicode]
        schema['password2'] = [unicode]

    return schema


def custom_update_user_schema(form_schema=False):

    schema = default_update_user_schema()

    schema['password'] = [custom_user_password_validator,
                          toolkit.get_validator('user_password_not_empty'),
                          toolkit.get_validator('ignore_missing'),
                          unicode]

    if form_schema:
        schema['password'] = [toolkit.get_validator('ignore_missing')]
        schema['password1'] = [toolkit.get_validator('ignore_missing'),
                               custom_user_password_validator,
                               toolkit.get_validator('user_passwords_match'),
                               unicode]
        schema['password2'] = [toolkit.get_validator('ignore_missing'),
                               unicode]

    return schema


# Custom validators
WRONG_PASSWORD_MESSAGE = ('Your password must be 8 characters or longer, ' +
                          'and contain at least one capital letter and a ' +
                          'number')


def custom_user_password_validator(key, data, errors, context):
    value = data[key]

    if isinstance(value, Missing):
        pass
    elif not isinstance(value, basestring):
        errors[('password',)].append(_('Passwords must be strings'))
    elif value == '':
        pass
    elif (len(value) < 8 or
          not any(x.isdigit() for x in value) or
          not any(x.isupper() for x in value)
          ):
        errors[('password',)].append(_(WRONG_PASSWORD_MESSAGE))


def at_least_n_tags(number_of_tags):

    def _callable(key, data, errors, context):
        value = data.get(key)
        _number_of_tags = int(number_of_tags)

        if not isinstance(value, basestring):
            return

        value = value.split(',')

        if len(value) < _number_of_tags:
            msg = (_('Enter at least 1 keyword') if _number_of_tags == 1 else
                   _('Enter at least {0} keywords'.format(_number_of_tags)))
            errors[key].append(msg)

    return _callable


def at_least_n_choices(number_of_choices):

    def _callable(key, data, errors, context):
        value = data.get(key)
        _number_of_choices = int(number_of_choices)

        if not isinstance(value, list):
            return

        if len(value) < _number_of_choices:
            msg = (_('Enter at least 1 choice') if _number_of_choices == 1 else
                   _('Enter at least {0} choices'.format(_number_of_choices)))
            errors[key].append(msg)

    return _callable


def opendatani_private_datasets(key, data, errors, context):

    if not create_all_datasets_private():
        return

    user_name = context.get('user')
    if user_name:
        user = toolkit.get_action('user_show')(
            {'ignore_auth': True}, {'id': user_name})

        if user['sysadmin']:
            return

    # Force all datasets to be private regardless of what the value is
    data[key] = True


# Custom helpers

def create_all_datasets_private():
    return toolkit.asbool(
        config.get('ckanext.opendatani.only_sysadmins_make_datasets_public',
                   False))


def user_is_sysadmin():
    if not toolkit.c.userobj:
        return False
    if toolkit.c.userobj.sysadmin:
        return True
    return False


def user_registered_within_last_day():
    '''Checks whether the user registered today'''
    if toolkit.c.userobj:
        return toolkit.c.userobj.created.date() == datetime.date.today()
    return False


def get_resource_count(resource_format, resources):
    ''' Returns resource count for given dataset.'''
    counter = 0
    for res in resources:
        if resource_format == res['format']:
            counter += 1
    return counter


def get_user_num_stale_datasets():
    """Get each user's inupdated datasets."""
    cuc = CustomUserController()
    user = toolkit.get_action('user_show')(
        {}, {'id': toolkit.c.userobj.id, 'include_datasets': True})
    data = user['datasets']
    stale_datasets = cuc._stale_datasets_for_user(data)
    return str(len(stale_datasets))


def group_list():
    group_list = toolkit.get_action('group_list')({}, {})
    return group_list


def package_list():
    package_list = toolkit.get_action('package_list')({}, {})
    return package_list
