from rdflib.namespace import Namespace
from ckanext.dcat.profiles import RDFProfile

DCT = Namespace("http://purl.org/dc/terms/")


class NIArcGISProfile(RDFProfile):
    '''
    An RDF profile for the Northern Ireland ArcGIS harvester

    '''

    def parse_dataset(self, dataset_dict, dataset_ref):

        #TODO: if there is more than one source with different defaults,
        # modify accordingly
        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = 'OSNI Mapping Helpdesk'
        dataset_dict['contact_email'] = 'mapping.helpdesk@dfpni.gov.uk'
        dataset_dict['license_id'] = 'uk-ogl'

        _remove_extra('contact_name', dataset_dict)
        _remove_extra('contact_email', dataset_dict)

        return dataset_dict


def _remove_extra(key, dataset_dict):
        dataset_dict['extras'][:] = [e
                                     for e in dataset_dict['extras']
                                     if e['key'] != key]
