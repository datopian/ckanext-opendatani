import logging
import requests
import json


class NiLogHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            data={
                'message': record.message
            }
            # TODO: read values from config
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Authorization': ''}
            requests.post('', data=json.dumps(data), headers=headers)
        except Exception as err:
            print err.message