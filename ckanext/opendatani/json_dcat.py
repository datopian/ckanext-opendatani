from builtins import str
import json
import logging
from hashlib import sha1
import traceback
import uuid

import requests
import rdflib
import os

from ckan import model
from ckan import logic
from ckan import plugins as p
from ckanext.harvest.model import HarvestObject, HarvestObjectExtra

from ckanext.dcat import converters
from ckanext.dcat.harvesters.base import DCATHarvester
from sqlalchemy.orm import Query
import datetime
import six
from ckanext.dcat.interfaces import IDCATRDFHarvester
import re

log = logging.getLogger(__name__)

def convert_to_html(text):
    """Converts text with formatting to HTML.

    Args:
        text: The text to be converted.

    Returns:
        The converted HTML string.
    """
    # Replace bold tags
    text = text.replace("[b]", "<b>").replace("[/b]", "</b>")

    # Replace URL links
    url_pattern = r'\[url=(https?://[^\]]+|mailto:[^\]]+)\](.*?)\[/url\]'
    replacement = r'[\2](\1)'
    text = re.sub(url_pattern, replacement, text)
    
    return text

def _remove_extra(key, dataset_dict):
        dataset_dict['extras'][:] = [e
                                     for e in dataset_dict['extras']
                                     if e['key'] != key]

class NsiraJSONHarvester(DCATHarvester):

    def info(self):
        return {
            'name': 'nsira_dcatjson',
            'title': 'NSIRA JSON (Restful) Harvester',
            'description': 'Harvester for Restful dataset descriptions ' +
                           'serialized as JSON'
        }
    
    def _get_content_and_type(self, url, harvest_job, page=1,
                              content_type=None):
        '''
        Gets the content and type of the given url.

        :param url: a web url (starting with http) or a local path
        :param harvest_job: the job, used for error reporting
        :param page: adds paging to the url
        :param content_type: will be returned as type
        :return: a tuple containing the content and content-type
        '''

        if not url.lower().startswith('http'):
            # Check local file
            if os.path.exists(url):
                with open(url, 'r') as f:
                    content = f.read()
                content_type = content_type or rdflib.util.guess_format(url)
                return content, content_type
            else:
                self._save_gather_error('Could not get content for this url',
                                        harvest_job)
                return None, None

        try:

            if page > 1:
                url = url + '&' if '?' in url else url + '?'
                url = url + 'page={0}'.format(page)

            log.debug('Getting file %s', url)

            # get the `requests` session object
            session = requests.Session()
            for harvester in p.PluginImplementations(IDCATRDFHarvester):
                session = harvester.update_session(session)

            # first we try a HEAD request which may not be supported
            did_get = False
            r = session.head(url)

            if r.status_code == 405 or r.status_code == 400:
                r = session.get(url, stream=True)
                did_get = True
            r.raise_for_status()

            cl = r.headers.get('content-length')
            if cl and int(cl) > self.MAX_FILE_SIZE:
                msg = '''Remote file is too big. Allowed
                    file size: {allowed}, Content-Length: {actual}.'''.format(
                    allowed=self.MAX_FILE_SIZE, actual=cl)
                self._save_gather_error(msg, harvest_job)
                return None, None

            if not did_get:
                r = session.get(url, stream=True)

            length = 0
            content = '' if six.PY2 else b''
            for chunk in r.iter_content(chunk_size=self.CHUNK_SIZE):
                content = content + chunk

                length += len(chunk)

                if length >= self.MAX_FILE_SIZE:
                    self._save_gather_error('Remote file is too big.',
                                            harvest_job)
                    return None, None

            if not six.PY2:
                content = content.decode('utf-8')

            if content_type is None and r.headers.get('content-type'):
                content_type = r.headers.get('content-type').split(";", 1)[0]


            # if content is a JSON array of URLS, fetch each url
            try:
                urls = json.loads(content)
                if isinstance(urls, list) and all(isinstance(u, str) for u in urls):
                    combined_content = []
                    for package_url in urls:
                        package_content, _ = self._get_content_and_type(package_url, harvest_job)
                        if package_content:
                            combined_content.append(json.loads(package_content))
                    content = json.dumps(combined_content).encode('utf-8')
                    content_type = 'application/json'
                    if not six.PY2:
                        content = content.decode('utf-8')
            except json.JSONDecodeError:
                self._save_gather_error('Could not parse content as JSON', harvest_job)
                return None, None
                        

            return content, content_type

        except requests.exceptions.HTTPError as error:
            if page > 1 and error.response.status_code == 404:
                # We want to catch these ones later on
                raise

            msg = 'Could not get content from %s. Server responded with %s %s'\
                % (url, error.response.status_code, error.response.reason)
            self._save_gather_error(msg, harvest_job)
            return None, None
        except requests.exceptions.ConnectionError as error:
            msg = '''Could not get content from %s because a
                                connection error occurred. %s''' % (url, error)
            self._save_gather_error(msg, harvest_job)
            return None, None
        except requests.exceptions.Timeout as error:
            msg = 'Could not get content from %s because the connection timed'\
                ' out.' % url
            self._save_gather_error(msg, harvest_job)
            return None, None



    def _get_guids_and_datasets(self, content):
        doc = json.loads(content)


        if isinstance(doc, list):
            # Assume a list of datasets
            datasets = doc
        elif isinstance(doc, dict):
            datasets = [doc]
        else:
            raise ValueError('Wrong JSON object')
        

        frequency = {
            "TLIST(A1)": "annually",
            "TLIST(Q1)": "quarterly",
            "TLIST(M1)": "monthly",
        }

        for dataset in datasets:
            filtered_keys = [key for key in dataset["dimension"] if key not in ("STATISTIC", "TLIST(A1)")]
            labels = [dataset["dimension"][key]["label"] for key in filtered_keys]

            if len(labels) == 1:
                output_string = labels[0]
            else:
                output_string = " by ".join(labels[:-1]) + " and " + labels[-1]


            # get Tlist from dataset using keys in frquency
            frequency_key = [key for key in dataset["dimension"] if key in ("TLIST(A1)", "TLIST(Q1)", "TLIST(M1)")]
            frequency_key = frequency_key[0]
            frequency_value = dataset["dimension"][frequency_key]["category"]["index"]
            time_period = f"{frequency_value[0]} - {frequency_value[-1]}"
            allowed_keys = {"exceptional", "official", "reservation", "archive", "experimental", "analytical"}
            tags = {k: v for k, v in dataset["extension"].items() if not isinstance(v, dict) and k in allowed_keys}

        
            dataset_copy  = {
                "title": dataset['label'],
                "titleTags": dataset['label'] + " "+ "by " + output_string,
                "name": dataset['extension']['matrix'],
                "description": convert_to_html(dataset['note'][0]), 
                "identifier": dataset['extension']['matrix'],
                "modified": dataset['updated'], 
                "landingPage": "", 
                "publisher": {
                    "name": dataset['extension']['contact'].get('name', ''),
                    "mbox": dataset['extension']['contact'].get('email', '')
                },
                "fn": dataset['extension']['contact'].get('name', ''),
                "hasEmail": dataset['extension']['contact'].get('email', ''),
                
                "language": [
                    "en"
                ],
                "distribution": [],
                "frequency": frequency[frequency_key],
                "timePeriod": time_period,
                "metaTags": json.dumps(tags),
            }

            for resource in dataset['link']['alternate']:
                if resource['type'] == "application/base64":
                    dataset_copy['distribution'].append({
                        'title': "Xlsx",
                        'accessURL': resource['href'],
                        'downloadURL': resource['href'],
                        'format': "xlsx"
                    })

                elif resource['type'] == "application/json":
                    dataset_copy['distribution'].append({
                        'title': f"JSON {resource['href'].split('/')[-2]}",
                        'accessURL': resource['href'],
                        'downloadURL': resource['href'],
                        'format': resource['type']
                    })

                else:
                    dataset_copy['distribution'].append({
                        'title': resource['type'].split("/")[1],
                        'accessURL': resource['href'],
                        'downloadURL': resource['href'],
                        'format': resource['type']
                    })



            as_string = json.dumps(dataset_copy)
            # Get identifier
            guid = dataset_copy.get('identifier')
            if not guid:
                # This is bad, any ideas welcomed
                guid = sha1(as_string).hexdigest()

            yield guid, as_string

    def _get_package_dict(self, harvest_object):

        content = harvest_object.content

        dcat_dict = json.loads(content)

        package_dict = converters.dcat_to_ckan(dcat_dict)

        package_dict['name'] = dcat_dict['name'].lower()

        return package_dict, dcat_dict

    def gather_stage(self, harvest_job):
        log.debug('In DCATJSONHarvester gather_stage steve')

        ids = []

        # Get the previous guids for this source
        query = \
            model.Session.query(HarvestObject.guid, HarvestObject.package_id) \
            .filter(HarvestObject.current == True) \
            .filter(HarvestObject.harvest_source_id == harvest_job.source.id)
        guid_to_package_id = {}

        for guid, package_id in query:
            guid_to_package_id[guid] = package_id

        guids_in_db = list(guid_to_package_id.keys())
        guids_in_source = []

        # Get file contents
        url = harvest_job.source.url

        previous_guids = []
        page = 1
        while True:

            try:
                content, content_type = \
                    self._get_content_and_type(url, harvest_job, page)
            except requests.exceptions.HTTPError as error:
                if error.response.status_code == 404:
                    if page > 1:
                        # Server returned a 404 after the first page, no more
                        # records
                        log.debug('404 after first page, no more pages')
                        break
                    else:
                        # Proper 404
                        msg = 'Could not get content. Server responded with ' \
                            '404 Not Found'
                        self._save_gather_error(msg, harvest_job)
                        return None
                else:
                    # This should never happen. Raising just in case.
                    raise

            if not content:
                return None

            try:

                batch_guids = []
                for guid, as_string in self._get_guids_and_datasets(content):
                    log.debug('Got identifier: {0}'
                              .format(guid.encode('utf8')))

                    batch_guids.append(guid)

                    if guid not in previous_guids:

                        if guid in guids_in_db:
                            # Dataset needs to be udpated
                            obj = HarvestObject(
                                guid=guid, job=harvest_job,
                                package_id=guid_to_package_id[guid],
                                content=as_string,
                                extras=[HarvestObjectExtra(key='status',
                                                           value='change')])
                        else:
                            # Dataset needs to be created
                            obj = HarvestObject(
                                guid=guid, job=harvest_job,
                                content=as_string,
                                extras=[HarvestObjectExtra(key='status',
                                                           value='new')])
                        obj.save()
                        ids.append(obj.id)

                if len(batch_guids) > 0:
                    guids_in_source.extend(set(batch_guids)
                                           - set(previous_guids))
                else:
                    log.debug('Empty document, no more records')
                    # Empty document, no more ids
                    break

            except ValueError as e:
                msg = 'Error parsing file: {0}'.format(str(e))
                self._save_gather_error(msg, harvest_job)
                return None

            if sorted(previous_guids) == sorted(batch_guids):
                # Server does not support pagination or no more pages
                log.debug('Same content, no more pages')
                break

            page = page + 1

            previous_guids = batch_guids

        # Check datasets that need to be deleted
        guids_to_delete = set(guids_in_db) - set(guids_in_source)
        for guid in guids_to_delete:
            obj = HarvestObject(
                guid=guid, job=harvest_job,
                package_id=guid_to_package_id[guid],
                extras=[HarvestObjectExtra(key='status', value='delete')])
            ids.append(obj.id)
            model.Session.query(HarvestObject).\
                filter_by(guid=guid).\
                update({'current': False}, False)
            obj.save()

        return ids

    def fetch_stage(self, harvest_object):
        return True

    def import_stage(self, harvest_object):
        log.debug('In DCATJSONHarvester import_stage')
        if not harvest_object:
            log.error('No harvest object received')
            return False

        if self.force_import:
            status = 'change'
        else:
            status = self._get_object_extra(harvest_object, 'status')

        if status == 'delete':
            # Delete package
            context = {'model': model, 'session': model.Session,
                       'user': self._get_user_name()}

            p.toolkit.get_action('package_delete')(
                context, {'id': harvest_object.package_id})
            log.info('Deleted package {0} with guid {1}'
                     .format(harvest_object.package_id, harvest_object.guid))

            return True

        if harvest_object.content is None:
            self._save_object_error(
                'Empty content for object %s' % harvest_object.id,
                harvest_object, 'Import')
            return False

        # Get the last harvested object (if any)
        previous_object = model.Session.query(HarvestObject) \
            .filter(HarvestObject.guid == harvest_object.guid) \
            .filter(HarvestObject.current == True) \
            .first()

        # Flag previous object as not current anymore
        if previous_object and not self.force_import:
            previous_object.current = False
            previous_object.add()

        
        package_dict, dcat_dict = self._get_package_dict(harvest_object)
        
        
        if not package_dict:
            return False

        if not package_dict.get('name'):
            package_dict['name'] = \
                self._get_package_name(harvest_object, package_dict['title'])

        # copy across resource ids from the existing dataset, otherwise they'll
        # be recreated with new ids
        if status == 'change':
            existing_dataset = self._get_existing_dataset(harvest_object.guid)
            if existing_dataset:
                copy_across_resource_ids(existing_dataset, package_dict)

        # Allow custom harvesters to modify the package dict before creating
        # or updating the package
        package_dict = self.modify_package_dict(package_dict,
                                                dcat_dict,
                                                harvest_object)
        # Unless already set by an extension, get the owner organization (if
        # any) from the harvest source dataset
        if not package_dict.get('owner_org'):
            source_dataset = model.Package.get(harvest_object.source.id)
            if source_dataset.owner_org:
                package_dict['owner_org'] = source_dataset.owner_org

        # Flag this object as the current one
        harvest_object.current = True
        harvest_object.add()

        context = {
            'user': self._get_user_name(),
            'return_id_only': True,
            'ignore_auth': True,
        }

        try:
            if status == 'new':
                package_schema = logic.schema.default_create_package_schema()
                
                context['schema'] = package_schema

                # We need to explicitly provide a package ID
                package_dict['id'] = str(uuid.uuid4())
                package_schema['id'] = [str]

                # Save reference to the package on the object
                harvest_object.package_id = package_dict['id']
                harvest_object.add()

                # Defer constraints and flush so the dataset can be indexed with
                # the harvest object id (on the after_show hook from the harvester
                # plugin)
                model.Session.execute(
                    'SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
                model.Session.flush()

            elif status == 'change':
                package_dict['id'] = harvest_object.package_id

            if status in ['new', 'change']:
                action = 'package_create' if status == 'new' else 'package_update'
                message_status = 'Created' if status == 'new' else 'Updated'
                package_dict['frequency'] = dcat_dict.get('frequency', '')
                package_dict['topic_category'] = 'governmentstatistics'
                package_dict['lineage'] = 'NISRA'
                package_dict['contact_name'] = dcat_dict.get('fn', '')
                package_dict['contact_email'] = dcat_dict.get('hasEmail', '')
                package_dict['license_id'] = 'uk-ogl'
                package_dict['source_last_updated'] = dcat_dict.get('modified', '')[:19].replace('.', '')
                package_dict['time_period'] = dcat_dict.get('timePeriod', '')
                package_dict['title_tags'] = dcat_dict.get('titleTags', '')
                package_dict['metatags'] = dcat_dict.get('metaTags', '')
                package_id = p.toolkit.get_action(action)(context, package_dict)
                log.info('%s dataset with id %s', message_status, package_id)

        except Exception as e:
            dataset = json.loads(harvest_object.content)
            dataset_name = dataset.get('name', '')

            self._save_object_error('Error importing dataset %s: %r / %s' % (dataset_name, e, traceback.format_exc()), harvest_object, 'Import')
            return False

        finally:
            model.Session.commit()

        return True

def copy_across_resource_ids(existing_dataset, harvested_dataset):
    '''Compare the resources in a dataset existing in the CKAN database with
    the resources in a freshly harvested copy, and for any resources that are
    the same, copy the resource ID into the harvested_dataset dict.
    '''
    # take a copy of the existing_resources so we can remove them when they are
    # matched - we don't want to match them more than once.
    existing_resources_still_to_match = \
        [r for r in existing_dataset.get('resources')]

    # we match resources a number of ways. we'll compute an 'identity' of a
    # resource in both datasets and see if they match.
    # start with the surest way of identifying a resource, before reverting
    # to closest matches.
    resource_identity_functions = [
        lambda r: r['uri'],  # URI is best
        lambda r: (r['url'], r['title'], r['format']),
        lambda r: (r['url'], r['title']),
        lambda r: r['url'],  # same URL is fine if nothing else matches
    ]

    for resource_identity_function in resource_identity_functions:
        # calculate the identities of the existing_resources
        existing_resource_identities = {}
        for r in existing_resources_still_to_match:
            try:
                identity = resource_identity_function(r)
                existing_resource_identities[identity] = r
            except KeyError:
                pass

        # calculate the identities of the harvested_resources
        for resource in harvested_dataset.get('resources'):
            try:
                identity = resource_identity_function(resource)
            except KeyError:
                identity = None
            if identity and identity in existing_resource_identities:
                # we got a match with the existing_resources - copy the id
                matching_existing_resource = \
                    existing_resource_identities[identity]
                resource['id'] = matching_existing_resource['id']
                # make sure we don't match this existing_resource again
                del existing_resource_identities[identity]
                existing_resources_still_to_match.remove(
                    matching_existing_resource)
        if not existing_resources_still_to_match:
            break
