#!/usr/bin/env python3
import argparse
import logging
import logging.config
import subprocess

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
parser.add_argument('--verbose', '-v', action='store_true', default=False, dest='debug',
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


def print_the_stuff(gd):
    """

    :param gd:
    :type gd GitDirectory
    :return:
    """
    print('DIR: {}'.format(gd.directory))
    if gd.week_log:
        for log_item in gd.week_log:
            for k, v in log_item:
                print('Key: {} Value: {}'.format(k, v))
    for line in gd.status.splitlines():
        print(line.decode('utf-8'))


def main():
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    repos = []

    for git_path in find_git_dirs(args.base_path):
        gd = GitDirectory(git_path)

        if args.fetch:
            gd.fetch_on_git_dir()

        gd.get_last_fetch_time()
        gd.get_git_status(short=args.short)
        gd.set_git_log("a week ago")

        print_the_stuff(gd)

        logger.debug('--------------------------------------')
        repos.append(gd)


if __name__ == '__main__':
    main()
