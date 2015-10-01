from datetime import datetime
import logging
import os

logger = logging.getLogger('helpGit')


class GitDirectory(object):
    week_log = None
    status = None
    last_fetch = None

    def __init__(self, git_dir):
        self.directory = git_dir

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
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.old_dir)
