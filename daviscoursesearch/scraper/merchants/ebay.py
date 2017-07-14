from .merchants import MerchantApi
from ...common.config import EBAY_APP_ID, EBAY_TRACKING_ID
import json
import requests

EBAY_NEW_FILTER = {
  'itemFilter(1).value(0)': 'New',
  'itemFilter(1).value(1)': '2000',
  'itemFilter(1).value(2)': '2500'
}

EBAY_USED_FILTER = {
  'itemFilter(1).value(0)': 'Used'
}

EBAY_USED_LOWER_BOUND = 3000
class EbayApi(MerchantApi):
  API_ENDPOINT = 'http://svcs.ebay.com/services/search/FindingService/v1'

  API_PARAMS = {
    'OPERATION-NAME': 'findItemsByProduct',
    'SERVICE-VERSION': '1.0.0',
    'SECURITY-APPNAME': EBAY_APP_ID,
    'RESPONSE-DATA-FORMAT': 'JSON',
    'productId.@type': 'ISBN',
    'sortOrder': 'PricePlusShippingLowest',
    'affiliate.networkId': 9,
    'affiliate.trackingId': EBAY_TRACKING_ID,
    'itemFilter(0).name': 'ListingType',
    'itemFilter(0).value(0)': 'FixedPrice'
  }

  @classmethod
  def _listings_with_params(cls, params):
    r = requests.get(cls.API_ENDPOINT, params=params)
    print(params)
    print(r.text)
    return json.loads(r.text)['findItemsByProductResponse']

  @classmethod
  def lookup_isbn(cls, isbn):
    params = cls.API_PARAMS.copy()
    params['productId'] = isbn
    params['itemFilter(1).name'] = 'Condition'

    params.update(EBAY_USED_FILTER)
    used_listings = cls._listings_with_params(params)

    params.update(EBAY_NEW_FILTER)
    new_listings = cls._listings_with_params(params)

    return used_listings

class HalfApi(EbayApi):
  def lookup_isbn(self):
    pass

  def lookup_isbns(self):
    pass

