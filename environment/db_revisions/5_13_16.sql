CREATE INDEX courses_prereq_req_reference ON courses_prerequisites(req_subject, req_number);
CREATE INDEX course_term_specific ON courses(term_year, term_month, subject, number);