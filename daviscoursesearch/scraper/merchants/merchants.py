from ...flaskapp.utils.db_utils import conn as db_conn
from datetime import datetime
from decimal import Decimal
import json
import psycopg2
import requests

class MerchantApi(object):
  def lookup_isbn(self, isbn):
    pass

  def lookup_isbns(self, isbns):
    pass

def store_offer(offer):
  cur = db_conn.cursor()

  offer['rental_id'] = None
  if offer.get('term_days'):
    cur.execute("""INSERT INTO textbooks_rentals (term_days) VALUES (%s)
      RETURNING id""", offer['rental_term_days'])
    offer['rental_id'] = cur.fetchone()[0]

  offer['updated'] = datetime.now()
  try:
    cur.execute("""INSERT INTO textbooks_offers
      (book_id, merchant, rental_id, price_with_shipping, listings_url, condition, merchant_metadata, updated)
      VALUES (%(book_id)s, %(merchant)s,
        %(rental_id)s, %(price_with_shipping)s,
        %(listings_url)s, %(condition)s, %(merchant_metadata)s, %(updated)s)""", offer)
  except psycopg2.IntegrityError:
    cur.execute("""UPDATE textbooks_offers
      SET rental_id = %(rental_id)s, price_with_shipping = %(price_with_shipping)s,
      listings_url = %(listings_url)s, condition = %(condition)s, updated = %(updated)s, merchant_metadata = %(merchant_metadata)s
      WHERE book_id = %(book_id)s AND merchant = %(merchant)s
        AND condition = %(condition)s""", offer)

def book_id_for_isbn(isbn):
  cur = db_conn.cursor()
  cur.execute("SELECT id FROM courses_textbooks WHERE isbn = %s", (isbn,))
  try:
    return cur.fetchone()[0]
  except TypeError:
    return None