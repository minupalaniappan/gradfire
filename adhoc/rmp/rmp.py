from bs4 import BeautifulSoup
import requests
import re
import json
from urllib.parse import unquote
from os.path import basename

class RateMyProfessor(object):
	INSTRUCTOR_COUNT = 3907
	INSTRUCTOR_LIST_ENDPOINT = 'http://search.mtvnservices.com/typeahead/suggest/'
	INSTRUCTOR_LIST_QUERY = {'solrformat': 'true',
		'q': '*%3A*+AND+schoolid_s%3A1073',
		'defType': 'edismax',
		'qf': 'teacherfullname_t%5E1000+autosuggest',
		'bf': 'pow(total_number_of_ratings_i%2C2.1)',
		'sort': '',
		'siteName': 'rmp',
		'rows': '10',
		'start': '0',
		'fl': 'pk_id+teacherfirstname_t+teacherlastname_t+total_number_of_ratings_i+averageratingscore_rf+schoolid_s',
		'prefix': 'schoolname_t%3A%22University+of+California+Davis%22'}

	INSTRUCTOR_DETAIL_ENDPOINT = 'http://www.ratemyprofessors.com/ShowRatings.jsp'

	INSTRUCTOR_RATINGS_ENDPOINT = 'http://www.ratemyprofessors.com/paginate/professors/ratings'

	@classmethod
	def get_instructors(cls, n=10):
		params = cls.INSTRUCTOR_LIST_QUERY.copy()
		params['rows'] = n

		req = requests.Request('GET', cls.INSTRUCTOR_LIST_ENDPOINT).prepare()
		req.url += '?' + '&'.join(['{}={}'.format(key, value) for key, value in params.items()])
		response = requests.Session().send(req)

		instructors = json.loads(response.text)['response']['docs']

		return instructors

	@classmethod
	def parse_instructor_detail(cls, instructor_id, html):
		soup = BeautifulSoup(html, 'html.parser')
		name = ' '.join([prof.string.strip() for prof in soup.find(class_='profname').children if prof and prof.string.strip()])
		instructor_title = list(soup.find(class_='result-title').children)[0].strip()

		grade_divs = soup.find_all(class_='grade')
		try:
			avg_grade = next(grade.text for grade in grade_divs if re.match(r'[ABCDF][+-]$', grade.text))
		except StopIteration:
			avg_grade = None
		
		hotness_div = next(div for div in grade_divs if div.find('figure'))
		hotness_rating_img_src = hotness_div.find('img').attrs['src']
		hotness_rating = basename(hotness_rating_img_src).split('-chili')[0]

		rating_divs = soup.find(class_='faux-slides').find_all(class_='rating-slider')
		ratings = list(map(lambda div: {
			'label': div.find(class_='label').text,
			'rating': div.find(class_='rating').text
			}, rating_divs))

		tag_elements = soup.find_all(class_='tag-box-choosetags')
		tags = list()
		for tag_ele in tag_elements:
			tag_text, count_ele = list(tag_ele.children)
			tag = tag_text.strip()
			count = count_ele.text[1:-1]
			tags.append({'tag': tag, 'count': int(count)})

		return {
			'rmp_id': instructor_id,
			'name': name,
			'title': instructor_title,
			'avg_grade': avg_grade,
			'hotness': hotness_rating,
			'ratings': ratings,
			'tags': tags
		}


	@classmethod
	def get_instructor_detail(cls, instructor_id):
		resp = requests.get(cls.INSTRUCTOR_DETAIL_ENDPOINT, params={'tid': instructor_id})
		if 'AddRating' in resp.url:
			return None
		
		return cls.parse_instructor_detail(instructor_id, resp.text)

	@classmethod
	def get_instructor_ratings(cls, instructor_id):
		page = 1
		ratings = list()
		resp = requests.get(cls.INSTRUCTOR_RATINGS_ENDPOINT, params={'tid': instructor_id, 'page': page})
		while resp.status_code == 200:
			ratings_page = json.loads(resp.text)['ratings']
			if not ratings_page:
				break
			ratings += ratings_page
			page += 1
			resp = requests.get(cls.INSTRUCTOR_RATINGS_ENDPOINT, params={'tid': instructor_id, 'page': page})

		return ratings
