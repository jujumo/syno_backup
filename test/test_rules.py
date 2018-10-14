import datetime
import unittest
import os.path as path
import sys

ROOT_PATH = path.dirname(path.dirname(path.realpath(__file__)))
sys.path.append(path.join(ROOT_PATH, 'src'))
from rules import *

class RulesLocalTest(unittest.TestCase):
    def test_basic(self):
        config = {
            "source": {
                "dirpath": "source_path"
              },
            "dest": {
                "dirpath": "destination_path"
            },
            "options": {}
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        print(args)
        self.assertEqual(args[-2], 'source_path/')
        self.assertEqual(args[-1], 'destination_path')


class RulesRemoteTest(unittest.TestCase):
    def test_remotes(self):
        config = {
          "source": {
            "dirpath": "/volume1/photo"
          },
          "dest": {
            "dirpath": "/volume1/NetBackup/save/photo/latest",
            "backup": "/volume1/NetBackup/save/photo/%Y-%m-%d-%H-%M",
            "ssh": {
              "url": "jumo-mimo.myds.me",
              "port": 35123,
              "user": "rsync",
              "key": "/var/services/homes/jumo/.ssh/id_rsa"
            }
          },
          "options": {
            "exclude": ["temp", "@eaDir"],
            "dryrun": True,
            "log_path": "/volume1/photo/log/%Y-%m-%d-%H-%M_log.txt"
          }
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        # print(rule.get_optional_args(now) + rule.get_positional_args(now))


if __name__ == '__main__':
    unittest.main()

