#!/usr/bin/env python3
import argparse
import logging
import logging.config
import subprocess
from pprint import pprint
from utils import ChDir, GitDirectory

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(module)s %(levelname)-8s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'helpGit': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

parser = argparse.ArgumentParser()
parser.add_argument('base_path', help='The base directory to search through')
parser.add_argument('--short', '-s', action='store_true', default=False, help='The base directory to search through')
parser.add_argument('--fetch', '-f', action='store_true', default=False,
                    help='For every git dir we find, run "git fetch".')
parser.add_argument('--verbose', '-v', action='store_true', default=False, dest='verbose',
                    help='The base directory to search through')

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('helpGit')

def find_git_dirs(base_dir):
    """
    Walks the base_dir to find all git directories.

    :param base_dir: The starting dir for walking
    :type base_dir str
    :return: yeild one dir at a time
    """
    for root, dirs, files in walk(base_dir):
        if 'svn' in dirs:
            dirs.remove('svn')
        if '.git' in dirs:
            yield root


def print_the_stuff(gd, show_logs=False):
    """

    :param gd:
    :type gd GitDirectory
    :return:
    """
    print('#{:_^100}#'.format(gd.directory))
    if gd.logs and show_logs:
        pprint(gd.logs)

    for line in gd.status.splitlines():
        print(line.decode('utf-8'))

    if gd.queued_commits:
        print('\nQueued commits:')
        pprint(gd.get_queued_commits_logs())

    else:
        print('\nNo Queued commits.')


def print_stats(list_of_git_dir_objects):
    total_repos = len(list_of_git_dir_objects)

def main():
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    repos = []

    for git_path in find_git_dirs(args.base_path):
        gd = GitDirectory(git_path)

        if args.fetch:
            gd.fetch_on_git_dir()

        gd.get_last_fetch_time()
        gd.get_git_status(verbose=args.verbose)
        gd.get_log()
        gd.get_queued_commits()

        repos.append(gd)
        print('Processed GitDir: {}'.format(gd))

    for index, gd in enumerate(repos):
        print_the_stuff(gd)
    print_stats(repos)


if __name__ == '__main__':
    main()
