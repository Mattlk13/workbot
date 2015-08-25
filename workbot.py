import json
import logging
import os
import subprocess

from flask import Flask, jsonify
from flask.templating import render_template

app = Flask(__name__)


class GitDir(object):
    def __init__(self, git_dir):
        self.directory = git_dir

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


def find_git_dirs(base_dir):
    """
    Walks the base_dir to find all git directories.

    :param base_dir: The starting dir for walking
    :type base_dir str
    :return: list of directories
    """
    all_git_dirs = []
    for root, dirs, files in os.walk(base_dir):
        if '.git' in dirs:
            all_git_dirs.append(root)

    return all_git_dirs


def create_cache_file(param):
    cache_file = '/tmp/gitdirs.json'
    if not os.path.isfile(cache_file):
        with open(cache_file, 'w+') as c_file:
            c_file.write(json.dumps(param))


def get_cached_dirs(base_dir, update_cache):
    """
    Reads a file that is the list of the directories found. This is what we use without refrshing the list
    :return: list of directories
    """

    cache_file = '/tmp/gitdirs.json'

    if os.path.isfile(cache_file) and not update_cache:
        with open(cache_file, 'r') as c_file:
            return json.load(c_file)
    else:
        dir_obj = {'base_dir': base_dir, 'git_dirs': find_git_dirs(base_dir)}
        create_cache_file(dir_obj)
        return dir_obj


def get_dirs(base_dir, update_cache=False):
    return get_cached_dirs(base_dir, update_cache=update_cache)


def verify_git_dir(git_dir):
    with ChDir(git_dir):
        try:
            subprocess.check_call(['git', 'rev-parse', '--is-inside-work-tree'])
            return True
        except subprocess.CalledProcessError as e:

            app.logger.info('Directory [{}] is not a GIT dir.'.format(git_dir))
            return False


def get_git_status(git_dir):
    """
     Uses git binary to get the information on the specified directory.

    :param git_dir: a known GIT directory
    :return: a git summary for the repository
    """
    with ChDir(git_dir):
        if verify_git_dir(git_dir):
            return subprocess.check_output(['git', 'status', '--porcelain'])
    return 'not a git dir'


def get_last_fetch_time(git_dir):
    with ChDir(git_dir):
        app.logger.info('[{}] : Git stat on git dir FETCH_HEAD file'.format(git_dir))
        try:
            mtime = os.stat('.git/FETCH_HEAD').st_mtime
            app.logger.debug('{} -> mtime: {}'.format(git_dir, mtime))
            return mtime
        except FileNotFoundError as e:
            app.logger.warn('[{}] : FETCH_HEAD not found.'.format(git_dir))
            return None


@app.route('/refresh_dirs')
def add_numbers():
    return jsonify(get_dirs(os.path.join(os.path.expanduser('~')), update_cache=True))


@app.route('/')
def hello_world():
    context = get_dirs(os.path.join(os.path.expanduser('~')))
    context['git_obj_list'] = []
    for git_dir in context.get('git_dirs'):
        gd = GitDir(git_dir)
        gd.last_fetch = get_last_fetch_time(git_dir)
        gd.status = get_git_status(git_dir).splitlines()
        context['git_obj_list'].append(gd)

    context['dir_summary'] = get_git_status(context.get('git_dirs')[1])
    return render_template('index.html', **context)


if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True)
