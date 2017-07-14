SELECT * FROM courses
  WHERE (
    (WITH RECURSIVE prereq_satisfied AS (
  SELECT 0, parent_req, array_agg(sts) child_satisfactions FROM

    (SELECT DISTINCT ON (id) cp.*, (scc.course_id IS NOT NULL) sts FROM courses_prerequisites cp
    LEFT JOIN courses c ON c.subject = cp.subject AND c.number = cp.number
    LEFT JOIN students_completed_courses scc ON student_id = 1 AND scc.course_id = c.id
    WHERE cp.course_id = courses.id AND cp.rel IS NULL ORDER BY id, sts DESC) course_satisfaction

  GROUP BY parent_req
  UNION
  SELECT id, cp.parent_req,
    ARRAY[((cp.rel = 'AND' AND true = all(ps.child_satisfactions))
      OR cp.rel = 'OR' AND true = any(ps.child_satisfactions))]::boolean[]
  FROM prereq_satisfied ps
  JOIN courses_prerequisites cp ON ps.parent_req = cp.id
  WHERE cp.parent_req IS NOT NULL)

  SELECT (true = ALL(array_agg(child_satisfactions)))
  FROM
    (SELECT parent_req, unnest(child_satisfactions) FROM prereq_satisfied)
    ps(parent_req, child_satisfactions)
  WHERE parent_req = (SELECT id FROM courses_prerequisites WHERE course_id = courses.id AND parent_req IS NULL)
  GROUP BY parent_req) = true or NOT EXISTS (SELECT 1 FROM courses_prerequisites WHERE course_id = courses.id))
 AND id = 142483;