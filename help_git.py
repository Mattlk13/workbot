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

GIT_COMMIT_FIELDS = ['id', 'author_name', 'author_email', 'date', 'message']
GIT_LOG_FORMAT = ['%H', '%an', '%ae', '%ad', '%s']
GIT_LOG_FORMAT = '%x1f'.join(GIT_LOG_FORMAT) + '%x1e'


def verify_git_dir(git_dir):
    with ChDir(git_dir):
        try:
            p = subprocess.check_call(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.DEVNULL)
            logger.debug('Verify Dir is indeed a git dir: {}'.format(git_dir))
            if p == 0:
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            logger.error('Directory [{}] is not a GIT dir.'.format(git_dir))
            return False


def get_git_status(gd, short=False):
    """
     Uses git binary to get the information on the specified directory.

    :param gd: a known GIT directory
    :type gd GitDirectory
    :return: a git summary for the repository
    """
    cmd_args = ['git', 'status', '--branch']

    with ChDir(gd.directory):
        if short:
            cmd_args.append('--porcelain')
        logger.debug(cmd_args)

        return subprocess.check_output(cmd_args)




def get_git_log(gd, since, max_count=50):
    with ChDir(gd.directory):
        p = subprocess.Popen(
            u'git log --max-count={1:d} --since="{2:s}" --format="{0:s}"'.format(GIT_LOG_FORMAT, max_count, since),
            shell=True,
            stdout=subprocess.PIPE
        )
        logger.debug('Running git log: {}'.format(p.args))
        (git_log_entries, _) = p.communicate()
        git_log_entries = git_log_entries.strip(b'\n\x1e').split(b"\x1e")
        git_log_entries = [row.strip().split(b"\x1f") for row in git_log_entries]
        git_log_entries = [dict(zip(GIT_COMMIT_FIELDS, row)) for row in git_log_entries]
        if any(git_log_entry.get('id') for git_log_entry in git_log_entries):
            logger.debug('git logs: {}'.format(git_log_entries))
            return git_log_entries


def fetch_on_git_dir(gd):
    with ChDir(gd.directory):
        try:
            return subprocess.check_call(['git', 'fetch'])
        except subprocess.CalledProcessError as e:
            logger.warning('Directory [{}] Could not fetch GIT data.'.format(gd))


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
            fetch_on_git_dir(gd)

        gd.get_last_fetch_time()
        gd.status = get_git_status(gd, args.short)
        gd.week_log = get_git_log(gd, "a week ago")

        print_the_stuff(gd)

        logger.debug('--------------------------------------')
        repos.append(gd)


if __name__ == '__main__':
    main()
