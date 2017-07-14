import argparse
from daviscoursesearch.common.environment import config
import daviscoursesearch.scraper.coursescraper as coursescraper
from davislib import Term

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('year')
  parser.add_argument('month')
  parser.add_argument('credentials_file')
  args, _ = parser.parse_known_args()

  username, password = open(args.credentials_file, 'r').read().split()

  coursescraper.scrape_courses_sb(Term(args.year, args.month), username, password)

if __name__ == '__main__':
  main()
