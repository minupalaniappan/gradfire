"""
Look up  using Amazon Product Advertising API
"""

import xml.etree.ElementTree as etree
import xmltodict
import hashlib, hmac, base64
import json
import requests
import urllib.parse
from datetime import datetime
from ...common.config import aws_access_key, aws_secret_key, amzn_associate_tag
from .merchants import book_id_for_isbn

AMZN_API_ENDPOINT = "http://webservices.amazon.com/onca/xml"
SIGNATURE_HEADER = """GET
webservices.amazon.com
/onca/xml
"""
AMZN_XML_NAMESPACES = {
  # flag for xmltodict indicating to strip the namespace from tags
  "http://webservices.amazon.com/AWSECommerceService/2011-08-01": None
}

def generate_signature(params):
  sorted_param_list = list()
  for k, v in sorted(params.items(), key=lambda item: item[0]):
    sorted_param_list.append('{}={}'.format(k, urllib.parse.quote_plus(v)))

  encoded_param_list = SIGNATURE_HEADER + '&'.join(sorted_param_list)
  hmac_params = hmac.new(aws_secret_key.encode('utf-8'), encoded_param_list.encode('utf-8'), hashlib.sha256).digest()
  return str(base64.b64encode(hmac_params), 'utf-8')

def amazon_isbn_lookup(isbn, response_group):
  parameters = {
    'Service': 'AWSECommerceService',
    'Operation': 'ItemLookup',
    'ResponseGroup': response_group,
    'SearchIndex': 'All',
    'IdType': 'ISBN',
    'ItemId': isbn,
    'AWSAccessKeyId': aws_access_key,
    'AssociateTag': amzn_associate_tag,
    'Timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
  }
  parameters['Signature'] = generate_signature(parameters)

  resp = requests.get(AMZN_API_ENDPOINT, params=parameters)
  parsed_resp = xmltodict.parse(resp.text, process_namespaces=True, namespaces=AMZN_XML_NAMESPACES)
  return parsed_resp

def first_item_for_response(resp):
    item = resp['ItemLookupResponse']['Items']['Item']
    if isinstance(item, list):
      return item[0]
    else:
      return item

def offers_for_isbn(isbn):
  resp = amazon_isbn_lookup(isbn, 'Large')
  try:
    item = first_item_for_response(resp)
  except KeyError:
    return None

  offers_url = item['Offers']['MoreOffersUrl']
  offers_url = urllib.parse.unquote(offers_url)
  offer_summary = item['OfferSummary']
  new_price = offer_summary.get('LowestNewPrice')
  used_price = offer_summary.get('LowestUsedPrice')
  offer_base = {
    'merchant': 'amzn',
    'listings_url': offers_url,
    'book_id': book_id_for_isbn(isbn),
    'merchant_metadata': json.dumps(item) # temp solution; should be stored in normalized format in courses_textbooks instead of textbooks_offers
  }

  offers = list()
  if new_price:
    new_offer = offer_base.copy()
    new_offer['condition'] = 'new'
    new_offer['price_with_shipping'] = new_price['Amount']
    offers.append(new_offer)
  if used_price:
    used_offer = offer_base.copy()
    used_offer['condition'] = 'used'
    used_offer['price_with_shipping'] = used_price['Amount']
    offers.append(used_offer)

  return offers

def item_attributes_for_isbn(isbn):
  resp = amazon_isbn_lookup(isbn, 'ItemAttributes')
  return first_item_for_response(resp)
