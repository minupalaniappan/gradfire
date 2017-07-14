from flask import request
MAX_GRADE_VIEWS = 3
def show_grade_distrib(grade_views):
  grade_views = int(request.cookies.get('grade_views', 0))

  return grade_views <= MAX_GRADE_VIEWS
