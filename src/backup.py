#!/usr/bin/env python

from subprocess import call, Popen, PIPE
from os.path import join, basename, exists, dirname
import datetime
from argparse import ArgumentParser
from os import makedirs, stat, remove, devnull
import logging
from rules import Rule
import json
import sys

rsync_always = [
        '--archive',            # = -rlptgoD
        '--compress',           # compress for remote transfer
        '--delete',             # remove deleted dirs
        '--delete-excluded',    # also delete the excluded files
        '--force',              # force deletion of dirs even if not empty
        '--progress',           # output progress as it goes on stdout
        '--no-owner',           # do not check ownership changes
        '--no-group',           # do not check ownership changes
        '--no-perms',           # do not check permission changes
        '--modify-window=1',    # allow slight timestamp variation (since fat32 is not very precise)
        '--itemize-changes',    # display the actions to be taken before starting
        '--one-file-system',    # Do not cross filesystem boundaries when recursing: for security reasons
]


def make_dirpath(filepath):
    if not exists(dirname(filepath)):
        makedirs(dirname(filepath))


def backup(args):
    with open(args.config) as config_file:
        config = json.load(config_file)
    rule = Rule(config)
    rule.options.dryrun = args.dryrun

    now = datetime.datetime.now()
    rsync_command = ['rsync'] + rsync_always + rule.get_optional_args(now) + rule.get_positional_args(now)

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

    logging.debug('done')

    # clean
    # remove(progress_filepath)


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
