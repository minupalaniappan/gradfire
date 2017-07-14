import argparse
from daviscoursesearch.common.environment import config
# hello
parser = argparse.ArgumentParser()
parser.add_argument('--host')
parser.add_argument('--port')
args, _ = parser.parse_known_args()

if args.host:
  config.host = args.host

if args.port:
  config.port = int(args.port)

import daviscoursesearch.flaskapp.root as root
root.app.run(host=config.host, port=config.port)
