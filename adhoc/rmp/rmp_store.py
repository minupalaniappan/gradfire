from rmp import RateMyProfessor as rmp
import json
import psycopg2
conn = psycopg2.connect("dbname=davis_course_search")
conn.autocommit = True

def store_instructor_detail(detail, ratings):
	detail['rating_averages'] = [(rating['label'], rating['rating']) for rating in detail['ratings']]
	detail['ratings'] = json.dumps(ratings)
	detail['tags'] = [(tag['tag'], tag['count']) for tag in detail['tags']]

	cur = conn.cursor()
	cur.execute("""INSERT INTO rmp_instructors (rmp_id, name, title, avg_grade, hotness, rating_averages, ratings, tags) 
		VALUES 
		(%(rmp_id)s, %(name)s, %(title)s, %(avg_grade)s, %(hotness)s, %(rating_averages)s, %(ratings)s, %(tags)s)
		""", detail)

def update_instructor_with_ratings(rmp_id, ratings):
	cur = conn.cursor()
	cur.execute("UPDATE rmp_instructors SET ratings = %s WHERE rmp_id = %s", (json.dumps(ratings), rmp_id))

def store_rmp_professors():
	instructors = rmp.get_instructors(n=3908)
	for instructor in instructors:
		detail = rmp.get_instructor_detail(instructor['pk_id'])
		if not detail:
			continue

		ratings = []
		if instructor['total_number_of_ratings_i'] > 0:
			ratings = rmp.get_instructor_ratings(instructor['pk_id'])

		try:
			store_instructor_detail(detail, ratings)
		except psycopg2.IntegrityError:
			update_instructor_with_ratings(instructor['pk_id'], ratings)

if __name__ == '__main__':
	store_rmp_professors()
