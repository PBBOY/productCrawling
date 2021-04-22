import os
import sys
import unittest

baseprojectpath = os.path.dirname(
                os.path.dirname(os.path.dirname(__file__))
            )
baseprojectpathexists = False
for syspath in sys.path:
    if baseprojectpath == syspath :
        baseprojectpathexists = True
        break

if not baseprojectpathexists:
    sys.path.append(baseprojectpath)

from common.config.configmanager import ConfigManager


class ConfigManagerTest(unittest.TestCase):

    def setUp(self) -> None:
        self._file = 'application_test.json'
        self.config = ConfigManager()

    def tearDown(self) -> None:
        self.f.close()

    # def test_load(self):
    #     with open(self.path, "r") as f:
    #         test_json: dict = json.load(f)
    #
    #         self.assertIsNotNone(test_json)
    #
    # def test_parse_data(self):
    #     json_data: dict = json.load(self.f)
    #
    #     database = json_data.get('database')
    #     self.assertIsNotNone(database)
    #     config = json_data.get('crawl_config')
    #     self.assertIsNotNone(config)


if __name__ == '__main__':
    unittest.main()