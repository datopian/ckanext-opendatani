from ckan.plugins import toolkit
import ckan.logic as logic
from ckanext.opendatani.model import CkanextSFTPLogs, table_dictize
check_access = logic.check_access


@toolkit.side_effect_free
def list_sftp_logs(context, data_dict):
    '''
    Returns list of all logs from sftp script in the db
    :param context:
    :param data_dict:
    :return: logs list
    '''

    check_access('list_sftp_logs', context)

    logs_table = CkanextSFTPLogs()
    result = logs_table.search()
    out = []
    if result:
        for log in result:
            log = table_dictize(log, context)
            out.append(log)
        return out
    else:
        # return empty list
        return out
