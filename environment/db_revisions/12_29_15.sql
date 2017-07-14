ALTER TABLE students_completed_courses ADD ge_areas text[];
ALTER TABLE students_completed_courses ADD from_transcript boolean;

ALTER TABLE students_tentative_courses ADD ge_areas text[];
ALTER TABLE students_tentative_courses ADD from_transcript boolean;

ALTER TABLE students_course_equivalences ADD ge_areas text[];
ALTER TABLE students_course_equivalences ADD from_transcript boolean;