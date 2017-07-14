UPDATE courses SET instructor_id = tmp.nrml_id FROM
    (SELECT instructors.id, alt_instr.id FROM instructors
        JOIN (select id, name, regexp_split_to_array(name, '\s') arr from instructors) tmp ON tmp.id = instructors.id and tmp.arr[2] ~ E'[A-Z]\\.' and array_length(tmp.arr, 1) = 3
        JOIN instructors alt_instr ON alt_instr.name = tmp.arr[1] || ' ' || tmp.arr[3]) AS tmp(non_nrml_id, nrml_id)
        WHERE instructor_id = tmp.non_nrml_id;

UPDATE courses_grades SET instructor_id = tmp.nrml_id FROM
    (select instructors.id, alt_instr.id FROM instructors
        JOIN (select id, name, regexp_split_to_array(name, '\s') arr from instructors) tmp ON tmp.id = instructors.id and tmp.arr[2] ~ E'[A-Z]\\.' and array_length(tmp.arr, 1) = 3
        JOIN instructors alt_instr ON alt_instr.name = tmp.arr[1] || ' ' || tmp.arr[3]) AS tmp(non_nrml_id, nrml_id)
    WHERE instructor_id = tmp.non_nrml_id;
delete from instructors where not exists (select 1 from courses where courses.instructor_id = instructors.id) and not exists (select 1 from courses_grades where courses_grades.instructor_id = instructors.id);