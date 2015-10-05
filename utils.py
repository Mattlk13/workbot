from datetime import datetime
import logging
import os
import subprocess

logger = logging.getLogger('helpGit')
GIT_COMMIT_FIELDS = ['id', 'author_name', 'author_email', 'date', 'message']
GIT_LOG_FORMAT = ['%H', '%an', '%ae', '%ad', '%s']
GIT_LOG_FORMAT = '%x1f'.join(GIT_LOG_FORMAT) + '%x1e'

JEFF_GMAIL = "jeffreyrobertbean@gmail.com"
JEFF_HDS = "jeff.bean@hds.com"


def get_git_config_user_email():
    return subprocess.check_output(['git', 'config', '--get', 'user.email'])


def get_git_config_user_name():
    return subprocess.check_output(['git', 'config', '--get', 'user.name'])


class GitDirectory(object):
    logs = None
    status = None
    last_fetch = None
    queued_commits = []
    remotes = []

    def __init__(self, git_dir):
        self.git_cmd = 'git'
        self.directory = os.path.abspath(git_dir)
        self._verify_git_dir()
        self.remotes = self.set_remote()

    def set_remote(self):
        cmd = [self.git_cmd, 'remote', '-v']
        with ChDir(self.directory):
            return subprocess.check_output(cmd).splitlines()

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

    def get_git_status(self, more=False):
        """
         Uses git binary to get the information on the specified directory.
        :return: a git summary for the repository
        """
        cmd_args = u'{} -c color.ui=always -c color.status=always status --branch '.format(self.git_cmd)
        if not more:
            cmd_args += '--short'
        with ChDir(self.directory):

            logger.debug('Running status command: {}'.format(cmd_args))
            proc = subprocess.Popen(
                cmd_args,
                shell=True,
                stdout=subprocess.PIPE
            )
            logger.debug('Running git status: {}'.format(proc.args))
            try:
                outs, errs = proc.communicate(timeout=15)
                self.status = outs
            except subprocess.TimeoutExpired:
                logger.warning('Timeout getting git status.')
                proc.kill()

    def get_queued_commits(self, author_filter=None):
        """
        Finding the commits that are not pushed to the origin remote
            http://stackoverflow.com/questions/2969214/git-programmatically-know-by-how-much-the-branch-is-ahead-behind-a-remote-branc
        """
        with ChDir(self.directory):
            try:
                logger.debug('Verify Dir Has an upstream branch: {}'.format(self.directory))
                subprocess.check_call([self.git_cmd, 'rev-parse', '--quiet', '@{u}..'])
            except subprocess.CalledProcessError as e:
                logger.exception(e)
                return
            cmd_args = [self.git_cmd, 'rev-list', ]
            if author_filter:
                cmd_args.extend([

                    '--author="{}"'.format(get_git_config_user_email()),
                    '--author="{}"'.format(get_git_config_user_name()),
                ])
            cmd_args.append('@{u}..')
            logger.debug('Running command: {}'.format(cmd_args))
            self.queued_commits = subprocess.check_output(cmd_args).splitlines()

    def get_queued_commits_logs(self):
        if self.logs and self.queued_commits:
            return [log for log in self.logs for queued_commit in self.queued_commits
                    if log['id'] == queued_commit]
        return []

    def get_log(self, since=None, max_count=50):
        with ChDir(self.directory):
            log_cmd = u'{git} log --max-count={1:d} --format="{0:s}"'.format(GIT_LOG_FORMAT, max_count,
                                                                             git=self.git_cmd),
            if since:
                log_cmd += u' --since="{0:s}"'.format(since)
            p = subprocess.Popen(
                log_cmd,
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
                self.logs = git_log_entries

    def fetch_on_git_dir(self):
        cmd = '{} fetch --progress --verbose'.format(self.git_cmd)
        with ChDir(self.directory):
            logger.debug('Starting to run FETCH on {}.'.format(self))
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL
            )
            try:
                outs, errs = proc.communicate(timeout=15)
                self.status = outs
            except subprocess.TimeoutExpired:
                logger.warning('Directory [{}] Could not FETCH.'.format(self.directory))
                proc.kill()

    def _verify_git_dir(self):
        with ChDir(self.directory):
            try:
                subprocess.check_call([self.git_cmd, 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.DEVNULL)
                logger.debug('Verify Dir is indeed a git dir: {}'.format(self.directory))
            except subprocess.CalledProcessError as e:
                logger.error('Directory [{}] is not a GIT dir.'.format(self.directory))
                logger.exception(e)

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
        logger.debug('Enter Dir: {}'.format(self.new_dir))
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        logger.debug('Exit Dir: {}'.format(self.old_dir))
        os.chdir(self.old_dir)
