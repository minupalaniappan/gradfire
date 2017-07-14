import argparse
from daviscoursesearch.common.environment import config
import daviscoursesearch.scraper.storescraper as storescraper
from davislib import Term

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('year')
  parser.add_argument('month')
  args, _ = parser.parse_known_args()

  storescraper.scrape_unknown_isbns_for_stored_term(Term(args.year, args.month))

if __name__ == '__main__':
  main()
