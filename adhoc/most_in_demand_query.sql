-- spring 2016 classes with >100 seats sorted by time-to-full

SELECT timestamp, tmp.subject, tmp.number, sum(courses.max_enrollment) max_enrollment
  FROM
    (SELECT min(timestamp), courses_enrollment.subject, courses_enrollment.number
    FROM courses_enrollment
    WHERE courses_enrollment.term_year = 2016
    AND courses_enrollment.term_month = 3
    AND courses_enrollment.available_seats = 0
    AND substring(courses_enrollment.number, 2, 1) != '9'
    AND substring(courses_enrollment.number, 1, 1)::integer < 2
    GROUP BY courses_enrollment.subject, courses_enrollment.number
    ORDER BY courses_enrollment.subject, courses_enrollment.number)
    AS tmp(timestamp, subject, number)
  JOIN courses ON courses.subject = tmp.subject AND courses.number = tmp.number
    AND courses.term_year = 2016 AND courses.term_month = 3
WHERE max_enrollment > 100
GROUP BY timestamp, tmp.subject, tmp.number
ORDER BY timestamp;