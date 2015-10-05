#!/usr/bin/env python3
import argparse
import logging
import logging.config
from pprint import pprint

from utils import GitDirectory

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
parser.add_argument('--color', '-c', action='store_true', default=False, help='Print text with color.')
parser.add_argument('--more', '-m', action='store_true', default=False,
                    help='Expand logs and status summaries to give more details on repository.')
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


class BColors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def print_the_stuff(gd, show_logs=False):
    """

    :param gd:
    :type gd GitDirectory
    :return:
    """
    print(BColors.HEADER + '{:*^120}'.format(gd.directory) + BColors.ENDC)
    if gd.logs and show_logs:
        pprint(BColors.OKBLUE + gd.logs + BColors.ENDC)

    print(BColors.WARNING + '\nStatus:' + BColors.ENDC)
    for line in gd.status.splitlines():
        print('\t' + line.decode('ascii'))

    if gd.queued_commits:
        commits = gd.get_queued_commits_logs()
        print(BColors.WARNING + '\nQueued commits: ' + BColors.ENDC + '{}'.format(
            gd.status.splitlines()[0].decode("ascii")))
        for commit_log in commits:
            print('\t| {blue}{commit_id}{endc} {:<84}'.format(commit_log['message'].decode("ascii"),
                                                              commit_id=commit_log['id'].decode("ascii"),
                                                              blue=BColors.OKBLUE, endc=BColors.ENDC))
    

def print_stats(list_of_git_dir_objects):
    """

    :param list_of_git_dir_objects: list of git directory objects
    :type list_of_git_dir_objects GitDirectory[]
    :return:
    """
    print(BColors.OKBLUE + '{:-^120}'.format(' Stats ') + BColors.ENDC)
    # Status at a high level for all repos
    total_repos = len(list_of_git_dir_objects)
    total_queued_commits = 0
    trash_repos = []
    for repo in list_of_git_dir_objects:
        total_queued_commits += len(repo.get_queued_commits_logs())
        if 'Trash' in repo.directory:
            trash_repos.append(repo.directory)

    print('Total repos found: {}'.format(total_repos))
    print('Total queues commits: {}'.format(total_queued_commits))
    print()
    print(BColors.WARNING + 'List of repos in your trash maybe?' + BColors.ENDC)
    print(BColors.WARNING + '\t- {}'.format("\n\t- ".join(trash_repos)))


def print_colors():
    print(BColors.HEADER + ' HEADER' + BColors.ENDC)
    print(BColors.OKBLUE + ' OKBLUE' + BColors.ENDC)
    print(BColors.OKGREEN + ' OKGREEN' + BColors.ENDC)
    print(BColors.WARNING + ' WARNING' + BColors.ENDC)
    print(BColors.FAIL + ' FAIL' + BColors.ENDC)


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
        gd.get_git_status(more=args.more)
        gd.get_log()
        gd.get_queued_commits()

        repos.append(gd)
        print('{green}Processed GitDir: {}{endc}'.format(gd, green=BColors.OKGREEN, endc=BColors.ENDC))

    for index, gd in enumerate(repos):
        print_the_stuff(gd)
    print()

    print_stats(repos)


if __name__ == '__main__':
    main()
