"""Version-controlled, non-personal subject transition rules.

Approval is deliberately NOT available from the public Streamlit interface: a
repository reviewer must edit the JSON, and deployment must be protected by IT.
This is a workflow aid, not an authentication or authorization mechanism.
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import date

LIBRARY_FILE = Path(__file__).with_name('approved_subject_transitions.json')
SCHEMA_VERSION = 1


def normalise_subject(value):
    return ' '.join(str(value).casefold().strip().split())


def validate_rule(rule):
    if not isinstance(rule, dict):
        raise ValueError('A mapping rule must be an object')
    mandatory = ('from_year', 'to_year', 'current_subject', 'source_subjects', 'status', 'method')
    if any(k not in rule for k in mandatory):
        raise ValueError('Missing required transition fields')
    y1, y2 = rule['from_year'], rule['to_year']
    if type(y1) is not int or type(y2) is not int or not (1 <= y1 <= 12 and y2 == y1 + 1):
        raise ValueError('Year transition must be consecutive and between years 1 and 13')
    if not isinstance(rule['current_subject'], str) or not rule['current_subject'].strip():
        raise ValueError('Current subject must be specified')
    sources = rule['source_subjects']
    if not isinstance(sources, list) or not sources or any(not isinstance(s,str) or not s.strip() for s in sources):
        raise ValueError('Provide at least one valid source subject')
    if len({normalise_subject(s) for s in sources}) != len(sources):
        raise ValueError('Repeated source subjects')
    if rule['status'] not in ('approved', 'proposed', 'retired'):
        raise ValueError('Invalid status')
    if rule['method'] not in ('single', 'mean_available'):
        raise ValueError('Unknown method')
    if rule['method'] == 'single' and len(sources) != 1:
        raise ValueError('Single mapping must contain exactly one source')
    if rule['status']=='approved' and not all(isinstance(rule.get(k),str) and rule[k].strip() for k in ('approved_by','approved_on','rationale')):
        raise ValueError('Approved rules require reviewer, date and rationale')
    if rule['status']=='approved':
        try: date.fromisoformat(rule['approved_on'])
        except ValueError as exc: raise ValueError('Invalid approval date') from exc
    return rule


def validate_library(payload):
    if not isinstance(payload,dict) or payload.get('schema_version') != SCHEMA_VERSION or not isinstance(payload.get('rules'),list):
        raise ValueError('Invalid transition library format/version')
    seen=set()
    for rule in payload['rules']:
        validate_rule(rule)
        if rule['status'] == 'approved':
            key=(rule['to_year'],normalise_subject(rule['current_subject']))
            if key in seen:
                raise ValueError('Multiple active approved rules for the same current subject and year')
            seen.add(key)
    return payload


def load_library(path=LIBRARY_FILE):
    """Fail closed if a malformed repository file is deployed."""
    return validate_library(json.loads(Path(path).read_text(encoding='utf-8')))


def find_rule(library, year, subject, allowed_sources):
    """Only return an approved rule if ALL its source subjects exist in the upload.

    Names are matched case-insensitively but retain exact uploaded spelling.
    """
    available={normalise_subject(x):x for x in allowed_sources}
    for rule in library['rules']:
        if rule['status']!='approved' or rule['to_year']!=int(year) or normalise_subject(rule['current_subject'])!=normalise_subject(subject):
            continue
        canonical=[available.get(normalise_subject(s)) for s in rule['source_subjects']]
        if all(canonical):return {**rule, 'resolved_sources':canonical}
    return None


def proposal(year, subject, sources, reason='Subject transition suggested for review'):
    rule={'from_year':int(year)-1,'to_year':int(year),'current_subject':str(subject),
          'source_subjects':list(sources),'method':'single' if len(sources)==1 else 'mean_available',
          'status':'proposed','rationale':reason}
    validate_rule(rule)
    return rule


def proposal_download(rules):
    return json.dumps({'schema_version':SCHEMA_VERSION, 'rules':rules},indent=2,ensure_ascii=False).encode('utf-8')
