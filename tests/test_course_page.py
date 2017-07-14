import logging
import unittest
from io import StringIO
from selenium import webdriver
from daviscoursesearch.flaskapp.utils.db_utils import conn
from daviscoursesearch.common.constants import ACTIVE_TERM
from daviscoursesearch.common.logging import js_exception_logger
from daviscoursesearch.common import config

class TestCoursePage(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.PhantomJS()
        self.driver.set_window_size(1024, 768)

    def tearDown(self):
        self.driver.quit()

    def assertTeachersListHasOptions(self):
        teachers = self.driver.find_element_by_id('teachers').find_elements_by_tag_name('option')
        self.assertGreater(len(teachers), 0)

    def test_active_classes(self):
        query = """SELECT subject, number FROM courses
            WHERE term_year = %s AND term_month = %s
            GROUP BY subject, number
            """
        cur = conn.cursor()
        cur.execute(query, ACTIVE_TERM)
        courses = cur.fetchall()
        for course in courses:
            print(course)
            subject, number = course
            self.driver.get("http://127.0.0.1:5000/search?q={}+{}".format(subject, number))
            self.assertIn(subject, self.driver.title)
            self.assertTeachersListHasOptions()

    def test_submit_question(self):
        pass

    def test_filter_by_teacher(self):
        pass
