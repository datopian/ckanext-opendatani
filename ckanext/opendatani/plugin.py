import datetime
# from pylons import config
from ckan.common import config
# import routes.mapper
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.navl.dictization_functions import Missing
from ckan.logic.schema import default_user_schema, default_update_user_schema
from ckan.logic.action.create import user_create as core_user_create
from ckan.logic.action.update import user_update as core_user_update
import ckan.lib.helpers as h
import datetime as dt
from ckanext.opendatani import helpers, blueprints
from collections import OrderedDict
import ckan.logic as logic


log = logging.getLogger(__name__)

_ = toolkit._


class OpendataniPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurable, inherit=True)
    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.ITemplateHelpers)
    # plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IBlueprint)


    def configure(self, config):
        toolkit.add_resource('assets', 'odni')

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'opendatani')
        toolkit.add_resource('assets', 'odni')

        # Set fixed config values for this extension
        config_['scheming.dataset_schemas'] = \
            'ckanext.opendatani:dataset_schema.json'
        config_['scheming.dataset_fallback'] = True

        # config_['licenses_group_url'] = '{0}/licenses.json'.format(
        #     config_['ckan.site_url'].rstrip('/'))

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
            'verify_datasets_exist': helpers.verify_datasets_exist,
            'is_admin': helpers.is_admin,
            'showcase_list': helpers.get_showcase_List
        }

    # IRoutes
    # def before_map(self, map):
    #     controller = 'ckanext.opendatani.controller:StaticController'
    #     with routes.mapper.SubMapper(map, controller=controller) as m:
    #         m.connect('privacy', '/privacy', action='privacy')
    #         m.connect('termsandconditions', '/terms-and-conditions',
    #                   action='termsandconditions')
    #         m.connect('cookies', '/cookies', action='cookies')
    #         m.connect('codeofconduct', '/code-of-conduct',
    #                   action='codeofconduct')
    #         m.connect('privacy_notice_reg', '/privacy_notice_reg', action='privacy_notice_reg')

    #     controller = 'ckanext.opendatani.controller:CustomUserController'
    #     with routes.mapper.SubMapper(map, controller=controller) as m:
    #         m.connect('/user/reset', action='request_reset')
    #         m.connect('dashboard_update_notifications', '/dashboard/update_notifications',
    #                   action='dashboard_update_notifications', ckan_icon='file')
    #         m.connect('add_groups', '/dashboard/update_notifications',
    #                   action='dashboard_update_notifications', ckan_icon='file')
    #         m.connect('/user/activity/{id}/{offset}', action='activity')
    #         m.connect('user_activity_stream', '/user/activity/{id}',
    #                   action='activity', ckan_icon='time')

    #     controller = 'ckanext.opendatani.controller:CustomPackageController'
    #     with routes.mapper.SubMapper(map, controller=controller) as m:
    #         m.connect('add_groups', '/organization/add_groups/{id}',
    #                   action='add_groups', ckan_icon='file')
    #         m.connect('/dataset/{id}/resource/{resource_id}',
    #                   action='resource_read')

    #     controller = 'ckanext.opendatani.controller:CustomReportController'
    #     with routes.mapper.SubMapper(map, controller=controller) as m:
    #         m.connect('/publisher-reports/publisher-report-{org}.csv',
    #                   action='prepare_report')

    #     return map

    # def after_map(self, map):
    #     return map

    # IBlueprints
    def get_blueprint(self):
        return [
            blueprints.dashboard_blueprint,
            blueprints.dataset_blueprint,
            blueprints.dashboard_blueprint,
            blueprints.organization_blueprint,
            blueprints.publisher_blueprint,
            blueprints.user_blueprint,
            blueprints.static_blueprint,
        ]

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
            'package_show': package_show,
            'package_search': package_search
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

    return core_user_update(context, data_dict)


@plugins.toolkit.chained_action   
@logic.side_effect_free
def package_show(up_func,context,data_dict): 
    result = up_func(context, data_dict)
    id = result.get('id')
    try:
        result['total_downloads'] = logic.get_action('package_stats')(context, {'package_id': id})
    except:
        log.error(f'package {id} stats not available')

    resources = result.get('resources')
    overall_stat = 0
    for i, resource in enumerate(resources):
        resource_id = resource.get('id')
        try:
            stats = logic.get_action('resource_stats')(context, {'resource_id': resource_id})
            result['resources'][i]['total_downloads'] = stats
            overall_stat += int(stats)
        except:
            log.error(f'resource {resource_id} not found')

    if "total_downloads" not in result:
        result['total_downloads'] = overall_stat
    return result


@plugins.toolkit.chained_action   
@logic.side_effect_free
def package_search(up_func,context,data_dict):
    search = up_func(context, data_dict)
    results = search.get('results')

    if len(results) > 0:
        for i, result in enumerate(results):
            id = result.get('id')
            log.info("HERE2 HERE1")
            log.info(id)
            stats = logic.get_action("package_show")(context, {'id': id})
            results[i]['total_downloads'] = stats['total_downloads']
    
    return search


@toolkit.side_effect_free
def report_resources_by_organization(context, data_dict):
    """
    Returns a list of OrderedDicts (one for each dataset in an organization)
    sorted by the last modified date, then creation date
    (if no modifications have been made yet).
    Each OrderedDict contains the following keys:
    dataset_name, dataset_url, resource_name, resource_url,
    dataset_organisation, dataset_organisation_url, resource_created,
    resource_last_modified, resource_view_count, resource_download_count
    :return: a sorted list of OrderedDicts
    :rtype: list
    """

    user = toolkit.c.user or context.get('name')
    org = data_dict.get('org_name') or context.get('org')
    report = []

    if not helpers.verify_datasets_exist(org):
        return report

    if 'org_name' in data_dict:
        del data_dict['org_name']

    if not helpers.is_admin(user, org):
        toolkit.abort(403, _('You are not authorized to access this \
                      report or the organization does not exist.'))

    data_dict['start'] = 0
    data_dict['include_private'] = True
    data_dict['rows'] = 1000

    if org:
        data_dict['q'] = 'organization:{0}'.format(org)

    results = toolkit.get_action('package_search')({}, data_dict)

    # We need this in the case that there are more
    # rows than the API hard limit of 1000
    def check_rows(results, data_dict, rows):
        for i in range(rows // 1000):
            data_dict['start'] += 1000
            results['results'] += \
                toolkit.get_action('package_search')({}, data_dict)['results']

        return results

    rows = results['count']

    if rows > 1000:
        results = check_rows(results, data_dict, rows)

    for item in results['results']:
        resources = item['resources']
        organization = item.get('organization')
        organization_name = None
        organization_url = None

        if organization:
            organization_name = organization.get('name')
            organization_url = (
                config.get('ckan.site_url') + '/organization/{0}'
                .format(organization_name))

        for resource in resources:

            # resource_view_count depends on tracking_summary, which
            # doesn't seem to be enabled. Once it's enabled,
            # resource_view_count will come from
            # resource.get('tracking_summary').get('total')
            # For now, there's a shortened version to avoid errors.

            # resource_download_count will also need to be looked into
            # when tracking_summary is enabled.

            is_external = False if config.get('ckan.site_url') in \
                resource.get('url') else True

            report.append(OrderedDict([
                ('dataset_name', item.get('title')),
                ('dataset_url', (
                    config.get('ckan.site_url') + '/dataset/{0}'
                    .format(item.get('name')))),
                ('resource_name', resource.get('name')),
                ('resource_url', resource.get('url')),
                ('dataset_organization', organization_name),
                ('dataset_organization_url', organization_url),
                ('resource_created', resource.get('created')),
                ('resource_last_modified', resource.get('last_modified')),
                ('resource_view_count', resource.get('tracking_summary', 0)),
                ('resource_download_count', resource.get('downloads', 0)),
                ('is_external', is_external)]))

    return sorted(report, key=lambda x: (x['resource_last_modified'],
                  x['resource_created']),
                  reverse=True)


# Custom schemas

def custom_create_user_schema(form_schema=False):

    schema = default_user_schema()

    schema['password'] = [custom_user_password_validator,
                          toolkit.get_validator('user_password_not_empty'),
                          toolkit.get_validator('ignore_missing'),
                          str]

    if form_schema:
        schema['password1'] = [toolkit.get_validator('user_both_passwords_entered'),
                               custom_user_password_validator,
                               toolkit.get_validator('user_passwords_match'),
                               str]
        schema['password2'] = [str]

    return schema


def custom_update_user_schema(form_schema=False):

    schema = default_update_user_schema()

    schema['password'] = [custom_user_password_validator,
                          toolkit.get_validator('user_password_not_empty'),
                          toolkit.get_validator('ignore_missing'),
                          str]

    if form_schema:
        schema['password'] = [toolkit.get_validator('ignore_missing')]
        schema['password1'] = [toolkit.get_validator('ignore_missing'),
                               custom_user_password_validator,
                               toolkit.get_validator('user_passwords_match'),
                               str]
        schema['password2'] = [toolkit.get_validator('ignore_missing'),
                               str]

    return schema


# Custom validators
WRONG_PASSWORD_MESSAGE = ('Your password must be 8 characters or longer, ' +
                          'and contain at least one capital letter and a ' +
                          'number')


def custom_user_password_validator(key, data, errors, context):
    value = data[key]

    if isinstance(value, Missing):
        pass
    elif not isinstance(value, str):
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

        if not isinstance(value, str):
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
    user = toolkit.get_action('user_show')(
        {}, {'id': toolkit.c.userobj.id, 'include_datasets': True})
    data = user['datasets']
    stale_datasets = blueprints._stale_datasets_for_user(data)
    return str(len(stale_datasets))


def group_list():
    group_list = toolkit.get_action('group_list')({}, {})
    return group_list


def package_list():
    package_list = toolkit.get_action('package_list')({}, {})
    return package_list
