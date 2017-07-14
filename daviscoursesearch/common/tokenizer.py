import re
from . import constants as const
from ..flaskapp.utils.utils import window
"""
Normalized query token types:
    crn
        regex

    course number
        regex

    term year
        2 or 4 digit integer regex
        potential conflict w/ course number
            throw an exception, or return a special value

    term month / session
        exact match of session name with term month
        'summer' - show all summer

    "ge" - TODO until we have student personal data

    units
        match integer before "unit" or "units" keywords

    day(s) of week

    "after" "before" and "at"
        "at" has to take into account +10min in afternoon
            "at 2" -> "at 2:10"

    full-text search with unrecognized words:
        subject DONE
        instructor
        title
"""

def tokenize(keywords):
    if isinstance(keywords, str):
        keywords = keywords.split(' ')
    keywords = [kw.lower() for kw in keywords]
    tokens, unmatched_keywords = tokenize_keywords(keywords)
    tokens += tokenize_fulltext(keywords)

    resolve_token_conflicts(tokens)
    return tokens

def resolve_token_conflicts(tokens):
    # Unit / course number conflict
    # e.g. "ecs 4 units"

    try:
        unit_token = next(token for token in tokens if token.type == 'unit')
        number_token = next(token for token in tokens if token.type == 'course_number')
        if number_token.normalized_value[-1] == str(unit_token.normalized_value):
            tokens.remove(number_token)
    except StopIteration:
        # no conflict
        pass

    # # Course number / summer session conflict
    # # e.g. "ecs summer session 1"
    # # should not match "1" as course number

    # try:
    #     course_number_token = next(token for token in tokens if token.type == 'course_number')
    #     term_month_token = next(token for token in tokens if token.type == 'term_month')
    #     if not any(token.type == 'term_year' for token in tokens):

    # except
TOKEN_TYPES = ['crn', 'course_number', 'subject_code', 'term_year', 'term_month', 'unit', 'ge_area']
SUBJECT_IGNORE = ('for', 'dan') # subject codes that may have conflicts

class Token(object):
    def __init__(self, token_type, keywords, normalized_value):
        if token_type not in TOKEN_TYPES:
            raise ValueError('Unrecognized token type {}'.format(token_type))
        self.type = token_type
        self.keywords = keywords
        self.normalized_value = normalized_value

    def __str__(self):
        return '{} token with normalized value: {} from kw {}'.format(self.type,
            self.normalized_value, self.keywords)


def tokenize_keywords(keywords):
    tokens = list()
    unmatched_keywords = list()
    for keyword in [w.lower() for w in keywords]:
        for matcher_method in KEYWORD_MATCHERS:
            token = matcher_method(keyword)

            if token:
                tokens.append(token)
            else:
                unmatched_keywords.append(keyword)

    return (tokens, unmatched_keywords)

def tokenize_fulltext(keywords):
    tokens = list()
    for matcher_method in FULLTEXT_MATCHERS:
        matched_tokens = matcher_method(keywords)
        if matched_tokens:
            tokens += matched_tokens


    return tokens

def match_crn(keyword):
    """
    Parameters:
        keyword
    """
    if re.match(r'[0-9]{5}$', keyword):
        return Token(token_type='crn', keywords=(keyword,), normalized_value=int(keyword))

    return None

COURSE_NUMBER_RE = r'([0-9]{1,3})([A-Za-z]{1,2})?'
def match_course_number(keyword, starting_with_subject=True):
    # Optional subject to handle 'che2b' case (no space)
    # Course number is 1-3 integers followed by 1 or 2 letters
    effective_re = COURSE_NUMBER_RE
    if starting_with_subject:
        effective_re = r'([A-Za-z]{3})' + effective_re

    matches = re.match(effective_re, keyword)
    # che2
    # che 2
    # not just '2'
    # reject number without preceding subject
    # but 9c is ok
    if matches:
        if starting_with_subject:
            _, number, letters = matches.groups()
        else:
            number, letters = matches.groups()
        if not letters:
            letters = ''

        if int(number) < 100 and len(number) < 3:
            number = ''.join(['0' for i in range(3 - len(number))]) + number

        return Token(token_type='course_number', keywords=(keyword,), normalized_value=number + letters.upper())

    return None

def match_term_year(keyword):
    matches = re.match(r'([0-9]{4})$', keyword)
    if matches:
        year = matches.group(1)
        if len(year) == 2:
            year = '20' + year

        return Token(token_type='term_year', keywords=(keyword,), normalized_value=year)

    return None

def match_term_month(keyword):
    for month, session_number in const.TERM_MONTH_BY_SESSION.items():
        if keyword == month:
            return Token(token_type='term_month', keywords=(keyword,), normalized_value=session_number)

    return None

def match_subject_code(keyword):
    keyword_candidate = keyword
    # handle 'che2a' case where subject and number are combined
    combined_match = re.match(r'([A-Za-z]{3})[0-9]', keyword)
    if combined_match:
        keyword_candidate = keyword[:3]

    if keyword_candidate.upper() in const.SUBJECTS:
        return Token(token_type='subject_code', keywords=(keyword,), normalized_value=keyword_candidate.upper())

def match_ge_code(keyword):
    if keyword.upper() in const.GE_AREAS_BY_OASIS_ABBRV.keys():
        return Token(token_type='ge_area', keywords=(keyword,), normalized_value=const.GE_AREAS_BY_OASIS_ABBRV[keyword.upper()])

def match_units(keywords):
    keyword_itr = iter(keywords)
    for keyword in keyword_itr:
        if re.match(r'[0-9]$', keyword):
            try:
                next_keyword = next(keyword_itr)
                if next_keyword == 'unit' or next_keyword == 'units':
                    return [Token(token_type='unit', keywords=(keyword, next_keyword), normalized_value=int(keyword))]
            except StopIteration:
                pass
    return None

def match_ge_area(keywords):
    keywords = [re.sub(r'[^A-Za-z]', '', kw.lower()) for kw in keywords]
    keywords = [kw for kw in keywords if kw]
    for area in const.GE_AREAS:
        area_split = [word.lower() for word in area.split()]
        area_split = [re.sub(r'[^A-Za-z]', '', word) for word in area_split]
        area_split = [word for word in area_split if word]
        offset = 0
        matched_kws = []
        for area_kw in area_split:
            try:
                offset = keywords[offset:].index(area_kw)
                matched_kws.append(area_kw)
            except ValueError:
                pass

        if matched_kws == area_split:
            return [Token(token_type='ge_area', keywords=matched_kws, normalized_value=area)]

def match_subject(keywords):
    """
    Match keywords to subject codes and names
    """
    keywords_by_subject = dict()
    for keyword in keywords:
        if keyword.upper() in const.SUBJECTS and keyword not in SUBJECT_IGNORE:
            return Token(token_type='subject', keywords=(keyword,), normalized_value=keyword.upper())
        elif keyword.title() in const.SUBJECT_CODES_BY_NAME.keys():
            return Token(token_type='subject', keywords=(keyword,), normalized_value=const.SUBJECT_CODES_BY_NAME[keyword.title()])

        for subject_code in const.SUBJECTS_BY_KEYWORD.get(keyword, []):
            try:
                keywords_by_subject[subject_code] += (keyword,)
            except KeyError:
                keywords_by_subject[subject_code] = (keyword,)

    try:
        top_match = max(keywords_by_subject.items(), key=lambda pair: len(pair[1]))
        return Token(token_type='subject', keywords=(keywords_by_subject,), normalized_value=top_match[0])
    except ValueError:
        return None

def match_term_month_fulltext(keywords):
    query = ' '.join(keywords)
    for kws, month in const.SEARCH_TERM_MONTH_BY_KWS.items():
        if kws in query:
            return [Token(token_type='term_month', keywords=kws.split(), normalized_value=month)]

def match_course_fulltext(keywords):
    for kw1, kw2 in window(keywords, n=2):
        number_token = match_course_number(kw2, starting_with_subject=False)
        if kw1.upper() in const.SUBJECTS and number_token:
            subject_token = Token(token_type='subject_code', keywords=(kw1,), normalized_value=kw1.upper())
            return [subject_token, number_token]
KEYWORD_MATCHERS = [
    match_crn,
    match_course_number,
    match_subject_code,
    match_term_month,
    match_term_year,
    match_units,
    match_ge_code
]

FULLTEXT_MATCHERS = [
    match_units,
    match_ge_area,
    match_term_month_fulltext,
    match_course_fulltext
]
