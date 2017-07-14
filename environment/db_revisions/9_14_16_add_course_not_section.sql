ALTER TABLE students_added_courses ADD subject text, ADD number text, ADD title text, ADD term_year int, ADD term_month int;
UPDATE students_added_courses SET
    subject = (SELECT courses.subject FROM courses WHERE courses.id = students_added_courses.course_id),
    number = (SELECT courses.number FROM courses WHERE courses.id = students_added_courses.course_id),
    title = (SELECT courses.title FROM courses WHERE courses.id = students_added_courses.course_id),
    term_year = (SELECT courses.term_year FROM courses WHERE courses.id = students_added_courses.course_id),
    term_month = (SELECT courses.term_month FROM courses WHERE courses.id = students_added_courses.course_id);