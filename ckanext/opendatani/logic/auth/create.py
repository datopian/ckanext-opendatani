from ckanext.opendatani.model import CkanextSFTPLogs
import ckan.logic as logic

check_access = logic.check_access


def insert_sftp_log(context, data_dict):
    '''
            Authorization check for inserting sftp logs
        '''
    # sysadmins only
    return {'success': False}