import logging
import requests
import json
from helpers import config_section


class NiLogHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)
        # do not throw erros from loging handler for
        # development set this to True
        logging.raiseExceptions = False

    def emit(self, record):
        try:
            data={
                'message': record.message
            }
            remote_ckan = config_section('logger')['url']
            api_key = config_section('logger')['apikey']
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': api_key}
            requests.post(remote_ckan, data=json.dumps(data), headers=headers)
        except Exception as err:
            self.handleError(err.message)