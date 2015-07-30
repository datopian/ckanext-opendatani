from pylons import config

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


_ = toolkit._


class OpendataniPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'opendatani')

        # Set fixed config values for this extension
        config_['scheming.dataset_schemas'] = 'ckanext.opendatani:dataset_schema.json'
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

    if not config.get('ckanext.opendatani.only_sysadmins_make_datasets_public',
                      False):
        return

    user_name = context.get('user')
    if user_name:
        user = toolkit.get_action('user_show')(
            {'ignore_auth': True}, {'id': user_name})

        if user['sysadmin']:
            return

    # Force all datasets to be private regardless of what the value is
    data[key] = True
