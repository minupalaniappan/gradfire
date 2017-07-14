Motivation: Subjects are often abbreviated by students -- "comp sci" -> computer science, "poli sci" -> political science, "chem" -> chemistry, etc. Our search engine needs to understand these abbreviations and map them to matching subjects. Currently, synonyms are currently hardcoded in the project in scripts/subject_word_synonyms.py.

The script **subjects_by_keyword.py** applies these synonyms and populates a python dictionary + PostgreSQL full text search tsvector.

**Usage:**
/home/andy/daviscoursesearch/ $ python3 -m daviscoursesearch.scripts.subjects_by_keyword.py daviscoursesearch/common/subjects_by_keyword.py

  Pulls synonyms from daviscoursesearch/scripts/subject_word_synonyms.py
and base subject list from daviscoursesearch/common/constants.py


Further work:
If we find this is too tedious to maintain, or that there are simply too many abbreviations, a more general implementation could involve string distance at the beginning of the word ("chem" is closest to "chemistry").