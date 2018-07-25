from ckan.plugins import toolkit

@toolkit.side_effect_free
def list_sftp_logs(context, data_dict):
    return 'SUCESS get'