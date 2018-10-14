import logging
import datetime
import unittest
import os.path as path
import sys

ROOT_PATH = path.dirname(path.dirname(path.realpath(__file__)))
sys.path.append(path.join(ROOT_PATH, 'src'))
from rules import *


class SourceTest(unittest.TestCase):
    def test_local_basic(self):
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
        logging.debug(args)
        self.assertEqual(args[-2], 'source_path/')
        self.assertEqual(args[-1], 'destination_path')


class TargetTest(unittest.TestCase):
    def test_remote_basic(self):
        config = {
            "source": {
                "dirpath": "source_path"
            },
            "dest": {
                "dirpath": "destination_path",
                "ssh": {
                    "url": "server.url",
                    "port": 35123,
                    "user": "user",
                    "key": "/path/to/id_rsa"
                }
            },
            "options": {}
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        logging.debug(args)
        self.assertEqual(args[-2], 'source_path/')
        self.assertEqual(args[-1], 'user@server.url:destination_path')

    def test_local_dated(self):
        config = {
            "source": {
                "dirpath": "source_path"
              },
            "dest": {
                "dirpath": "destination_path/%Y-%m-%d-%H-%M"
            },
            "options": {}
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        logging.debug(args)
        self.assertEqual(args[-2], 'source_path/')
        self.assertEqual(args[-1], 'destination_path/2012-09-16-00-00')


class VersionTest(unittest.TestCase):
    def test_basic(self):
        config = {
          "source": {
            "dirpath": "source_path"
          },
          "dest": {
            "dirpath": "destination_path",
            "backup": "backup_path/"
          },
          "options": {}
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        logging.debug(args)
        # check there is expected flags
        self.assertIn('--backup', args)
        self.assertIn('--backup-dir={}'.format(config['dest']['backup']), args)

    def test_dated(self):
        config = {
            "source": {
                "dirpath": "source_path"
            },
            "dest": {
                "dirpath": "destination_path",
                "backup": "backup_path/%Y-%m-%d-%H-%M"
            },
            "options": {}
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        logging.debug(args)
        # check there is expected flags
        self.assertIn('--backup', args)
        self.assertIn('--backup-dir=backup_path/2012-09-16-00-00', args)


class LogTest(unittest.TestCase):
    def test_basic(self):
        config = {
          "source": {
            "dirpath": "source_path"
          },
          "dest": {
            "dirpath": "destination_path"
          },
          "options": {},
           "log": {
                "success": "log.txt",
                "error": "errors.txt",
                "progress": "progress.txt"
           }
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        logging.debug(args)
        self.assertIn('--log-file={}'.format(config['log']['success']), args)
        self.assertEqual(config['log']['success'], rule.log.get_sucess_filepath(now))
        self.assertEqual(config['log']['progress'], rule.log.get_progress_filepath(now))
        self.assertEqual(config['log']['error'], rule.log.get_error_filepath(now))

    def test_dated(self):
        config = {
          "source": {
            "dirpath": "source_path"
          },
          "dest": {
            "dirpath": "destination_path"
          },
          "options": {},
           "log": {
                "success": "%Y-%m-%d-%H-%M_log.txt",
                "error": "%Y-%m-%d-%H-%M_errors.txt",
                "progress": "%Y-%m-%d-%H-%M_progress.txt"
           }
        }
        rule = Rule(config)
        now = datetime.datetime(2012, 9, 16, 0, 0)
        args = rule.get_optional_args(now) + rule.get_positional_args(now)
        logging.debug(args)
        self.assertIn('--log-file=2012-09-16-00-00_log.txt', args)
        self.assertEqual('2012-09-16-00-00_log.txt', rule.log.get_sucess_filepath(now))
        self.assertEqual('2012-09-16-00-00_progress.txt', rule.log.get_progress_filepath(now))
        self.assertEqual('2012-09-16-00-00_errors.txt', rule.log.get_error_filepath(now))


if __name__ == '__main__':
    if __debug__:
        logging.getLogger().setLevel(logging.DEBUG)

    unittest.main()

