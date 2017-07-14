from ...common.config import chegg_credentials
from .merchants import MerchantApi
import requests
import json
from decimal import Decimal

def chegg_offers_for_isbn(isbn):
  chg = CheggRentalApi(chegg_credentials['api_key'], chegg_credentials['password'])
  return chg.lookup_isbn(isbn)

class CheggApiError(Exception):
  pass

class CheggRentalApi(MerchantApi):
  ENDPOINT = 'http://api.chegg.com/rent.svc'

  def __init__(self, api_key, password):
    self.api_key = api_key
    self.password = password
    self.COMMON_PARAMS = {'KEY': api_key,
      'PW': self.password,
      'R': 'JSON',
      'V': '2.0',
      'with_pids': 1}

  def lookup_isbn(self, isbn):
    """
    Look up a single ISBN
    """
    return self.lookup_isbns([isbn])

  def lookup_isbns(self, isbns):
    """
    A single API to call to look up many ISBNs.
    """
    params = self.COMMON_PARAMS.copy()
    params['isbn'] = ','.join(isbns)
    resp = requests.get(CheggRentalApi.ENDPOINT, params=params)

    json_resp = json.loads(resp.text)
    if json_resp['Error'] == False:
      return normalize_offers(json_resp['Data']['Items'])
    else:
      raise CheggApiError(json_resp['ErrorMessage'])

  def normalize_offers(self, offers):
    offers_nrml = list()
    for offer in filter(lambda offer: offer['Renting'], offers):
      shipping_price = min(offer['ShippingPrices'], key=lambda price: float(price['cost_each']))['cost_each']
      price_with_shipping = str(Decimal(offer['BookInfo']['ListPrice']) + Decimal(shipping_price))
      quarter_term = next(term for term in offer['Terms'] if term['term'] == 'QUARTER')
      offer_fields = {
        'product_id': None,
        'price_with_shipping': str(Decimal(quarter_term['price']) + Decimal(shipping_price)),
        'list_price': quarter_term['price'],
        'merchant': 'chegg',
        'is_rental': True,
        'term_days': quarter_term['term_days']
      }
      offers_nrml.append(offer_fields)

    return offers_nrml


# def store_offers_for_isbn(isbn):
#   book_id = book_id_for_isbn(isbn)
#   chg = CheggRentalApi(chegg_credentials['api_key'], chegg_credentials['password'])
#   offers = chg.lookup_isbn(isbn)
#   for offer in offers:
#     import ipdb; ipdb.set_trace()
#     shipping_price = min(offer['ShippingPrices'], key=lambda price: float(price['cost_each']))['cost_each']
#     price_with_shipping = str(Decimal(offer['BookInfo']['ListPrice']) + Decimal(shipping_price))
#     offer_fields = {
#       'book_id': book_id,
#       'product_id': None,
#       'price_with_shipping': price_with_shipping,
#       'list_price': offer['BookInfo']['ListPrice'],
#       'merchant': 'chegg'
#     }

#     if offer['Renting']:
#       quarter_term = next(term for term in offer['Terms'] if term['term'] == 'QUARTER')
#       offer_fields['term_days'] = quarter_term['term_days']
#       offer_fields['list_price'] = quarter_term['price']
#       offer_fields['price_with_shipping'] = str(Decimal(quarter_term['price']) + Decimal(shipping_price))
#       store_offer(offer_fields)
