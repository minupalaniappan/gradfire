from collections import OrderedDict
from itertools import chain
from .subjects_by_keyword import SUBJECTS_BY_KEYWORD
import datetime

MAX_GRADE_VIEWS = 3
USER_ROLES = ['student', 'employee']
REGISTRATION_START_DATES_BY_TERM = {
    (2016, 1): datetime.date(2015, 11, 2),
    (2016, 3): datetime.date(2016, 2, 1),
    (2016, 5): datetime.date(2016, 4, 25),
    (2016, 6): datetime.date(2016, 4, 25),
    (2016, 7): datetime.date(2016, 4, 25),
    (2016, 10): datetime.date(2016, 5, 9)
}

PRETTY_MEETING_TYPE_BY_CODE = {
  'LEC': 'Lecture',
  'L/D': 'Lab/Discussion',
  'LAB': 'Lab',
  'WRK': 'Work',
  'LIS': 'Listening',
  'DIS': 'Discussion',
  'F-V': 'Film Viewing',
  'REC': 'Recording',
  'PRJ': 'Project',
  'SEM': 'Seminar',
  'TUT': 'Tutorial'
}
INSTRUCTION_START_DATES_BY_TERM = {
    (2016, 10): datetime.datetime(2016, 9, 21)
}

INSTRUCTION_END_DATES_BY_TERM = {
    (2016, 10): datetime.datetime(2016, 12, 3)
}

DROP_DEADLINE_BY_TERM = {
    (2016, 1): datetime.date(2016, 2, 1),
    (2016, 3): datetime.date(2016, 4, 22),
    (2016, 10): datetime.date(2016, 10, 18)
}
MAX_TERM = (2016, 10) # can this be autopopulated at startup from db?
ACTIVE_TERM = (2016, 10) # default term for search
CURRENT_TERM = (2016, 10) # term for courses currently being taught
LOWEST_TERM = (2008, 1)

PRETTY_SESSION_BY_MONTH = {
    1: 'Winter',
    3: 'Spring',
    5: 'Summer Session 1',
    6: 'Summer Special',
    7: 'Summer Session 2',
    10: 'Fall'
}

SUBJECTS = ['AAS', 'ABG', 'ABI', 'ABS', 'ABT', 'ACC', 'AED', 'AGC', 'AGE', 'AGR', 'AHI', 'AMR', 'AMS', 'ANB', 'ANE', 'ANG', 'ANS', 'ANT', 'APC', 'ARB', 'ARE', 'ART', 'ASA', 'ASE', 'AST', 'ATM', 'AVS', 'BCB', 'BCM', 'BIM', 'BIS', 'BIT', 'BMB', 'BPH', 'BPT', 'BST', 'CAN', 'CAR', 'CDB', 'CEL', 'CGS', 'CHA', 'CHE', 'CHI', 'CHN', 'CLA', 'CLH', 'CLR', 'CMH', 'CMN', 'CNE', 'CNS', 'COM', 'CPS', 'CRD', 'CRI', 'CRO', 'CSM', 'CST', 'CTS', 'DAN', 'DEB', 'DER', 'DES', 'DRA', 'DVM', 'EAD', 'EAE', 'EAL', 'EAP', 'EAS', 'EBS', 'ECH', 'ECI', 'ECL', 'ECM', 'ECN', 'ECS', 'EDO', 'EDU', 'EEC', 'EJS', 'EME', 'EMR', 'EMS', 'ENG', 'ENH', 'ENL', 'ENM', 'ENP', 'ENT', 'EPI', 'EPP', 'ERS', 'ESM', 'ESP', 'EST', 'ETX', 'EVE', 'EXB', 'EXS', 'FAP', 'FMS', 'FOR', 'FPS', 'FRE', 'FRS', 'FSM', 'FST', 'GAS', 'GDB', 'GEL', 'GEO', 'GER', 'GGG', 'GMD', 'GRK', 'HDE', 'HEB', 'HIN', 'HIS', 'HMR', 'HNR', 'HON', 'HPH', 'HPS', 'HRT', 'HUM', 'HUN', 'HYD', 'IAD', 'ICL', 'IDI', 'IMD', 'IMM', 'IPM', 'IRE', 'IST', 'ITA', 'JPN', 'JST', 'LAH', 'LAT', 'LAW', 'LDA', 'LIN', 'MAE', 'MAT', 'MCB', 'MCP', 'MDI', 'MDS', 'MGB', 'MGP', 'MGT', 'MHI', 'MIB', 'MIC', 'MMI', 'MPH', 'MPM', 'MPS', 'MSA', 'MSC', 'MST', 'MUS', 'NAC', 'NAS', 'NCM', 'NEM', 'NEP', 'NEU', 'NGG', 'NPB', 'NRS', 'NSC', 'NSU', 'NUB', 'NUT', 'OBG', 'OEH', 'OPT', 'OSU', 'OTO', 'PAS', 'PBG', 'PBI', 'PED', 'PFS', 'PGG', 'PHA', 'PHE', 'PHI', 'PHR', 'PHY', 'PLB', 'PLP', 'PLS', 'PMD', 'PMI', 'PMR', 'POL', 'POM', 'POR', 'PPP', 'PSC', 'PSU', 'PSY', 'PTX', 'PUL', 'RAL', 'RDI', 'REL', 'RMT', 'RNU', 'RON', 'RST', 'RUS', 'SAF', 'SAS', 'SOC', 'SPA', 'SPH', 'SSC', 'STA', 'STH', 'STP', 'STS', 'SUR', 'TCS', 'TSK', 'TTP', 'TXC', 'URD', 'URO', 'UWP', 'VCR', 'VEN', 'VET', 'VMB', 'VMD', 'VME', 'VSR', 'WFB', 'WFC', 'WLD', 'WMS']

SUBJECT_CODES_BY_NAME = {
    'African American & African Std': 'AAS',
    'Agric Mngt & Range Resources': 'AMR',
    'Agricultural & Envir Chem Grad': 'AGC',
    'Agricultural & Resource Econ': 'ARE',
    'Agricultural Economics': 'AGE',
    'Agricultural Education': 'AED',
    'Agricultural Systems & Envir': 'ASE',
    'Agronomy': 'AGR',
    'American Studies': 'AMS',
    'Animal Behavior (Graduate Gp)': 'ANB',
    'Animal Biology': 'ABI',
    'Animal Biology Grad Gp': 'ABG',
    'Animal Genetics': 'ANG',
    'Animal Science': 'ANS',
    'Anthropology': 'ANT',
    'Applied Behavioral Sciences': 'ABS',
    'Applied Biological System Tech': 'ABT',
    'Arabic': 'ARB',
    'Art History': 'AHI',
    'Art Studio': 'ART',
    'Asian American Studies': 'ASA',
    'Astronomy': 'AST',
    'Atmospheric Science': 'ATM',
    'Avian Sciences': 'AVS',
    'Bio, Molec, Cell, Dev Bio GG': 'BCB',
    'Biochemistry & Molec Biol Grad': 'BMB',
    'Biological Sciences': 'BIS',
    'Biophotonics': 'BPT',
    'Biophysics (Graduate Group)': 'BPH',
    'Biostatistics': 'BST',
    'Biotechnology': 'BIT',
    'Biotechnology (Desig Emphasis)': 'DEB',
    'Cantonese': 'CAN',
    'Cell & Developmental Biol Grad': 'CDB',
    'Celtic': 'CEL',
    'Chemistry': 'CHE',
    'Chicano Studies': 'CHI',
    'Chinese': 'CHN',
    'Cinema & Technocultural Stud': 'CTS',
    'Cinema and Digital Media': 'CDM',
    'Classics': 'CLA',
    'Clinical Research': 'CLH',
    'Colleges at La Rue': 'CLR',
    'Cognitive Science': 'CGS',
    'Communication': 'CMN',
    'Community & Regional Develpmnt': 'CRD',
    'Comparative Literature': 'COM',
    'Consumer Economics': 'CNE',
    'Consumer Sciences': 'CNS',
    'Critical Theory (Desig Emphas)': 'CRI',
    'Croatian': 'CRO',
    'Crop Science & Management': 'CSM',
    'Cultural Studies': 'CST',
    'Danish': 'DAN',
    'Design': 'DES',
    'Dramatic Art': 'DRA',
    'East Asian Studies': 'EAS',
    'Ecology': 'ECL',
    'Economics': 'ECN',
    'Economy, Justice & Society': 'EJS',
    'Education': 'EDU',
    'Education Abroad Program': 'EAP',
    'Endocrinology (Graduate Group)': 'EDO',
    'Engineering': 'ENG',
    'Engineering Aerospace Sci': 'EAE',
    'Engineering Applied Sci-Davis': 'EAD',
    'Engineering Applied Sci-Lvrmor': 'EAL',
    'Engineering Biological Systems': 'EBS',
    'Engineering Biomedical': 'BIM',
    'Engineering Chemical': 'ECH',
    'Engineering Chemical-Materials': 'ECM',
    'Engineering Civil & Environ': 'ECI',
    'Engineering Computer Science': 'ECS',
    'Engineering Electrical & Compu': 'EEC',
    'Engineering Materials Science': 'EMS',
    'Engineering Mechanical': 'EME',
    'Engineering Mechanical & Aero': 'MAE',
    'English': 'ENL',
    'Entomology': 'ENT',
    'Environmental Horticulture': 'ENH',
    'Environmental Plan & Managemnt': 'ENP',
    'Environmental Resource Science': 'ERS',
    'Environmental Sci & Management': 'ESM',
    'Environmental Science & Policy': 'ESP',
    'Environmental Studies': 'EST',
    'Environmental Toxicology': 'ETX',
    'Epidemiology (Graduate Group)': 'EPI',
    'Evolution and Ecology': 'EVE',
    'Exercise Biology': 'EXB',
    'Exercise Science': 'EXS',
    'Fiber And Polymer Science': 'FPS',
    'Film Studies': 'FMS',
    'Food Science & Technology': 'FST',
    'Food Service Management': 'FSM',
    'Forensic Science': 'FOR',
    'French': 'FRE',
    'Freshman Seminar': 'FRS',
    'Genetics (Graduate Group)': 'GGG',
    'Geography': 'GEO',
    'Geology': 'GEL',
    'German': 'GER',
    'Global Disease Biology': 'GDB',
    'Greek': 'GRK',
    'Health Informatics': 'MHI',
    'Hebrew': 'HEB',
    'Hindi/Urdu': 'HIN',
    'History': 'HIS',
    'History & Philosophy of Sci.': 'HPS',
    'Honors Challenge': 'HNR',
    'Horticulture': 'HRT',
    'Human Development': 'HDE',
    'Human Rights': 'HMR',
    'Humanities': 'HUM',
    'Hungarian': 'HUN',
    'Hydrologic Science': 'HYD',
    'Immunology (Graduate Group)': 'IMM',
    'Integrated Pest Management': 'IPM',
    'Integrated Studies': 'IST',
    'International Agricultural Dev': 'IAD',
    'International Commercial Law': 'ICL',
    'International Relations': 'IRE',
    'Italian': 'ITA',
    'Japanese': 'JPN',
    'Jewish Studies': 'JST',
    'Landscape Architecture': 'LDA',
    'Latin': 'LAT',
    'Latin American & Hemispheric': 'LAH',
    'Law': 'LAW',
    'Linguistics': 'LIN',
    'Management': 'MGT',
    'Management Work Prof Bay Area': 'MGB',
    'Management Working Professionl': 'MGP',
    'Master of Public Health': 'MPH',
    'Math & Physical Sci': 'MPS',
    'Mathematics': 'MAT',
    'Med - Anesthesiology': 'ANE',
    'Med - Biological Chemistry': 'BCM',
    'Med - Cell Biol & Human Anat': 'CHA',
    'Med - Clinical Psychology': 'CPS',
    'Med - Community & Intl Health': 'CMH',
    'Med - Dermatology': 'DER',
    'Med - Epidemiology & Prev Med': 'EPP',
    'Med - Family Practice': 'FAP',
    'Med - Human Physiology': 'HPH',
    'Med - Internal Medicine': 'IMD',
    'Med - Intrl: Cardiology': 'CAR',
    'Med - Intrl: Clinic Nutr&Metab': 'NCM',
    'Med - Intrl: Emergency Med': 'EMR',
    'Med - Intrl: Endocrinol &Metab': 'ENM',
    'Med - Intrl: Gastroenterology': 'GAS',
    'Med - Intrl: General Medicine': 'GMD',
    'Med - Intrl: Hematology-Oncol': 'HON',
    'Med - Intrl: Infectious Dis': 'IDI',
    'Med - Intrl: Nephrology': 'NEP',
    'Med - Intrl: Pulmonary': 'PUL',
    'Med - Medical Microbiology': 'MMI',
    'Med - Medical Pharmacol &Toxic': 'PHA',
    'Med - Medical Science': 'MDS',
    'Med - Neurology': 'NEU',
    'Med - Neurosurgery': 'NSU',
    'Med - Obstetrics & Gynecology': 'OBG',
    'Med - Occupational &Envrn Hlth': 'OEH',
    'Med - Ophthalmology': 'OPT',
    'Med - Orthopaedic Surgery': 'OSU',
    'Med - Otolaryngology': 'OTO',
    'Med - Pathology': 'PMD',
    'Med - Pediatrics': 'PED',
    'Med - Physical Medicine &Rehab': 'PMR',
    'Med - Plastic Surgery': 'PSU',
    'Med - Psychiatry': 'PSY',
    'Med - Public Health Sciences': 'SPH',
    'Med - Radiation Oncology': 'RON',
    'Med - Radiology (Diagnostic)': 'RDI',
    'Med - Radiology-Nuclear Med': 'RNU',
    'Med - Rheumatology (Allergy)': 'RAL',
    'Med - Surgery': 'SUR',
    'Med - Urology': 'URO',
    'Medical Informatics': 'MDI',
    'Medieval Studies': 'MST',
    'Microbiology': 'MIC',
    'Microbiology (Graduate Group)': 'MIB',
    'Middle East/South Asian Std': 'MSA',
    'Military Science': 'MSC',
    'Molecular and Cellular Biology': 'MCB',
    'Molecular, Cell & Int Physio': 'MCP',
    'Music': 'MUS',
    'Native American Studies': 'NAS',
    'Nature and Culture': 'NAC',
    'Nematology': 'NEM',
    'Neurobiology, Physio & Behavior': 'NPB',
    'Neuroscience (Graduate Group)': 'NSC',
    'Nursing': 'NRS',
    'Nutrition': 'NUT',
    'Nutrition Graduate Group': 'NGG',
    'Nutritional Biology (Grad Grp)': 'NUB',
    'Performance Studies (Grad Grp)': 'PFS',
    'Pharmacology-Toxicology (Grad)': 'PTX',
    'Philosophy': 'PHI',
    'Physical Education': 'PHE',
    'Physician Assistant Studies': 'PAS',
    'Physics': 'PHY',
    'Physiology Graduate Group': 'PGG',
    'Plant Biology': 'PLB',
    'Plant Biology (Graduate Group)': 'PBI',
    'Plant Pathology': 'PLP',
    'Plant Protection & Pest Mangmt': 'PPP',
    'Plant Science': 'PLS',
    'Political Science': 'POL',
    'Pomology': 'POM',
    'Population Biology': 'PBG',
    'Portuguese': 'POR',
    'Professional Accountancy': 'ACC',
    'Psychology': 'PSC',
    'Range Science': 'RMT',
    'Religious Studies': 'RST',
    'Russian': 'RUS',
    'School of Veterinary Medicine': 'VET',
    'Science & Technology Studies': 'STS',
    'Science and Society': 'SAS',
    'Short-Term Abroad Program': 'STP',
    'Social Theory & Compar History': 'STH',
    'Sociology': 'SOC',
    'Soil Science': 'SSC',
    'Spanish': 'SPA',
    'Statistics': 'STA',
    'Study of Religion': 'REL',
    'Sustainable Ag & Food Sys': 'SAF',
    'Technocultural Studies': 'TCS',
    'Textiles & Clothing': 'TXC',
    'Transportation Tech & Policy': 'TTP',
    'Turkish': 'TSK',
    'University Writing Program': 'UWP',
    'Urdu': 'URD',
    'Vegetable Crops': 'VCR',
    'Veterinary Clinical Rotation': 'DVM',
    'Veterinary Medicine': 'VMD',
    'Viticulture & Enology': 'VEN',
    'VM Anatomy, Physiol & Cell Bio': 'APC',
    'VM Medicine and Epidemiology': 'VME',
    'VM Molecular Biosciences': 'VMB',
    'VM Pathology, Microbiol &Immun': 'PMI',
    'VM Population Health & Reprod': 'PHR',
    'VM Preventive Veterinary Med': 'MPM',
    'VM Surgical & Radiological Sci': 'VSR',
    'Wildlife, Fish & Conserv Biol': 'WFC',
    'Women\'s Studies': 'WMS',
    'Workload': 'WLD'
}

SUBJECT_NAMES_BY_CODE = {v: k for k,v in SUBJECT_CODES_BY_NAME.items()}

CONJUNCTIONS = ['and']

TERM_SESSION_BY_MONTH = {
    1: 'winter',
    3: 'spring',
    5: 'summer-1',
    6: 'summer-special',
    7: 'summer-2',
    10: 'fall'
}

TERM_MONTH_BY_SESSION = {v: k for k, v in TERM_SESSION_BY_MONTH.items()}

SEARCH_TERM_MONTH_BY_KWS = [
    ('ss 1', 5),
    ('ss special', 6),
    ('ss 2', 7),
    ('ss1', 5),
    ('ss2', 7),
    ('summer session 1', 5),
    ('summer special', 6),
    ('summer session 2', 7),
    ('summer 1', 5),
    ('summer special', 6),
    ('summer 2', 7),
    ('summer', 5) # just 'summer' will default to summer session 1; order matters for this one
]
SEARCH_TERM_MONTH_BY_KWS = OrderedDict(SEARCH_TERM_MONTH_BY_KWS)

MEETING_DAYS_BY_CHAR = {
    'M': 'monday',
    'T': 'tuesday',
    'W': 'wednesday',
    'R': 'thursday',
    'F': 'friday',
    'S': 'saturday'
}

CAT_MINIMUMS = {'Topical Breadth': 52,
                'Core Literacies': 27} # 35 is actual, but english req differs by college and is not supported yet

CAT_HAS_EXACT_MINIMUM = {
    'Topical Breadth': False,
    'Core Literacies': True
}

AREA_MINIMUMS = {
    'Topical Breadth': 52,
    'Arts & Humanities': 12,
    'Science & Engineering': 12,
    'Social Sciences': 12,
    # 'English Composition': 8, (this requirement differs by college)
    'Writing Experience': 6,
    'Oral Literacy': 3,
    'Visual Literacy': 3,
    'American Cultures, Governance & History': 6,
    'Domestic Diversity': 3,
    'World Cultures': 3,
    'Quantitative Literacy': 3,
    'Scientific Literacy': 3
}

GE_CATEGORIES = [
    'Topical Breadth',
    'Core Literacies'
]

GE_AREAS_BY_CATEGORY = {
    'Topical Breadth': [
        'Arts & Humanities',
        'Science & Engineering',
        'Social Sciences'],
    'Core Literacies': [
       # 'English Composition', (this requirement differs by college)
       'Writing Experience',
       'Oral Literacy',
       'Visual Literacy',
       'American Cultures, Governance & History',
       'Domestic Diversity',
       'World Cultures',
       'Quantitative Literacy',
       'Scientific Literacy']
}

GE_AREAS = list(chain(*GE_AREAS_BY_CATEGORY.values()))

GE_AREA_SHORTNAMES = {
    'American Cultures, Governance & History': 'ACG&H'
}
QUERY_TIMEOUT = 15

GE_AREAS_BY_OASIS_ABBRV = OrderedDict([
    ('AH', 'Arts & Humanities'),
    ('SE', 'Science & Engineering'),
    ('SS', 'Social Sciences'),
    ('WE', 'Writing Experience'),
    ('OL', 'Oral Literacy'),
    ('VL', 'Visual Literacy'),
    ('ACGH', 'American Cultures, Governance & History'),
    ('DD', 'Domestic Diversity'),
    ('WC', 'World Cultures'),
    ('QL', 'Quantitative Literacy'),
    ('SL', 'Scientific Literacy')
])

GRADE_ORDER_BY_LETTER = [
  ('A+', 1),
  ('A', 2),
  ('A-', 3),
  ('B+', 4),
  ('B', 5),
  ('B-', 6),
  ('C+', 7),
  ('C', 8),
  ('C-', 9),
  ('D+', 10),
  ('D', 11),
  ('D-', 12),
  ('F', 13),
  ('P', 14),
  ('NP', 15)
]
GRADE_ORDER_BY_LETTER = OrderedDict(GRADE_ORDER_BY_LETTER)

SCHEDULE_DAYS = ['M', 'T', 'W', 'R', 'F']
