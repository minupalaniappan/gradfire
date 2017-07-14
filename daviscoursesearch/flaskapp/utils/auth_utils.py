import base64
import os
from passlib.hash import pbkdf2_sha512, sha256_crypt
from passlib.utils import ab64_decode
from ...common.config import remember_me_expiration

def salt_and_checksum_text(text, salt_text=None):
  salt = None
  if salt_text:
    salt = ab64_decode(salt_text.encode('utf-8'))

  hash_ = pbkdf2_sha512.encrypt(text, salt=salt)
  digest, rounds, salt, checksum = hash_[1:].split('$')
  return (salt, checksum)

def session_token_checksum(token):
  hash_ = sha256_crypt.encrypt(token, rounds=15000, salt='')
  digest, rounds, salt, checksum = hash_[1:].split('$')
  return checksum

def random_base64_string():
  return str(base64.b64encode(os.urandom(8)), 'utf-8')