from datetime import datetime
import logging
import os
import subprocess

logger = logging.getLogger('helpGit')
GIT_COMMIT_FIELDS = ['id', 'author_name', 'author_email', 'date', 'message']
GIT_LOG_FORMAT = ['%H', '%an', '%ae', '%ad', '%s']
GIT_LOG_FORMAT = '%x1f'.join(GIT_LOG_FORMAT) + '%x1e'


class GitDirectory(object):
    logs = None
    status = None
    last_fetch = None
    queued_commits = []
    remote = None
    def __init__(self, git_dir):
        self.directory = os.path.abspath(git_dir)
        self._verify_git_dir()
        self.set_remote()

    def set_remote(self):
        cmd = ['git', 'remote', '-v']
        with ChDir(self.directory):
            self.remote = subprocess.check_output(cmd)

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

    def get_git_status(self, verbose=False):
        """
         Uses git binary to get the information on the specified directory.

        :param gd: a known GIT directory
        :type gd GitDirectory
        :return: a git summary for the repository
        """
        cmd_args = ['git', 'status', '--branch']
        with ChDir(self.directory):
            if not verbose:
                cmd_args.append('--porcelain')
            logger.debug('Running status command: {}'.format(cmd_args))
            self.status = subprocess.check_output(cmd_args)

    def get_queued_commits(self):
        """
        Ffinding the commits that are not pushed to the origin remote
            http://stackoverflow.com/questions/2969214/git-programmatically-know-by-how-much-the-branch-is-ahead-behind-a-remote-branc
        """
        if not self.last_fetch:
            logger.warning('Since fetch was found, we cant rely on the rev-list to be accruate. SKIPPING queued commits')
            return
        cmd_args = ['git', 'rev-list', '@{u}..']
        with ChDir(self.directory):
            logger.debug('Running command: {}'.format(cmd_args))
            self.queued_commits = subprocess.check_output(cmd_args).splitlines()

    def get_queued_commits_logs(self):
        if self.logs and self.queued_commits:
            return [log for log in self.logs for queued_commit in self.queued_commits
                if log['id'] == queued_commit]

    def get_log(self, since=None, max_count=50):
        with ChDir(self.directory):
            log_cmd = u'git log --max-count={1:d} --format="{0:s}"'.format(GIT_LOG_FORMAT, max_count),
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
        with ChDir(self.directory):
            try:
                logger.info('Starting to run FETCH on {}.'.format(self))
                return subprocess.check_call(['git', 'fetch', '--progress', '--verbose'])
            except subprocess.CalledProcessError as e:
                logger.warning('Directory [{}] Could not FETCH.'.format(self.directory))


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
