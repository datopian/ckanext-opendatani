import ckanext.sftp_script.uploader as parse_id
import unittest


class TestUploader(unittest.TestCase):

    #def setUp(self):
        #

    def test_parse_id(self):
        id = 'aa2c9a3c-395c-232d-bc8f-6b759155555'
        path = 'OSNI_Open_Data_Largescale_Boundaries_' + id + '.csv'
        result = parse_id(path)
        self.assertEqual(result, id)
