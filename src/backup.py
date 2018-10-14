#!/usr/bin/env python

from subprocess import call, Popen, PIPE
from os.path import realpath, basename, exists, dirname
import datetime
from argparse import ArgumentParser
from os import makedirs, stat, remove, devnull
import logging
from rules import Rule
import json
import sys


def make_dirpath(filepath):
    if not exists(dirname(filepath)):
        makedirs(dirname(filepath))


def backup(args):
    with open(args.config) as config_file:
        config = json.load(config_file)
    rule = Rule(config)
    rule.options.dryrun = args.dryrun

    now = datetime.datetime.now()
    rsync_command = ['rsync'] + rule.get_optional_args(now) + rule.get_positional_args(now)

    # create dirs fro log files
    success_filepath = rule.log.get_sucess_filepath(now)
    if not args.debug and success_filepath:
        make_dirpath(success_filepath)

    progress_filepath = rule.log.get_progress_filepath(now)
    if args.verbose or args.debug or not progress_filepath:
        progress_file = sys.stdout
    else:
        make_dirpath(progress_filepath)
        progress_file = open(progress_filepath, "w")

    error_filepath = rule.log.get_error_filepath(now)
    if args.verbose or args.debug or not error_filepath:
        error_file = sys.stderr
    else:
        make_dirpath(error_filepath)
        error_file = open(error_filepath, 'w') if error_filepath else PIPE

    # process
    if args.debug:
        print(' '.join(rsync_command))
    else:
        rsync_process = Popen(rsync_command, stdout=progress_file, stderr=error_file)
        rsync_process.wait()

    # some cleaning
    if progress_filepath and exists(progress_filepath):
        remove(progress_filepath)

    if error_filepath and exists(error_filepath):
        is_errors = not stat(error_filepath).st_size == 0
        if not is_errors:
            remove(error_filepath)
            user_message = 'sucessfull save of {}.'.format(rule.source.dirpath)
        else:
            with open(error_filepath, 'r') as error_file:
                last_error = error_file.readlines()[-1].decode()
                user_message = 'finished with errors on save of {}: {}'.format(rule.source.dirpath, last_error)
    else:
        user_message = 'done'

    notify_command = ['synodsmnotify', '@administrators', 'Backup {}'.format(basename(realpath(rule.source.dirpath))), user_message]
    call(notify_command)

    logging.debug('done')


def main():
    try:
        parser = ArgumentParser(description='Launch rsync for the given config file.')
        parser.add_argument('-v', '--verbose', action='store_true', help='verbose message')
        parser.add_argument('-c', '--config', required=True, help='config file path')
        parser.add_argument('-n', '--dryrun', action='store_true', help='dry-run rsync')
        parser.add_argument('-d', '--debug', action='store_true', help='print the rsync command')
        args = parser.parse_args()

        verbose = args.verbose
        if verbose:
            logging.getLogger().setLevel(logging.INFO)
        if __debug__:
            logging.getLogger().setLevel(logging.DEBUG)

        backup(args)

    except Exception as e:
        logging.critical(e)
        if __debug__:
            raise


if __name__ == '__main__':
    main()
