from ckan.tests import factories


class Dataset(factories.Dataset):
    frequency = 'daily'
    contact_name = 'boita'
    license_id = 'Test'
    topic_category = 'farming'
    contact_email = 'Test'
    lineage = 'Test'
    notes = 'Test'
