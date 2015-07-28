import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class OpendataniPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)

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
