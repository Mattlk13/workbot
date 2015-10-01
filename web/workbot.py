import json
import logging
import os
import subprocess
from django.utils.datetime_safe import datetime

from flask import Flask, jsonify
from flask.templating import render_template
from utils import ChDir, GitDir

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')



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


def read_json_from_cache_file(cache_file):
    with open(cache_file, 'r') as c_file:
        return json.load(c_file)


def write_json_to_cache_file(json_data, cache_file):
    with open(cache_file, 'w+') as c_file:
        c_file.write(json.dumps(json_data))


def get_cached_dirs(base_dir, update_cache):
    """
    Reads a file that is the list of the directories found. This is what we use without refreshing the list
    :return: list of directories
    """

    cache_file = app.config.get('GIT_CACHE_FILE')

    if os.path.isfile(cache_file) and not update_cache:
        return read_json_from_cache_file(cache_file)
    else:
        dir_obj = {'base_dir': base_dir, 'git_dirs': find_git_dirs(base_dir)}
        write_json_to_cache_file(dir_obj, cache_file)
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
            return datetime.fromtimestamp(mtime)
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


@app.route('/config')
def config_file():
    context = {'config': app.config.items()}
    return render_template('config.html', **context)


if __name__ == '__main__':
    app.logger.setLevel(logging.DEBUG)
    app.run(debug=True)
