CREATE INDEX courses_ge_areas_idx on courses USING GIN (ge_areas);
