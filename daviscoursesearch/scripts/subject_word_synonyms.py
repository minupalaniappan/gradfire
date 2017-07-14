SUBJECT_WORD_SYNONYMS = {
    'engineer': 'engineering',
    'grad': 'graduate',
    'lvrmor': 'livermore',
    'aero': 'aerospace',
    'molec': 'molecular',
    'ag': 'agriculture',
    'econ': 'economics',
    'tech': 'technology',
    'intl': 'internal',
    'envrn': 'environmental',
    'endocrinol': 'endocrinology',
    'metab': 'metabolism',
    'poli': 'political',
    'compar': 'comparative',
    'physio': 'physiology',
    'prev': 'preventative',
    'immun': 'immunology',
    'dev': set(['developmental', 'development']),
    'develpmnt': 'development',
    'chicano': 'chicana/o',
    'biol': 'biology',
    'pharmacol': 'pharmacology',
    'std': 'studies',
    'chem': set(['chemistry', 'chemical']),
    'prof': 'professional',
    'rehab': 'rehabilitation',
    'oncol': 'oncology',
    'stud': 'studies',
    'dis': 'diseases',
    'mngt': 'management',
    'microbiol': 'microbiology',
    'agric': 'agriculture',
    'reprod': 'reproductive',
    'comp': 'computer',
    'compu': 'computer',
    'environ': 'environmental',
    'toxic': 'toxicology',
    'nutr': 'nutrition',
    'hlth': 'health',
    'anat': 'anatomy',
    'sci': 'science',
    'bio': set(['biology', 'biological']),
    'med': 'medicine',
    'emphas': 'emphasis',
    'intrl': 'internal',
    'conserv': 'conservation',
    'sys': 'systems',
    'int': 'internal',
    'clinic': 'clinical',
    'desig': 'design',
    'mangmt': 'management',
    'managemnt': 'management',
    'physiol': 'physiology',
    'envir': 'environmental',
    'grp': 'group',
    'vm': 'veterinary medicine',
    'math': 'mathematics',
    'neurology': 'neurobiology',
    'chicano': set(['chicana/o', 'chicana']),
    'hydrologic': 'hydrology'
}

for word, synonyms in SUBJECT_WORD_SYNONYMS.items():
    if isinstance(synonyms, str):
        SUBJECT_WORD_SYNONYMS[word] = set([synonyms])

# Include reverse synonyms as well
for word, synonyms in SUBJECT_WORD_SYNONYMS.copy().items():
    for synonym in synonyms:
        SUBJECT_WORD_SYNONYMS[synonym] = set([word]) | (synonyms - set(synonym))

# Words sharing synonyms should reference each other
for word, synonyms in SUBJECT_WORD_SYNONYMS.items():
    for synonym in synonyms.copy():
        for other_word, other_synonyms in SUBJECT_WORD_SYNONYMS.items():
            if synonym in other_synonyms.copy():
                SUBJECT_WORD_SYNONYMS[other_word].add(word)
                SUBJECT_WORD_SYNONYMS[word].add(other_word)
