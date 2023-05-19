import requests
import logging
from pylons import config

from rdflib.namespace import Namespace

from ckan.plugins import toolkit
from ckanext.dcat.profiles import RDFProfile

log = logging.getLogger(__name__)


DCT = Namespace("http://purl.org/dc/terms/")


class NIArcGISProfile(RDFProfile):
    '''
    An RDF profile for the Northern Ireland ArcGIS harvester

    '''

    def parse_dataset(self, dataset_dict, dataset_ref):

        # TODO: if there is more than one source with different defaults,
        # modify accordingly
        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = 'OSNI Mapping Helpdesk'
        dataset_dict['contact_email'] = 'osniopendata@dfpni.gov.uk'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        # Ping the ArcGIS server so the processing of the files
        # starts
        identifier = None
        avoid = []

        if toolkit.asbool(
                config.get('ckanext.opendatani.harvest.ping_arcgis_urls')):

            for extra in dataset_dict.get('extras', []):
                if extra['key'] == 'identifier' and extra['value']:
                    identifier = extra['value']
            if identifier:
                query = toolkit.get_action('package_search')(
                    {}, {'q': 'guid:"{0}"'.format(identifier)})
                if query['count']:
                    current_dataset = query['results'][0]
                    for current_resource in current_dataset.get('resources',
                                                                []):
                        if ('requested' in current_resource and
                                toolkit.asbool(current_resource['requested'])):
                            avoid.append(current_resource['url'])

            for resource in dataset_dict.get('resources', []):
                if resource.get('format') == 'OGC WMS':
                    resource['format'] = 'WMS'

                resource['requested'] = False
                file_formats = ('geojson', 'kml', 'zip', 'csv')

                if resource['url'] in avoid:
                    resource['requested'] = True
                elif resource.get('format') is not None:
                    if resource.get('format').lower() in file_formats:
                        try:
                            requests.head(resource['url'])

                            resource['requested'] = True
                            log.debug(
                                'Requested resource to start the processing: {0}'
                                .format(resource['url']))
                        except Exception, e:
                            log.debug(
                                'Error requesting resource: {0}\n{1}'
                                .format(resource['url'], e))
                            pass

        return dataset_dict


class CausewayProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):

        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = 'Nial Mc Sorley'
        dataset_dict['contact_email'] = 'Nial.McSorley@causewaycoastandglens.gov.uk'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        # Ping the ArcGIS server so the processing of the files
        # starts
        identifier = None
        avoid = []

        if toolkit.asbool(
                config.get('ckanext.opendatani.harvest.ping_arcgis_urls')):

            for extra in dataset_dict.get('extras', []):
                if extra['key'] == 'identifier' and extra['value']:
                    identifier = extra['value']
            if identifier:
                query = toolkit.get_action('package_search')(
                    {}, {'q': 'guid:"{0}"'.format(identifier)})
                if query['count']:
                    current_dataset = query['results'][0]
                    for current_resource in current_dataset.get('resources',
                                                                []):
                        if ('requested' in current_resource and
                                toolkit.asbool(current_resource['requested'])):
                            avoid.append(current_resource['url'])

            for resource in dataset_dict.get('resources', []):
                if resource.get('format') == 'OGC WMS':
                    resource['format'] = 'WMS'
                if resource.get('format') == 'ZIP':
                    resource['format'] = 'SHP'

                resource['requested'] = False
                file_formats = ('geojson', 'kml', 'zip', 'csv')

                if resource['url'] in avoid:
                    resource['requested'] = True
                elif resource.get('format') is not None:
                    if resource['format'].lower() in file_formats:
                        try:
                            requests.head(resource['url'])

                            resource['requested'] = True
                            log.debug(
                                'Requested resource to start the processing: {0}'
                                .format(resource['url']))
                        except Exception, e:
                            log.debug(
                                'Error requesting resource: {0}\n{1}'
                                .format(resource['url'], e))
                            pass

        return dataset_dict


class MidulsterProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):

        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = 'Nicky Doris'
        dataset_dict['contact_email'] = 'Nicky.doris@midulstercouncil.org'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        # Ping the ArcGIS server so the processing of the files
        # starts
        identifier = None
        avoid = []

        if toolkit.asbool(
                config.get('ckanext.opendatani.harvest.ping_arcgis_urls')):

            for extra in dataset_dict.get('extras', []):
                if extra['key'] == 'identifier' and extra['value']:
                    identifier = extra['value']
            if identifier:
                query = toolkit.get_action('package_search')(
                    {}, {'q': 'guid:"{0}"'.format(identifier)})
                if query['count']:
                    current_dataset = query['results'][0]
                    for current_resource in current_dataset.get('resources',
                                                                []):
                        if ('requested' in current_resource and
                                toolkit.asbool(current_resource['requested'])):
                            avoid.append(current_resource['url'])

            for resource in dataset_dict.get('resources', []):
                if resource.get('format') == 'OGC WMS':
                    resource['format'] = 'WMS'
                if resource.get('format') == 'ZIP':
                    resource['format'] = 'SHP'

                resource['requested'] = False
                file_formats = ('geojson', 'kml', 'zip', 'csv')

                if resource['url'] in avoid:
                    resource['requested'] = True
                elif resource.get('format') is not None:
                    if resource['format'].lower() in file_formats:
                        try:
                            requests.head(resource['url'])

                            resource['requested'] = True
                            log.debug(
                                'Requested resource to start the processing: {0}'
                                .format(resource['url']))
                        except Exception, e:
                            log.debug(
                                'Error requesting resource: {0}\n{1}'
                                .format(resource['url'], e))
                            pass

        return dataset_dict

class EsriArcGISProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):

        # TODO: if there is more than one source with different defaults,
        # modify accordingly
        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = 'Product Management'
        dataset_dict['contact_email'] = 'mapping.helpdesk@finance-ni.gov.uk'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        # Ping the ArcGIS server so the processing of the files
        # starts
        identifier = None
        avoid = []

        if toolkit.asbool(
                config.get('ckanext.opendatani.harvest.ping_arcgis_urls')):

            for extra in dataset_dict.get('extras', []):
                if extra['key'] == 'identifier' and extra['value']:
                    identifier = extra['value']
            if identifier:
                query = toolkit.get_action('package_search')(
                    {}, {'q': 'guid:"{0}"'.format(identifier)})
                if query['count']:
                    current_dataset = query['results'][0]
                    for current_resource in current_dataset.get('resources',
                                                                []):
                        if ('requested' in current_resource and
                                toolkit.asbool(current_resource['requested'])):
                            avoid.append(current_resource['url'])

            for resource in dataset_dict.get('resources', []):
                if resource.get('format') == 'OGC WMS':
                    resource['format'] = 'WMS'

                resource['requested'] = False
                file_formats = ('geojson', 'kml', 'zip', 'csv')

                if resource['url'] in avoid:
                    resource['requested'] = True
                elif resource.get('format') is not None:
                    if resource['format'].lower() in file_formats:
                        try:
                            requests.head(resource['url'])

                            resource['requested'] = True
                            log.debug(
                                'Requested resource to start the processing: {0}'
                                .format(resource['url']))
                        except Exception, e:
                            log.debug(
                                'Error requesting resource: {0}\n{1}'
                                .format(resource['url'], e))
                            pass

        return dataset_dict

class DaeraCoreProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):

        # TODO: if there is more than one source with different defaults,
        # modify accordingly
        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = 'DAERA Open Data Enquiries'
        dataset_dict['contact_email'] = 'OpenDataEnquiries@daera-ni.gov.uk'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        # Ping the ArcGIS server so the processing of the files
        # starts
        identifier = None
        avoid = []

        if toolkit.asbool(
                config.get('ckanext.opendatani.harvest.ping_arcgis_urls')):

            for extra in dataset_dict.get('extras', []):
                if extra['key'] == 'identifier' and extra['value']:
                    identifier = extra['value']
            if identifier:
                query = toolkit.get_action('package_search')(
                    {}, {'q': 'guid:"{0}"'.format(identifier)})
                if query['count']:
                    current_dataset = query['results'][0]
                    for current_resource in current_dataset.get('resources',
                                                                []):
                        if ('requested' in current_resource and
                                toolkit.asbool(current_resource['requested'])):
                            avoid.append(current_resource['url'])

            for resource in dataset_dict.get('resources', []):
                if resource.get('format') == 'OGC WMS':
                    resource['format'] = 'WMS'

                resource['requested'] = False
                file_formats = ('geojson', 'kml', 'zip', 'csv')

                if resource['url'] in avoid:
                    resource['requested'] = True
                elif resource.get('format') is not None:
                    if resource['format'].lower() in file_formats:
                        try:
                            requests.head(resource['url'])

                            resource['requested'] = True
                            log.debug(
                                'Requested resource to start the processing: {0}'
                                .format(resource['url']))
                        except Exception, e:
                            log.debug(
                                'Error requesting resource: {0}\n{1}'
                                .format(resource['url'], e))
                            pass

        return dataset_dict

class NisraProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):

        # TODO: if there is more than one source with different defaults,
        # modify accordingly
        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = 'NISRA'
        dataset_dict['contact_name'] = "Christopher O'Neill"
        dataset_dict['contact_email'] = 'christopher.oneill@nisra.gov.uk'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        # Ping the ArcGIS server so the processing of the files
        # starts
        identifier = None
        avoid = []

        if toolkit.asbool(
                config.get('ckanext.opendatani.harvest.ping_arcgis_urls')):

            for extra in dataset_dict.get('extras', []):
                if extra['key'] == 'identifier' and extra['value']:
                    identifier = extra['value']
            if identifier:
                query = toolkit.get_action('package_search')(
                    {}, {'q': 'guid:"{0}"'.format(identifier)})
                if query['count']:
                    current_dataset = query['results'][0]
                    for current_resource in current_dataset.get('resources',
                                                                []):
                        if ('requested' in current_resource and
                                toolkit.asbool(current_resource['requested'])):
                            avoid.append(current_resource['url'])

            for resource in dataset_dict.get('resources', []):
                if resource.get('format') == 'OGC WMS':
                    resource['format'] = 'WMS'

                resource['requested'] = False
                file_formats = ('geojson', 'kml', 'zip', 'csv')

                if resource['url'] in avoid:
                    resource['requested'] = True
                elif resource.get('format') is not None:
                    if resource['format'].lower() in file_formats:
                        try:
                            requests.head(resource['url'])

                            resource['requested'] = True
                            log.debug(
                                'Requested resource to start the processing: {0}'
                                .format(resource['url']))
                        except Exception, e:
                            log.debug(
                                'Error requesting resource: {0}\n{1}'
                                .format(resource['url'], e))
                            pass

        return dataset_dict


def _remove_extra(key, dataset_dict):
        dataset_dict['extras'][:] = [e
                                     for e in dataset_dict['extras']
                                     if e['key'] != key]
