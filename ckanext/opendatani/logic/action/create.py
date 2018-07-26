from ckanext.opendatani.model import CkanextSFTPLogs
import ckan.logic as logic

check_access = logic.check_access


def insert_sftp_log(context, data_dict):
    '''
    Insert new log from sftp script
    :param context: log message
    :return: saved log
    '''

    check_access('insert_sftp_log', context)

    data = {
        'message': data_dict['message']
    }
    logs_table = CkanextSFTPLogs(**data)
    logs_table.save()

    return data