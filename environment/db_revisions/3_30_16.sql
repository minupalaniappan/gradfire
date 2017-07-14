ALTER TABLE instructors ADD name_components text[];
UPDATE instructors SET name_components = regexp_split_to_array(lower(name), E'\\\s+');
CREATE INDEX name_component_index ON instructors USING gin (name_components);
