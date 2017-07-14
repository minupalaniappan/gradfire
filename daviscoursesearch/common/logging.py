from . import config
from io import StringIO
import json
import logging
import os
import sys
import traceback

exception_logger = logging.getLogger(__name__)
exception_logger.setLevel(logging.ERROR)

exception_log_file = os.path.join(config.logging_dir, config.exception_log_file)
exception_log_handler = logging.FileHandler(exception_log_file)
exception_logger.addHandler(exception_log_handler)
exception_logger.addHandler(logging.StreamHandler(sys.stderr))

js_exception_logger = logging.getLogger(__name__ + '-js')
js_exception_logger.setLevel(logging.ERROR)
js_exception_log_file = os.path.join(config.logging_dir, config.js_exception_log_file)
js_exception_log_handler = logging.FileHandler(js_exception_log_file)
js_exception_log_handler = js_exception_logger.addHandler(js_exception_log_handler)
js_exception_logger.addHandler(logging.StreamHandler(sys.stderr))
from slackclient import SlackClient
sc = SlackClient(config.slack_api_token)

def slack_log_exception(summary):
  ei = sys.exc_info()
  sio = StringIO()
  traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
  exception_text = sio.getvalue()
  sio.close()

  sc.api_call("chat.postMessage",
    channel=config.slack_exception_channel,
    text=json.dumps(summary) + exception_text,
    username='discourse')

def log_js_exception(message, url, linecol, user_id):
    exception_json = json.dumps({
        'message': message,
        'url': url,
        'linecol': linecol,
        'user_id': user_id
    })
    js_exception_logger.error(exception_json)
    if config.db_name == 'dcs_dev':
      sc.api_call("chat.postMessage",
          channel=config.slack_exception_channel,
          text=exception_json,
          username='discourse')

