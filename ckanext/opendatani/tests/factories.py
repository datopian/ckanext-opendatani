from ckan.tests import factories


class Dataset(factories.Dataset):
    title = 'Test dataset'
    notes = 'Some notes'
    topic_category = ['farming', 'biota']
    tags = [{'name': 'tag 1'}, {'name': 'tag 2'}, {'name': 'tag 3'}]
    lineage = 'Info about lineage'
    frequency = 'daily'
    license_id = 'uk-ogl'
    contact_name = 'Some Guy'
    contact_email = 'guy@example.com'
    additional_info = 'Some additional info'
    resources = [{
        'url': 'http://example.com/file.csv'
    }]
