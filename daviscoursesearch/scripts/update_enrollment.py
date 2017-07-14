import argparse
from daviscoursesearch.common.environment import config
import daviscoursesearch.scraper.enrollment_scraper as enrollment_scraper
from davislib import Term

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('year')
  parser.add_argument('month')
  parser.add_argument('credentials_file')
  args, _ = parser.parse_known_args()

  username, password = open(args.credentials_file, 'r').read().split()

  enrollment_scraper.scrape_enrollment(Term(args.year, args.month), (username, password))

if __name__ == '__main__':
  main()
