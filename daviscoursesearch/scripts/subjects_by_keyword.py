# coding: utf-8
import argparse
import inflect
import re
from collections import namedtuple
from ..common import constants, environment
from ..flaskapp.utils.db_utils import conn as db_conn
from .subject_word_synonyms import SUBJECT_WORD_SYNONYMS
from itertools import combinations, chain
from pprint import PrettyPrinter

DB_KEYWORDS_IGNORE = ['program', 'davis', 'davi']
DELIMETERS = ['-', '&', '/']
infl = inflect.engine()

def split_word(word):
	for delimeter in DELIMETERS:
		split = word.split(delimeter)
		if len(split) > 1:
			return split

	return [word]

def synonyms_for_word(word):
	synonyms = SUBJECT_WORD_SYNONYMS.get(word, None)
	if synonyms:
		if isinstance(synonyms, str):
			return [word, synonyms]
		elif isinstance(synonyms, set):
			return [word] + list(synonyms)
	else:
		return [word]

def flatten_keywords(subjects):
	return map(
		lambda subject: subject._replace(keywords=chain(*subject.keywords)), subjects
	)

def remove_special_characters(subject_keywords):
	return map(
		lambda subject: subject._replace(keywords=(map(lambda word: re.sub(r'^[^A-Za-z]|[^A-Za-z]$', '', word), subject.keywords))),
		subject_keywords)

def remove_empty_kw(subject_keywords):
	return map(lambda subject: subject._replace(keywords=filter(lambda word: word, subject.keywords)), subject_keywords)

def lower_case(subject_keywords):
	return map(
		lambda subject: subject._replace(keywords=map(lambda word: word.lower(), subject.keywords)), subject_keywords)

def remove_conjunctions(subject_keywords):
	return map(lambda subject: subject._replace(keywords=filter(lambda word: word not in constants.CONJUNCTIONS, subject.keywords)), subject_keywords)

def split_by_delimeters(subject_keywords):
	return map(
		lambda subject: subject._replace(keywords=map(split_word, subject.keywords)), subject_keywords)

def add_synonyms(subject_keywords):
	return map(
		lambda subject: subject._replace(keywords=map(synonyms_for_word, subject.keywords)), subject_keywords)

def include_plural_and_nonplural(subject_keywords):
	return map(
		lambda subject: subject._replace(keywords=map(lambda word: (word, infl.plural(word)), subject.keywords)), subject_keywords)

def generate_keywords():
	SubjectKeywords = namedtuple('SubjectKeywords', ['keywords', 'code'])
	subject_keywords = map(
		lambda subject: SubjectKeywords(keywords=subject[0].split(' '), code=subject[1]),
			constants.SUBJECT_CODES_BY_NAME.items()
	)

	subject_keywords = remove_special_characters(subject_keywords)

	subject_keywords = remove_empty_kw(subject_keywords)

	subject_keywords = lower_case(subject_keywords)

	subject_keywords = remove_conjunctions(subject_keywords)

	subject_keywords = split_by_delimeters(subject_keywords)
	subject_keywords = flatten_keywords(subject_keywords)

	subject_keywords = add_synonyms(subject_keywords)
	subject_keywords = flatten_keywords(subject_keywords)

	subject_keywords = include_plural_and_nonplural(subject_keywords)
	subject_keywords = list(flatten_keywords(subject_keywords))
	subject_keywords = [subject._replace(keywords=set(subject.keywords)) for subject in subject_keywords]

	keywords_by_subject = dict()
	for subject in subject_keywords:
		keywords_by_subject[subject.code] = subject.keywords

	subjects_by_keyword = dict()
	for subject in subject_keywords:
		for word in subject.keywords:
			try:
				subjects_by_keyword[word] += (subject.code,)
			except KeyError:
				subjects_by_keyword[word] = (subject.code,)

	return keywords_by_subject, subjects_by_keyword

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('outfile') # script should write to file and update db
	args, _ = parser.parse_known_args()

	keywords_by_subject, subjects_by_keyword = generate_keywords()
	f = open(args.outfile, 'w')
	f.write('SUBJECTS_BY_KEYWORD = ')
	PrettyPrinter(indent=4, stream=f).pprint(subjects_by_keyword)

	cur = db_conn.cursor()
	cur.execute("TRUNCATE subjects")
	for subject, keywords in keywords_by_subject.items():
		keywords = list(keywords)
		keywords = [kw for kw in keywords if not any(kw_to_ignore in kw for kw_to_ignore in DB_KEYWORDS_IGNORE)]
		kws_space_sep = ' '.join(keywords)
		cur.execute("INSERT INTO subjects (code, tsv, keywords) VALUES (%s, to_tsvector(%s), %s)", (subject, kws_space_sep, kws_space_sep))
