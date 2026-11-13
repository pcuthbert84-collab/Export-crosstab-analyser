"""Pure calculation layer for DBSJP Data Intelligence. No storage or network operations."""
from __future__ import annotations
import re
from dataclasses import dataclass
import pandas as pd
from grade_equivalences import baseline_equivalent
from alevel_grade_conversions import gcse_to_alevel_expected
from btec_it_grade_conversions import expected_btec_level, classify_btec_progress

KS3_POINTS = {'WT-':1,'WT':2,'WT+':3,'ME-':4,'ME':5,'ME+':6,'EX-':7,'EX':8,'MA':9}
GCSE_POINTS = {str(i):float(i) for i in range(1,10)} | {'U':0.0}
ALEVEL_POINTS = {'U':0,'E':2,'D':4,'C':5,'B':6,'A':7,'A*':9}
BTEC_POINTS = {'FAIL':1,'PASS':5,'MERIT':6,'DISTINCTION':7,'DISTINCTION*':9}
GROUP_FIELDS = ['SEN','Emirati','HAS / LAS','Islamic A/B','High Ability Learner','EAL','Home Grown','New Students']
SUBJECT_CATEGORIES = {
    'English': {'english','reading','writing','english language','english literature'},
    'Mathematics': {'mathematics','maths','further mathematics','further maths'},
    'Science': {'science','biology','chemistry','physics','combined science','btec science','science - biology','science - chemistry','science - physics','science - combined'},
    'Islamic': {'islamic a','islamic b','islamic studies a','islamic studies b','islamic studies'},
    'MSC': {'msc','msc studies'}, 'SSA': {'ssa','uae social studies a'}
}
GRADE_PAT = re.compile(r'^\s*(?:(?:Y|YEAR)\s*(\d+)\s*)?(WT\+|WT-|WT|ME\+|ME-|ME|EX-|EX|MA|A\*|[1-9]|U|[A-E]|D\*|P|M|D|PASS|MERIT|DISTINCTION\*|DISTINCTION|FAIL|\d\s*,\s*\d)\s*$', re.I)

@dataclass(frozen=True)
class Grade:
    raw: str
    point: float
    kind: str
    level: str
    curriculum_year: int | None = None
    pair: tuple[int,int] | None = None


def parse_grade(value, kind='auto', year=None):
    if pd.isna(value) or str(value).strip().upper() in ('','-','—','N/A','NA','NAN','NONE','NULL'):
        return None
    raw = str(value).strip().upper().replace(' ', '')
    match = re.fullmatch(r'(?:Y(\d+))?(WT-|WT\+|WT|ME-|ME\+|ME|EX-|EX|MA)', raw)
    if match:
        cy = int(match.group(1)) if match.group(1) else None
        label = match.group(2)
        return Grade(str(value), float(KS3_POINTS[label]), 'descriptor', label, cy)
    pair = re.fullmatch(r'([1-9]),([1-9])',raw)
    if pair:
        a,b=map(int,pair.groups())
        if a<b or a-b>1: return None
        return Grade(str(value), (a+b)/2., 'double',raw,None,(a,b))
    if raw in ('FAIL','PASS','MERIT','DISTINCTION','DISTINCTION*','D*') and kind in ('btec','auto'):
        name = 'DISTINCTION*' if raw=='D*' else raw
        return Grade(str(value),float(BTEC_POINTS[name]),'btec',name)
    if kind=='btec' and raw in ('P','M','D'):
        name={'P':'PASS','M':'MERIT','D':'DISTINCTION'}[raw]
        return Grade(str(value),float(BTEC_POINTS[name]),'btec',name)
    if raw == 'U':
        return Grade(str(value), 0.0, kind if kind in ('alevel','btec') else 'gcse', 'U')
    if kind=='alevel' and raw in ALEVEL_POINTS:
        return Grade(str(value),float(ALEVEL_POINTS[raw]),'alevel',raw)
    if raw in GCSE_POINTS and kind in ('auto','gcse'):
        return Grade(str(value),GCSE_POINTS[raw],'gcse',raw)
    # Unambiguous letter grades are recognised as A level when not explicitly GCSE.
    if raw in ('A*','A','B','C','E') and kind=='auto':
        return Grade(str(value),float(ALEVEL_POINTS[raw]),'alevel',raw)
    return None


def subject_category(name):
    n=str(name).strip().lower()
    for cat, aliases in SUBJECT_CATEGORIES.items():
        if n in aliases:return cat
    if n.startswith('science - '):return 'Science'
    return name


def assessment_type(column):
    v=str(column).strip().lower()
    if 'challenge target' in v:return 'challenge'
    if 'target' in v:return 'target'
    if 'class' in v:return 'class'
    return 'assessment'


def parse_dcpro(df, year, source_name='Uploaded file'):
    """Return long-form records. Student identifiers stay solely in the active session."""
    cols=[str(c).strip() for c in df.columns]
    student_col=next((c for c in df.columns if str(c).strip().lower() in ('student id','studentid','student code')),None)
    group_cols=[c for c in df.columns if str(c).strip() in GROUP_FIELDS]
    subject_cols={}
    for c in df.columns:
        parts=str(c).split(',',1)
        if len(parts)<2:continue
        subject=parts[0].strip();field=parts[1].strip()
        if not subject or not field:continue
        subject_cols.setdefault(subject,[]).append((c,field))
    records=[]
    for idx,row in df.iterrows():
        sid=str(row[student_col]).strip() if student_col is not None and pd.notna(row[student_col]) else f'{source_name}-{idx}'
        for subject,pairs in subject_cols.items():
            item={'student_id':sid,'year':int(year),'phase':2 if year<=6 else 3 if year<=11 else 4,
                  'subject':subject,'category':subject_category(subject),'source':source_name}
            for gc in group_cols:item[str(gc).strip()] = row[gc] if pd.notna(row[gc]) else None
            for c,field in pairs:
                item[field]=row[c] if pd.notna(row[c]) else None
            # Only create records with some actual assessment/target data, not class-only.
            if any(assessment_type(k)!='class' and pd.notna(v) for k,v in item.items() if k not in ('student_id','year','phase','subject','category','source',*GROUP_FIELDS)):
                records.append(item)
    return pd.DataFrame(records)


def select_grade(record, preferred, fallback=None, kind='auto', allow_gcse_baseline=False):
    for key in (preferred,fallback):
        if key and key!='None':
            g=parse_grade(record.get(key), kind)
            # Only selected PRIOR assessment columns in A Level cohorts may contain
            # GCSE numeric grades. Never reinterpret current A Level results.
            if g is None and allow_gcse_baseline and kind=='alevel':
                g=parse_grade(record.get(key),'gcse')
            if g:return g,key
    return None,None


def classify_attainment(grade, enrolled_year=None):
    if not grade:return None
    if grade.kind=='descriptor':
        if grade.curriculum_year is not None and enrolled_year is not None:
            if grade.curriculum_year<enrolled_year:return 'Below'
            if grade.curriculum_year>enrolled_year:return 'Above'
        return 'Below' if grade.point<=4 else 'At' if grade.point==5 else 'Above'
    if grade.kind=='gcse':return 'Below' if grade.point<=3 else 'At' if grade.point<=5 else 'Above'
    if grade.kind=='double':
        a,b=grade.pair
        return 'Below' if (a,b)<(4,3) else 'At' if (a,b)<(6,5) else 'Above'
    if grade.kind=='btec':return 'Below' if grade.level in ('FAIL','U') else 'At' if grade.level=='PASS' else 'Above'
    if grade.kind=='alevel':return 'Below' if grade.level in ('U','E','D') else 'At' if grade.level=='C' else 'Above'
    return None


def progress(baseline, current, current_year=None, baseline_year=None, subject=None):
    if not baseline or not current:return None
    btec_expected=expected_btec_level(baseline,current,subject)
    if btec_expected is not None:
        return classify_btec_progress(btec_expected,current)
    # School-approved equivalence applies to every subject, using the same
    # workbook's selected baseline/current points (or approved subject aliases).
    approved_expected = baseline_equivalent(baseline, current)
    if approved_expected is None:
        approved_expected = gcse_to_alevel_expected(baseline, current)
    expected = baseline.point
    if approved_expected is not None:
        expected = float(approved_expected)
    elif baseline.kind=='descriptor' and current.kind in ('gcse','double'):
        return None
    elif baseline.kind!=current.kind:
        return None
    elif baseline.kind=='descriptor' and baseline.curriculum_year and current.curriculum_year:
        # Same descriptor with expected one-year curriculum advancement.
        year_gap=(current_year-baseline_year) if current_year is not None and baseline_year is not None else 1
        curriculum_gap=current.curriculum_year-baseline.curriculum_year
        if curriculum_gap<year_gap:return 'Less'
        if curriculum_gap>year_gap:return 'Better'
    if current.kind=='gcse' and current.point>=7:return 'Better'
    if current.kind=='descriptor' and current.level in ('EX-','EX','MA') and (current.curriculum_year is None or current_year is None or current.curriculum_year>=current_year):return 'Better'
    if current.kind=='double' and current.pair>=(7,6):return 'Better'
    if current.kind=='alevel' and current.level in ('A','A*'):return 'Better'
    return 'Better' if current.point>expected else 'Expected' if current.point==expected else 'Less'


def target_met(actual,target):
    if not actual or not target:return None
    if actual.kind != target.kind:return None
    if actual.kind=='double':return actual.pair >= target.pair
    if actual.kind=='descriptor' and actual.curriculum_year and target.curriculum_year and actual.curriculum_year!=target.curriculum_year:
        return actual.curriculum_year>target.curriculum_year
    return actual.point >= target.point


def value_added(actual,target):
    if not actual or not target or actual.kind!=target.kind:return None
    if actual.kind=='double':return sum(a-b for a,b in zip(actual.pair,target.pair))/2
    return actual.point-target.point


def judgement(primary,secondary,n):
    if n<5 or primary is None or secondary is None:return None
    from decimal import Decimal,ROUND_HALF_UP
    p=int(Decimal(str(primary)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    s=int(Decimal(str(secondary)).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    if p<75:return 'Weak'
    if s>=75:return 'Outstanding'
    if s>=61:return 'Very Good'
    if s>=50:return 'Good'
    return 'Acceptable'


def derive(records, baseline, baseline_fallback, current, current_fallback,target,challenge):
    out=[]
    for rec in records.to_dict('records'):
        subject=rec['subject'].lower()
        kind='btec' if 'btec' in subject else 'alevel' if rec['year']>=12 else 'auto'
        cur,c_source=select_grade(rec,current,current_fallback,kind)
        old,b_source=select_grade(rec,baseline,baseline_fallback,kind,allow_gcse_baseline=(kind=='alevel'))
        t,_=select_grade(rec,target,None,kind)
        ch,_=select_grade(rec,challenge,None,kind)
        # A level grade interpretation requires explicit qualification context; exposed as option later.
        att=classify_attainment(cur,rec['year'])
        prog=progress(old,cur,rec['year'],rec['year']-1,subject=rec['subject'])
        met=target_met(cur,t);met75=target_met(cur,ch)
        va=value_added(cur,t)
        decline=(cur.point<old.point) if cur and old and cur.kind==old.kind else None
        item={k:rec.get(k) for k in ['student_id','year','phase','subject','category','source',*GROUP_FIELDS]}
        item.update({'baseline_grade':old.raw if old else None,'current_grade':cur.raw if cur else None,
                     'baseline_source':b_source,'current_source':c_source,'target_grade':t.raw if t else None,
                     'challenge_grade':ch.raw if ch else None,'attainment':att,'progress':prog,
                     'met_cat4':met,'met_cat4_75':met75,'value_added':va,'decline':decline})
        concern=[]
        if att=='Below':concern.append('Below standard')
        if met is False:concern.append('Below target')
        if prog=='Less':concern.append('Less progress')
        if decline:concern.append('Grade decline')
        item['concerns']=', '.join(concern);item['concern_count']=len(concern)
        out.append(item)
    return pd.DataFrame(out)


def english_overlap(data):
    """English generic supersedes Reading/Writing for the same student/year."""
    eng=data[data['category']=='English'].copy()
    if eng.empty:return eng
    generic=eng[eng['subject'].str.strip().str.lower()=='english']
    keys=set(zip(generic.loc[generic['current_grade'].notna(),'student_id'],generic.loc[generic['current_grade'].notna(),'year']))
    mask=eng.apply(lambda r:r['subject'].strip().lower() not in ('reading','writing') or (r['student_id'],r['year']) not in keys,axis=1)
    return eng[mask]


def summarise(data, by=('category',), method='pooled'):
    if data.empty:return pd.DataFrame()
    rows=[]
    for key,grp in data.groupby(list(by),dropna=False):
        keys=(key,) if not isinstance(key,tuple) else key
        rec=dict(zip(by,keys)); rec['records']=len(grp);rec['students']=grp['student_id'].nunique()
        # only qualified rows are denominator for each measure
        for col,good,label in [('attainment',['At','Above'],'at_or_above'),('attainment',['Above'],'above'),('progress',['Expected','Better'],'expected_plus'),('progress',['Better'],'better')]:
            valid=grp[grp[col].notna()]
            if method=='unweighted' and 'subject' in grp.columns:
                rates=[]
                for _,sub in valid.groupby('subject'):
                    rates.append(100*sub[col].isin(good).mean())
                rate=sum(rates)/len(rates) if rates else None
            else:rate=100*valid[col].isin(good).mean() if len(valid) else None
            rec[label]=rate;rec[label+'_n']=len(valid)
        rec['attainment_judgement']=judgement(rec['at_or_above'],rec['above'],rec['at_or_above_n'])
        rec['progress_judgement']=judgement(rec['expected_plus'],rec['better'],rec['expected_plus_n'])
        for col in ('met_cat4','met_cat4_75'):
            eligible=grp[grp[col].notna()] if col in grp.columns else grp.iloc[0:0]
            rec[col]=100*eligible[col].astype(bool).mean() if len(eligible) else None
            rec[col+'_n']=len(eligible)
        rec['va']=grp['value_added'].mean() if 'value_added' in grp.columns else None
        rows.append(rec)
    return pd.DataFrame(rows)
