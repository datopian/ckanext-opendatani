import pysftp
import functools
import tempfile
import datetime
from ckanapi import RemoteCKAN, NotFound, ValidationError, CKANAPIError
import re
import logging
from logging import getLogger
from logger import  NiLogHandler
import shutil
from helpers import config_section

log = getLogger(__name__)
log.setLevel('DEBUG')


def print_transfer(filename, bytes_so_far, bytes_total):
    '''
    Print download bytes and percentages
    :param filename:
    :param bytes_so_far:
    :param bytes_total:
    :return:
    '''
    print 'Transfer of %r is at %d/%d bytes (%.1f%%)' % (
       filename, bytes_so_far, bytes_total, 100. * bytes_so_far / bytes_total)


def parse_id(resource_id):
    '''
    Parse resource name and get id from it. Id will always be after last _
    :param resource_id: Resource file name
    :return:
    '''
    m = re.search(r'([^\_]+$)', resource_id)
    resource_name = m.group(1)
    # remove .csv
    resourceid = resource_name[:-4]
    return resourceid


def connect():
    '''
    Connect to SFTP server and get files
    :return:
    '''

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # create tmp dir for downloaded resources
    tmpdir = tempfile.mkdtemp()
    sftp_host = config_section('sftp')['host']
    sftp_user = config_section('sftp')['username']
    sftp_pass = config_section('sftp')['password']

    try:
        with pysftp.Connection(sftp_host,
                               username=sftp_user,
                               password=sftp_pass,
                               cnopts = cnopts
                               ) as sftp:
            # initial dir in NI sftp server
            sftp.chdir('/DE')
            for dir in sftp.listdir():
                # check if remotepath is a directory
                if sftp.isdir(dir):
                    sftp.chdir(dir)
                    for file in sftp.listdir('.'):
                        # check if remotepath is a file
                        if sftp.isfile(file):
                            callback_for_filename = \
                                functools.partial(print_transfer, file)
                            try:
                                # download resource
                                sftp.get(file, tmpdir + '/' +
                                         file, callback=callback_for_filename)
                                # log.info('Successfully downloaded: '+ file)
                                resource_create(dir, tmpdir + '/' + file, dir)
                            except Exception as e:
                                log.error(e.message)
                    sftp.chdir('..')
    except Exception as ex:
        log.error(ex.message)

    finally:
        # remove tmp dir
        shutil.rmtree(tmpdir)


def resource_create(package_id, resource, dataset):
    '''
    Upload resource to CKAN
    :param package_id: id of the Dataset
    :param resource: resource path
    :param dataset: dataset name
    :return:
    '''
    ua = 'ckanapicall/1.0 (+https://ni-stage.ckan.io)'
    resourceid = parse_id(resource)
    # TODO: remove mapings when deployed to prod
    mapata = {

        '80b35bde-a3d9-48fa-956d-51df777d8f54':'6f1f81c8-3b77-42df-9a6d-1fdf30884937',
        'ee2c9a3c-395c-402d-bc8f-6b7591038108':'d36d5582-fcb1-4c70-9a22-c22ce456cd14'
    }
    remote_ckan = config_section('actions')['url']
    api_key = config_section('actions')['apikey']

    last_modified = datetime.datetime.now().isoformat()
    try:
        with RemoteCKAN(remote_ckan,
                        apikey=api_key,
                        user_agent=ua) as ni_portal:
            response = ni_portal.action.resource_update(
                    package_id=package_id,
                    upload=open(resource, 'rb'),
                    last_modified= last_modified,
                    id=mapata[resourceid]
                )
            if response:
                # get resource preview url instead of download link
                resource_url = response['url'].split('/download')[0]
                resource_name = response['name']
                log.info('Successfully updated ' + dataset + ' resource '+ '<a href="'
                         + resource_url + '">' + resource_name + '</a>')
    except NotFound as nf:
        log.error('Resource was not found. ' + nf)
    except ValidationError as ve:
        log.error('Resource validation error. '+ ve)
    except CKANAPIError as ce:
        log.error('Resource update error. ' + ce)


if __name__ == "__main__":
    logging.basicConfig(filename='./uploader-logs.txt',
                        datefmt="%Y-%m-%d %H:%M:%S")
    logger = getLogger().addHandler(NiLogHandler())
    connect()