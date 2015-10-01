from datetime import datetime
import logging
import os
import subprocess

logger = logging.getLogger('helpGit')
GIT_COMMIT_FIELDS = ['id', 'author_name', 'author_email', 'date', 'message']
GIT_LOG_FORMAT = ['%H', '%an', '%ae', '%ad', '%s']
GIT_LOG_FORMAT = '%x1f'.join(GIT_LOG_FORMAT) + '%x1e'


class GitDirectory(object):
    week_log = None
    status = None
    last_fetch = None

    def __init__(self, git_dir):
        self.directory = git_dir
        self._verify_git_dir()

    def get_last_fetch_time(self):
        with ChDir(self.directory):
            logger.debug('[{}] : Git stat on git dir FETCH_HEAD file'.format(self.directory))
            try:
                mtime = os.stat('.git/FETCH_HEAD').st_mtime
                mtime = datetime.fromtimestamp(mtime)
                logger.debug('{} -> mtime: {}'.format(self.directory, mtime))
                self.last_fetch = mtime
            except FileNotFoundError as e:
                logger.warning('[{}] : FETCH_HEAD not found.'.format(self.directory))

    def get_git_status(self, short=False):
        """
         Uses git binary to get the information on the specified directory.

        :param gd: a known GIT directory
        :type gd GitDirectory
        :return: a git summary for the repository
        """
        cmd_args = ['git', 'status', '--branch']
        with ChDir(self.directory):
            if short:
                cmd_args.append('--porcelain')
            logger.debug('Running status command: {}'.format(cmd_args))
            self.status = subprocess.check_output(cmd_args)

    def set_git_log(self, since, max_count=50):
        with ChDir(self.directory):
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
                self.week_log = git_log_entries

    def _verify_git_dir(self):
        with ChDir(self.directory):
            try:
                p = subprocess.check_call(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.DEVNULL)
                logger.debug('Verify Dir is indeed a git dir: {}'.format(self.directory))
                if p == 0:
                    return True
                else:
                    return False
            except subprocess.CalledProcessError as e:
                logger.error('Directory [{}] is not a GIT dir.'.format(self.directory))
                return False


    def __str__(self):
        return self.directory

    def __unicode__(self):
        return self.directory


class ChDir(object):
    """
    Step into a directory temporarily.
    """

    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        logger.debug('Change Dir: {}'.format(self.new_dir))
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        logger.debug('Change Dir: {}'.format(self.old_dir))
        os.chdir(self.old_dir)
