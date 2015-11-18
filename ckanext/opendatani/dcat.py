from rdflib.namespace import Namespace
from ckanext.dcat.profiles import RDFProfile

DCT = Namespace("http://purl.org/dc/terms/")


class NIArcGISProfile(RDFProfile):
    '''
    An RDF profile for the Northern Ireland ArcGIS harvester

    '''

    def parse_dataset(self, dataset_dict, dataset_ref):

        dataset_dict['frequency'] = 'notPlanned'
        dataset_dict['topic_category'] = 'location'
        dataset_dict['lineage'] = '-'
        dataset_dict['contact_name'] = '-'
        dataset_dict['contact_email'] = '-'
        dataset_dict['license_id'] = 'uk-ogl'

        contact_name = [e['value']
                        for e in dataset_dict.get('extras', [])
                        if e['key'] == 'contact_name' and e['value']]
        if contact_name:
            dataset_dict['contact_name'] = contact_name[0]
            dataset_dict['extras'][:] = [e
                                         for e in dataset_dict['extras']
                                         if e['key'] != 'contact_name']

        return dataset_dict
