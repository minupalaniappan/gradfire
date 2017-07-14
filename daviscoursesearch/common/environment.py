import argparse
import daviscoursesearch.common.config as config
import os
import subprocess
abs_root_path = os.path.abspath(__file__)
config.project_root = os.path.dirname(os.path.dirname(os.path.dirname(abs_root_path)))

config.last_commit_hash = subprocess.check_output('/usr/bin/git show HEAD --pretty=format:"%h" --no-patch', shell=True, cwd=config.project_root).decode('utf-8')
config.logging_dir = os.path.join(config.project_root, 'logs')
config.secret_key = open(os.path.join(config.project_root, 'secret', 'secret_key'), 'rb').read()
config.aws_access_key, config.aws_secret_key = open(os.path.join(config.project_root, 'secret', 'aws_creds'), 'r').read().split(',')
parser = argparse.ArgumentParser()
parser.add_argument('--env')
parser.add_argument('--debug', action='store_true')
args, _ = parser.parse_known_args()


if args.env == 'dev':
    config.db_name = 'dcs_dev'

if args.debug:
    config.debug = True