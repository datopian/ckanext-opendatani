from ckan.plugins import toolkit
from ckanext.opendatani.model import CkanextSFTPLogs

@toolkit.side_effect_free
def list_sftp_logs(context, data_dict):
    '''
    Returns list of all logs from sftp script in the db
    :param context:
    :param data_dict:
    :return: logs list
    '''

    logs_table = CkanextSFTPLogs()
    result = logs_table.search()
    if result:
        return result
    else:
        return 'No logs found.'
