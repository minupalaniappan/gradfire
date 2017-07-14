import daviscoursesearch.scraper.coursescraper as cs
from davislib import Term

TERM_MONTHS = ['10', '05', '06', '07', '03', '01']
for year in range(2008, 2016):
  for month in TERM_MONTHS:
    print('Scraping {} {}'.format(year, month))
    cs.scrape_course_detail(Term(year, month))

