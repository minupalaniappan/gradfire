UPDATE subjects SET name = 'Med - Intrl: Cardiology' WHERE code = 'CAR';
UPDATE subjects SET name = 'Med - Intrl: Endocrinol &Metab' WHERE code = 'ENM';
UPDATE subjects SET name = 'Med - Intrl: Gastroenterology' WHERE code = 'GAS';
UPDATE subjects SET name = 'Med - Intrl: Infectious Dis' WHERE code = 'IDI';
UPDATE subjects SET name = 'Med - Intrl: Hematology-Oncol' WHERE code = 'HON';
UPDATE subjects SET name = 'Med - Intrl: Cardiology' WHERE code = 'CAR';
UPDATE subjects SET name = 'Med - Intrl: Nephrology' WHERE code = 'NEP';
UPDATE subjects SET name = 'Med - Intrl: Pulmonary' WHERE code = 'PUL';
UPDATE subjects SET name = 'Med - Intrl: General Medicine' WHERE code = 'GMD';
UPDATE subjects SET name = 'Med - Intrl: Clinic Nutr&Metab' WHERE code = 'NCM';
UPDATE subjects SET name = 'Med - Intrl: Emergency Med' WHERE code = 'EMR';


ALTER TABLE subjects ADD is_undergraduate boolean;
UPDATE subjects SET is_undergraduate = (EXISTS
    (SELECT 1 FROM courses WHERE subject = subjects.code
        AND substring(number, 0 ,4)::integer < 200));