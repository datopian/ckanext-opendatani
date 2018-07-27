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

log = getLogger(__name__)
log.setLevel('DEBUG')


def print_transfer(filename, bytes_so_far, bytes_total):
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
    return  resourceid


def connect():
    '''
    Connect to SFTP server and get files
    :return:
    '''

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    # create tmp dir for downloaded resources
    tmpdir = tempfile.mkdtemp()
    try:
        # TODO: read values from config
        with pysftp.Connection('SERVER',
                               username='USER',
                               password='PASS',
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
                            callback_for_filename = functools.partial(print_transfer, file)
                            # download resource
                            try:
                                sftp.get(file, str(tmpdir)+'/'+file, callback=callback_for_filename)
                                log.info('Successfully downloaded: '+ file)
                                resource_create(dir, str(tmpdir) + '/' + file)
                            except Exception as e:
                                log.error(e.message)
                    sftp.chdir('..')
    except Exception as ex:
        log.error(ex.message)

    finally:
        # remove tmp dir
        shutil.rmtree(tmpdir)


def resource_create(package_id, resource):
    '''
    Upload resource to CKAN
    :param package_id: id of the Dataset
    :param resource: resource path
    :return:
    '''
    ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'
    resourceid = parse_id(resource)
    # TODO: remove mapings when deployed to prod
    mapata = {

        '80b35bde-a3d9-48fa-956d-51df777d8f54':'6f1f81c8-3b77-42df-9a6d-1fdf30884937',
        'ee2c9a3c-395c-402d-bc8f-6b7591038108':'d36d5582-fcb1-4c70-9a22-c22ce456cd14'
    }
    try:
        with RemoteCKAN('https://ni-stage.ckan.io/',
                        apikey='',
                        user_agent=ua) as ni_portal:
            response = ni_portal.action.resource_update(
                    package_id=package_id,
                    upload=open(resource, 'rb'),
                    last_modified=datetime.datetime.now().isoformat(),
                    id=mapata[resourceid]
                )
            log.info('Successfully updated ' + response['name'] +
                     ' resource '+ response['url'])
    except NotFound as nf:
        log.error('Resource was not found. ' + nf)
    except ValidationError as ve:
        log.error('Resource validation error. '+ ve)
    except CKANAPIError as ce:
        log.error('Resource update error. ' + ce)


if __name__ == "__main__":
    logging.basicConfig(filename='./uploader-logs.txt')
    logger = getLogger().addHandler(NiLogHandler())
    connect()