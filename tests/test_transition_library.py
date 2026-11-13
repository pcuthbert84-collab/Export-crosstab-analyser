import copy
import json
import pytest
from transition_library import (
    load_library,validate_library,find_rule,proposal,proposal_download,
)


def approved():
    return dict(from_year=6,to_year=7,current_subject='English',
                source_subjects=['Reading','Writing'],method='mean_available',
                status='approved',approved_by='School Assessment Lead',
                approved_on='2026-11-13',rationale='Documented English cross-phase mapping')


def test_seed_is_proposal_not_approved():
    library=load_library()
    assert library['rules'][0]['status']=='proposed'
    assert find_rule(library,7,'English',['Reading','Writing']) is None


def test_approved_rule_resolves_uploaded_subject_case():
    library={'schema_version':1,'rules':[approved()]}
    validate_library(library)
    rule=find_rule(library,7,'english',['READING','writing','Maths'])
    assert rule['resolved_sources']==['READING','writing']
    assert rule['method']=='mean_available'


def test_approved_rule_requires_every_source():
    lib={'schema_version':1,'rules':[approved()]}
    assert find_rule(lib,7,'English',['Reading']) is None
    assert find_rule(lib,8,'English',['Reading','Writing']) is None


def test_cannot_approve_without_named_reviewer_and_reason():
    bad=approved();del bad['approved_by']
    with pytest.raises(ValueError):validate_library({'schema_version':1,'rules':[bad]})


def test_duplicate_active_rules_rejected():
    with pytest.raises(ValueError):validate_library({'schema_version':1,'rules':[approved(),approved()]})


def test_nonconsecutive_year_rejected():
    bad=approved();bad['from_year']=5
    with pytest.raises(ValueError):validate_library({'schema_version':1,'rules':[bad]})


def test_invalid_method_rejected():
    bad=approved();bad['method']='weighted'
    with pytest.raises(ValueError):validate_library({'schema_version':1,'rules':[bad]})


def test_proposals_never_contain_student_ids():
    p=proposal(7,'English',['Reading','Writing'])
    encoded=proposal_download([p])
    obj=json.loads(encoded)
    assert obj['rules'][0]['status']=='proposed'
    assert 'student_id' not in encoded.decode()


def test_proposal_never_auto_applies():
    p=proposal(7,'English',['Reading','Writing'])
    assert find_rule({'schema_version':1,'rules':[p]},7,'English',['Reading','Writing']) is None
