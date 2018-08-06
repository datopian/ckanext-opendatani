import ckan.logic as logic
from ckan.plugins.toolkit import _


def insert_sftp_log(context, data_dict):
    '''
            Authorization check for inserting sftp logs
        '''
    # sysadmins only
    return {'success': False}


def list_sftp_logs(context, data_dict):
    '''
            Authorization check for list sftp logs
        '''
    # logged in user only
    user = context['user']

    if user:
        return {'success': True}
    else:
        message = _('Only registered users can view logs.')

        return {'success': False, 'msg': message}