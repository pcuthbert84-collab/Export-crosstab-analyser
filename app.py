"""DBSJP Data Intelligence — Leadership prototype v2.0.

Use synthetic/non-identifying data only until school-approved production hosting,
Entra authentication, authorisation and security review have been completed.
"""
from __future__ import annotations
import io
import hashlib
import re
from datetime import datetime
from html import escape
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from engine import parse_dcpro, derive, summarise, GROUP_FIELDS
from session_performance import fingerprint, reuse, clear_private
from year_detection import suggest_year
from progress_subject_mapping import mapping_candidates, apply_subject_mappings
from same_cohort_mapping import same_cohort_candidates, apply_same_cohort_mappings
from progress_coverage import progress_coverage
from transition_library import load_library, find_rule, proposal, proposal_download, normalise_subject, is_explicitly_unmapped
from overview_tables import summary_tables, compact_table, detail_table
from dashboard_analytics import (
    PHASES, combined_assessments, filtered_cohort_summary, coverage_status,
    percentage_label, ppm_subject_counts, attained_grade_counts, subject_coverage, focus_judgements, assessment_coverage, ppm_subject_hotspots,
)
from dashboard_exports import excel_bytes, pdf_summary
from dashboard_ui import (
    THEME_CSS, NAV_ITEMS, row_style, grade_legend_html,
    metric_bars, judgement_mix, progress_mix, group_compare, grade_distribution_chart,
)

st.set_page_config(page_title='DBSJP | Data Intelligence',page_icon='📊',layout='wide',initial_sidebar_state='expanded')
st.markdown(THEME_CSS, unsafe_allow_html=True)


def load_excel(blob):
    """Read workbook bytes, without persisting data to disk."""
    book=pd.ExcelFile(io.BytesIO(blob),engine='openpyxl')
    return [(sheet,pd.read_excel(book,sheet_name=sheet,dtype=object)) for sheet in book.sheet_names]


def auto_select(items, phrase, default=0):
    for i,item in enumerate(items):
        if phrase.lower() in str(item).lower():return i
    return min(default, max(0,len(items)-1))


def guessed_year(filename,default=8):
    match=re.search(r'(?:year|yr|\by)\s*[-_ ]?\s*(1[0-3]|[1-9])\b',filename,re.I)
    return int(match.group(1)) if match else default


def table_display(df, *, height=520):
    st.dataframe(row_style(df),hide_index=True,use_container_width=True,height=min(height,max(155,46+(len(df)+1)*36)))


def labelled_metric(container,label,value,caption=None):
    with container:
        st.metric(label,value)
        if caption:st.caption(caption)


def show_performance_tables(frame, by, key):
    """Render only the selected performance view, avoiding slow hidden tabs.

    A horizontal radio is deliberate: st.tabs eagerly executes content in every
    tab, even when hidden. A radio selection triggers Streamlit's normal rerun,
    updates immediately, and computes only the selected table and export.
    """
    choice = st.radio(
        'Assessment view', ['Attainment', 'Progress'], horizontal=True,
        key=f'{key}_assessment_view',
        help='Switches the visible results immediately; no Apply button is needed.',
    )
    kind = choice.lower()
    # Summaries are derived only once for the current visible cohort and mode.
    # Reuse is strictly session-local and the key includes all data and filters.
    table_key = fingerprint(
        'tables-v2',
        [(str(row.student_id), str(row.year), str(row.subject),
          str(row.attainment), str(row.progress), str(row.current_grade),
          str(row.target_grade), str(row.met_cat4), str(row.met_cat4_75))
         for row in frame.itertuples(index=False)],
        list(by), method,
    )
    att, prog, dist = reuse(
        st.session_state, f'presentation_{key}', table_key,
        lambda: summary_tables(frame, by, method),
    )
    table = att if kind == 'attainment' else prog
    if table.empty:
        st.info(f'No valid {choice.lower()} results for this selection.')
        return
    l, r = st.columns([2.5, 1], vertical_alignment='bottom')
    with l:
        st.markdown(f'**{choice} by subject**')
    with r:
        detail = st.radio(
            'Table detail', ['Compact', 'Detailed'], horizontal=True,
            key=f'{key}_{kind}_style', label_visibility='collapsed',
        )
    shown = compact_table(table, by, kind) if detail == 'Compact' else detail_table(table, by, kind)
    focus = st.selectbox(
        'Focus on',
        ['All results', 'Weak / Acceptable', 'Good or above', 'Without judgement'],
        key=f'{key}_{kind}_focus',
        help='Filter this table and its Excel export by the calculated KHDA judgement.',
    )
    shown = focus_judgements(shown, focus)
    st.markdown(grade_legend_html(), unsafe_allow_html=True)
    if shown.empty:
        st.info('No subject rows match that KHDA focus. Try All results.')
    else:
        table_display(shown, height=570)
    if detail == 'Detailed':
        st.caption('Grade counts refer to assessment results. Target-predicted attainment uses available target grades; target-based progress percentages use their own eligible denominators.')
        with st.expander('Grade frequencies — counts and percentages'):
            d = dist.copy()
            if not d.empty:
                d['Percent'] = d['Percent'].map(percentage_label)
                d = d.rename(columns={'category':'Subject','subject':'Subject','year':'Year', 'Grade':'Grade','Count':'Number','Percent':'% of grades'})
                st.dataframe(d, hide_index=True, use_container_width=True)
    # Generation of the Excel export is delayed until the visible table is ready.
    st.download_button(
        f'Download {choice.lower()} table · Excel',
        excel_bytes(shown), f'DBSJP_{key}_{kind}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key=f'{key}_{kind}_download',
    )
    st.caption('Number = unique students with valid grades for this measure. Combined subject categories may include multiple assessment results per student; the underlying numerator and denominator use eligible subject records.')


def narrative_findings(s):
    """Deterministic descriptive observations; not diagnoses or causal explanations."""
    if s.empty:return []
    eligible=s.loc[s['at_or_above_n'].ge(5) & s['at_or_above'].notna()].copy()
    if eligible.empty:return []
    out=[]
    strongest=eligible.sort_values('at_or_above',ascending=False).iloc[0]
    weakest=eligible.sort_values('at_or_above').iloc[0]
    out.append(f"Highest meeting-or-above attainment: **{strongest['category']}** ({percentage_label(strongest['at_or_above'])}; {int(strongest['at_or_above_n'])} valid results).")
    if strongest['category']!=weakest['category']:
        out.append(f"Lowest meeting-or-above attainment: **{weakest['category']}** ({percentage_label(weakest['at_or_above'])}; {int(weakest['at_or_above_n'])} valid results).")
    progress=s.loc[s['expected_plus_n'].ge(5) & s['expected_plus'].notna()]
    if not progress.empty:
        less=progress.sort_values('expected_plus').iloc[0]
        out.append(f"Lowest expected-or-better progress: **{less['category']}** ({percentage_label(less['expected_plus'])}; {int(less['expected_plus_n'])} valid comparisons).")
    return out


# ───────────────────── Main application ─────────────────────
with st.sidebar:
    st.markdown('<div class="db-eyebrow">DUBAI BRITISH SCHOOL</div>',unsafe_allow_html=True)
    st.markdown('### Data Intelligence')
    st.caption('Leadership dashboard · v2.8 · approved subject transitions')
    st.divider()
    view=st.radio('Explore', [x[0] for x in NAV_ITEMS],index=0)
    st.divider()
    if '_dbsjp_upload_revision' not in st.session_state:
        st.session_state['_dbsjp_upload_revision']=0
    if st.button('Clear uploads and analysis',help='Clear the upload widget plus parsed and calculated assessment records for this session.'):
        clear_private(st.session_state)
        st.session_state['_dbsjp_upload_revision']+=1
        st.rerun()
    uploads=st.file_uploader('Upload DCPro Excel files',type=['xlsx'],accept_multiple_files=True,key=f"dbsjp_uploads_{st.session_state['_dbsjp_upload_revision']}",help='One workbook per year group; use synthetic data for development.')
    st.caption('Session-only processing and reuse. Do not use with real student data on public hosting.')

st.markdown('''<div class="db-hero"><div class="db-eyebrow" style="color:#9cd4df">DBSJP · ASSESSMENT & REPORTING</div>
<h1>Data Intelligence</h1><p>Clearer insights. Better questions. More targeted support.</p></div>''',unsafe_allow_html=True)
st.warning('**Development environment — synthetic or properly anonymised data only.** Student-record access control, secure hosting and production data protection are not yet implemented.',icon='🔒')

if not uploads:
    clear_private(st.session_state)
    st.subheader('Your assessment workspace')
    st.write('Upload one or more year-group DCPro Excel exports using the sidebar. Then confirm the year group and assessment columns to explore your results.')
    c1,c2,c3=st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown('#### 01 · Upload')
            st.write('Select your year-group workbooks. Each file is checked for recognised assessment columns.')
    with c2:
        with st.container(border=True):
            st.markdown('#### 02 · Configure')
            st.write('Choose current, baseline and fallback assessments plus standard and challenge targets.')
    with c3:
        with st.container(border=True):
            st.markdown('#### 03 · Explore')
            st.write('Open the subject, group and PPM views or generate an aggregate report.')
    st.info('To try the interface without identifiable records, use **SYNTHETIC_DCPro_Year8.xlsx** supplied in the ZIP package.')
    with st.expander('What is available in this build?'):
        st.markdown('''**Available:** subject breakdowns, attainment/progress judgements, filtered charts, PPM lists, student groups, CAT4, value added, Excel exports and an aggregate PDF.  
**Planned:** production Microsoft 365 authentication, secure hosting, a full historical 87-table Data Pack, EYFS, NGRT, GL/IBT imports and public exam data.''')
    st.stop()

st.markdown('### 1 · Confirm your uploads')
loaded=[]
selected_signatures=[]
for i,file in enumerate(uploads):
    try:
        blob=file.getvalue()
        if len(blob)>12*1024*1024:
            st.error(f'{file.name}: File exceeds the prototype 12 MB limit.');continue
        file_fingerprint=fingerprint(blob)
        sheets=reuse(st.session_state, f'workbook_{i}', file_fingerprint, lambda: load_excel(blob))
    except Exception:
        st.error(f'{file.name}: Could not read a valid Excel workbook.');continue
    with st.expander(f'{file.name} · {len(sheets)} worksheet(s)',expanded=True):
        selected_sheets=st.multiselect('Worksheets to include',[name for name,_ in sheets],default=[sheets[0][0]],key=f'upload_sheets_{i}')
        active_sheets=[(name,df) for name,df in sheets if name in selected_sheets]
        guess=suggest_year(file.name,active_sheets)
        options=['Please select']+list(range(1,14))
        default_idx=guess.year if guess.year is not None else 0
        year_key=file_fingerprint[:12]
        sheet_key=hashlib.sha256('|'.join(sorted(selected_sheets)).encode()).hexdigest()[:8]
        year=st.selectbox('Confirm year group',options,index=default_idx,key=f'upload_year_{i}_{year_key}_{sheet_key}',help='Automatically suggested from class codes, year-group columns or filename; always confirm. A workbook must represent one enrolled year group.')
        st.caption(f'Year-group suggestion: {guess.note}')
        if year=='Please select':
            st.warning('Choose a year group above before this workbook is included in the analysis.')
            continue
        for sheet,df in sheets:
            if sheet in selected_sheets:
                st.caption(f'{sheet}: {len(df):,} source rows · {len(df.columns):,} columns')
                parse_key=fingerprint(file_fingerprint,sheet,year)
                parsed=reuse(st.session_state,f'parsed_{i}_{hashlib.sha256(sheet.encode()).hexdigest()[:10]}',parse_key,lambda: parse_dcpro(df,year,file.name))
                if not parsed.empty:
                    loaded.append(parsed)
                    selected_signatures.append((i,file.name,parse_key))

if not loaded:
    st.info('No DCPro assessment records were found in the selected worksheets.')
    st.stop()
record_key=fingerprint(selected_signatures)
records=reuse(st.session_state,'records',record_key,lambda:pd.concat(loaded,ignore_index=True))
if records.duplicated(['student_id','year','subject']).any():
    st.error('Duplicate student/year/subject records have been detected. Review overlapping uploads before relying on results; duplicate records have not been automatically removed.')

excluded={'student_id','year','phase','subject','category','source',*GROUP_FIELDS}
fields=sorted(x for x in records.columns if x not in excluded and any(word in str(x).lower() for word in ('cpl','ag','exam','mock','target')))
assess=[f for f in fields if 'target' not in f.lower()]
targets=[f for f in fields if 'target' in f.lower()]
if not assess:
    st.error('No recognised assessment-grade columns were found. Check the selected DCPro worksheets.')
    st.stop()

with st.expander('2 · Assessment and target settings',expanded=True):
    st.caption('Priority 2 is used only if Priority 1 has no valid grade for the individual student and subject.')
    c1,c2,c3,c4=st.columns(4)
    with c1:base=st.selectbox('Baseline · first choice',assess,index=auto_select(assess,'DP3'))
    with c2:base2=st.selectbox('Baseline · fallback',['None']+assess,index=1+auto_select(assess,'exam') if any('exam' in x.lower() for x in assess) else 0)
    with c3:cur=st.selectbox('Current · first choice',assess,index=auto_select(assess,'DP1'))
    with c4:cur2=st.selectbox('Current · fallback',['None']+assess,index=1+auto_select(assess,'mock') if any('mock' in x.lower() for x in assess) else 0)
    a,b=st.columns(2)
    with a:tar=st.selectbox('Standard CAT4 target',['None']+targets,index=next((i+1 for i,t in enumerate(targets) if t.lower().startswith('target')),0))
    with b:cha=st.selectbox('CAT4 75 · Challenge target',['None']+targets,index=1+auto_select(targets,'Challenge') if targets else 0)
    st.caption('Unsupported cross-grade-set comparisons remain unclassified until approved; this build does not infer equivalences.')

# Repository-controlled approval library, never stores student data.
try:
    transition_library=load_library()
except (ValueError, OSError, KeyError) as exc:
    st.error(f'Subject transition library is invalid: {exc}. No library mappings will be applied.')
    st.stop()

mapping_rules={}
requested_proposals=[]
with st.expander('Optional · Progress subject transition library',expanded=False):
    st.caption('Approved rules can preselect earlier-year subjects. Suggested rules need review and do not run automatically. Any override applies only to this dashboard session.')
    candidates=reuse(st.session_state,'mapping_candidates',fingerprint(record_key,base,base2),lambda:mapping_candidates(records,base,None if base2=='None' else base2))
    available=[item for item in candidates if item['missing_same_subject']>0
               and not is_explicitly_unmapped(transition_library,item['year'],item['subject'])]
    approved=[r for r in transition_library['rules'] if r['status']=='approved']
    proposed=[r for r in transition_library['rules'] if r['status']=='proposed']
    st.caption(f'Library: {len(approved)} approved transition(s), {len(proposed)} awaiting review, {len(transition_library.get("no_mapping_decisions", []))} explicitly unmapped. Approvals are managed through reviewed GitHub changes, not this public dashboard.')
    if transition_library.get('no_mapping_decisions'):
        with st.expander('School decisions: deliberately unmapped subjects',expanded=False):
            for decision in transition_library['no_mapping_decisions']:
                st.caption(f"Year {decision['to_year']} {decision['current_subject']}: no earlier-subject transition approved.")
    if not available:
        st.info('No eligible earlier-year subjects found with matching student IDs and available baseline grades. Upload adjacent year groups to configure a transition.')
    else:
        for item in available:
            year=item['year'];name=item['subject']
            active=find_rule(transition_library,year,name,item['sources'])
            suggested=next((r for r in proposed if r['to_year']==year and normalise_subject(r['current_subject'])==normalise_subject(name)),None)
            with st.container(border=True):
                st.markdown(f'**Year {year} · {name}** ← Year {year-1}')
                if active:
                    st.caption(f'Approved by {active["approved_by"]} on {active["approved_on"]}: {active["rationale"]}')
                elif suggested:
                    st.caption('Suggested for review (NOT approved): '+', '.join(suggested['source_subjects']))
                else:
                    st.caption('No approved rule; you can select a temporary mapping below.')
                enabled=st.checkbox('Use this mapping for the current session',value=bool(active),
                                    key=f'transition_enabled_{year}_{hashlib.sha256(name.encode()).hexdigest()[:12]}')
                selected=st.multiselect(
                    'Earlier-year subject(s)',item['sources'],
                    default=(active['resolved_sources'] if active else []),
                    key=f'transition_sources_{year}_{hashlib.sha256(name.encode()).hexdigest()[:12]}')
                if enabled and selected:
                    mapping_rules[(year,name)]=selected
                    st.caption('Using '+('one source' if len(selected)==1 else 'the mean of available source grades')+'. Existing valid baselines will not be replaced.')
                elif enabled:
                    st.warning('Select at least one earlier-year subject to enable this mapping.')
                if selected and (not active or [normalise_subject(x) for x in selected]!=[normalise_subject(x) for x in active['resolved_sources']]):
                    if st.checkbox('Include my selection in a non-personal approval request',key=f'transition_proposal_{year}_{hashlib.sha256(name.encode()).hexdigest()[:12]}'):
                        requested_proposals.append(proposal(year,name,selected))
        if requested_proposals:
            st.download_button('Download mapping proposals for subject leader approval',
                proposal_download(requested_proposals),'DBSJP_Subject_Mapping_Proposals.json',
                mime='application/json',key='subject_mapping_proposals_download')
            st.caption('The downloaded proposals contain subject and year names only, not student data. A designated reviewer must approve and commit them into the library.')
        if mapping_rules:
            st.warning('Subject mapping does not approve cross-grade-set conversions. Review any conversion warnings before using progress results.')

calc_key=fingerprint(record_key,base,base2,cur,cur2,tar,cha)
base_computed=reuse(st.session_state,'calculated',calc_key,
    lambda:derive(records,base,None if base2=='None' else base2,cur,None if cur2=='None' else cur2,None if tar=='None' else tar,None if cha=='None' else cha))
# Never mutate a cached result. Reuse mapped results only when rules/assessments match.
mapped_key=fingerprint(calc_key,sorted((year,name,tuple(sources)) for (year,name),sources in mapping_rules.items()))
computed,mapping_audit=reuse(st.session_state,'mapped',mapped_key,
    lambda:apply_subject_mappings(base_computed,records,mapping_rules,base,None if base2=='None' else base2))
if mapping_rules:
    applied=int((mapping_audit.get('status',pd.Series(dtype=str))=='Mapped').sum())
    unsupported=int((mapping_audit.get('status',pd.Series(dtype=str))=='Needs conversion').sum())
    st.caption(f'Progress subject mapping: {applied} student-subject comparisons mapped; {unsupported} need an approved grade conversion.')
    if not mapping_audit.empty and unsupported:
        with st.expander('Mappings requiring conversion review'):
            st.dataframe(mapping_audit.loc[mapping_audit.status!='Mapped'],hide_index=True,use_container_width=True)

# A DCPro current-year export can contain a *prior assessment* under a different
# subject heading. This is not a match to the other cohort's current workbook.
with st.expander('Optional · Match previous grades within the same cohort export', expanded=False):
    st.caption('Example: Year 7 English current grade with last year’s Reading/Writing grades in the Year 7 export, or Year 11 English with an English Language prior exam grade. Only applies if explicitly enabled; grade conversions must be approved.')
    candidates=reuse(st.session_state,'same_cohort_candidates',fingerprint(calc_key,mapped_key,transition_library),
        lambda:same_cohort_candidates(records,computed,base,None if base2=='None' else base2,transition_library))
    if not candidates:
        st.info('No same-cohort subject transition candidates were detected for the selected assessments.')
        same_rules={}
    else:
        names=[f"Year {c['year']} · {c['subject']} ({c['missing']} current students without a baseline)" for c in candidates]
        approved_indices=[i for i,c in enumerate(candidates) if find_rule(
            transition_library,c['year'],c['subject'],[x['subject'] for x in c['sources']],
            source_scope='same_cohort_prior_assessment')]
        selected_targets=st.multiselect('Choose the subject transitions to configure',range(len(candidates)),
            default=approved_indices,format_func=lambda i:names[i],key='same_cohort_mapping_focus')
        same_rules={}
        for choice_index in selected_targets:
            selected_candidate=candidates[choice_index]
            options=[x['subject'] for x in selected_candidate['sources']]
            approved_same=find_rule(transition_library,selected_candidate['year'],
                selected_candidate['subject'],options,source_scope='same_cohort_prior_assessment')
            with st.container(border=True):
                st.markdown(f"**Year {selected_candidate['year']} · {selected_candidate['subject']}**")
                st.caption('Prior-assessment subjects in this same cohort: '+', '.join(f"{x['subject']} ({x['students']})" for x in selected_candidate['sources']))
                if approved_same:
                    st.caption('Approved subject mapping: '+', '.join(approved_same['resolved_sources'])+'. This does not approve unsupported grade conversions.')
                unique=f"{selected_candidate['year']}_{hashlib.sha256(selected_candidate['subject'].encode()).hexdigest()[:8]}"
                selected=st.multiselect('Choose previous-assessment subject(s)',options,
                    default=(approved_same['resolved_sources'] if approved_same else []),
                    key=f'same_cohort_sources_{unique}')
                enabled=st.checkbox('Use this mapping for the current session',value=bool(approved_same),
                    key=f'same_cohort_enable_{unique}')
                if enabled and selected:
                    same_rules[(selected_candidate['year'],selected_candidate['subject'])]=selected
                elif enabled:st.warning('Choose at least one previous-assessment subject.')
        st.caption('Unsupported descriptor-to-GCSE equivalences are not invented. Those records remain outside progress percentages until the school approves the conversion rules.')
if same_rules:
    same_key=fingerprint(mapped_key,sorted((y,s,tuple(v)) for (y,s),v in same_rules.items()))
    computed,same_audit=reuse(st.session_state,'same_cohort_mapped',same_key,
        lambda:apply_same_cohort_mappings(computed,records,same_rules,base,None if base2=='None' else base2))
    mapped_count=int((same_audit.status=='Mapped').sum()) if not same_audit.empty else 0
    blocked_count=int((same_audit.status=='Needs approved conversion').sum()) if not same_audit.empty else 0
    st.info(f'Same-cohort subject mapping: {mapped_count} additional progress comparisons; {blocked_count} need an approved grade conversion.')

if computed.empty:
    st.info('No assessment outcomes were found with the selected configuration.');st.stop()

with st.expander('3 · Filters · phase, year, subject and groups',expanded=True):
    present_phases=sorted(int(x) for x in computed.phase.dropna().unique())
    left,right=st.columns([1,2])
    with left:
        selected_phases=st.multiselect('Phases',options=[1,2,3,4],default=present_phases,format_func=lambda v:f'{PHASES[v][0]} · {PHASES[v][1]}',help='Phase 1 (EYFS) imports are planned for a later version.')
    permitted_years=sorted(int(v) for v in computed.loc[computed.phase.isin(selected_phases),'year'].unique())
    with right:
        selected_years=st.multiselect('Year groups',permitted_years,default=permitted_years,key='selected_years',help='Only year groups belonging to the selected phases are listed.')
    category_options=sorted(computed.loc[computed.year.isin(selected_years),'category'].dropna().unique())
    a,b=st.columns(2)
    with a:categories=st.multiselect('Reporting subjects / categories',category_options,default=category_options)
    subjects_options=sorted(computed.loc[computed.year.isin(selected_years)&computed.category.isin(categories),'subject'].dropna().unique())
    with b:subjects=st.multiselect('Individual subjects',subjects_options,default=subjects_options)
    method_choice=st.radio('Combined subject method',['Pooled subject results (default)','Unweighted subject percentages'],horizontal=True)
    group_filters={}
    group_options=[c for c in GROUP_FIELDS if c in computed and computed[c].notna().any()]
    if group_options:
        with st.expander('Additional student-group filters'):
            for g in group_options:
                options=sorted(computed[g].dropna().astype(str).unique())
                selected=st.multiselect(g,options,key='group_'+g)
                if selected:group_filters[g]=selected

method='unweighted' if method_choice.startswith('Unweighted') else 'pooled'
data=computed.loc[computed.phase.isin(selected_phases)&computed.year.isin(selected_years)&computed.category.isin(categories)&computed.subject.isin(subjects)].copy()
for field,values in group_filters.items():data=data.loc[data[field].astype(str).isin(values)]
if data.empty:
    st.info('No results match those filters. Select a different phase, year group, subject or student group.')
    st.stop()
combined=combined_assessments(data)
# Surface the denominator before any leadership judgement is viewed.
current_n=int(combined['current_grade'].notna().sum())
progress_n=int(combined['progress'].notna().sum())
if current_n and progress_n < current_n:
    st.info(f'**Progress coverage:** {progress_n:,} of {current_n:,} current-grade assessment results have a classified progress comparison ({100*progress_n/current_n:.0f}%). Some records are excluded because a baseline is missing or grade equivalence is unapproved. Expand the Progress coverage panel to review the exclusions by year and subject.')

with st.expander('Progress coverage and excluded results · check before using progress judgements', expanded=(view=='School Overview')):
    st.caption('Counts show distinct students with a valid CURRENT grade, not total enrolment. Unclassified progress is excluded from KHDA-style progress percentages; missing baselines and unsupported grade conversions are shown separately.')
    audit=progress_coverage(combined,by=('year','category'))
    if not audit.empty:
        cols=['year','category','Students with current grade','Students with baseline and current','Progress classified','Current grade, baseline missing','Grade conversion not approved','From optional mapping','% progress coverage']
        audit=audit[cols].rename(columns={'year':'Year','category':'Subject'})
        st.dataframe(audit,hide_index=True,use_container_width=True)
        low=audit.loc[(audit['Students with current grade']>=5)&(audit['% progress coverage']<75)]
        if not low.empty:st.warning(f'{len(low)} subject/year rows have progress coverage below 75%. Review their missing baselines and grade equivalences before interpreting progress judgements.')
        st.download_button('Download aggregate progress coverage · Excel',excel_bytes(audit),'DBSJP_Progress_Coverage.xlsx',key='progress_coverage_download')

st.markdown(f'<div class="db-strip"><b>Current selection</b> · {escape(coverage_status(data))} <br><span class="db-small">{len(data):,} subject records; {data.student_id.nunique():,} distinct students. Method: {"unweighted subject averages" if method=="unweighted" else "pooled assessment records"}.</span></div>',unsafe_allow_html=True)

with st.expander('Data quality and assessment-source coverage', expanded=False):
    q=assessment_coverage(data,base,cur)
    qcols=st.columns(4)
    for col,label,value in zip(qcols,['Valid current grades','Baseline grades found','Comparable progress results','Current fallback used'],
                               [q['current_grade'],q['baseline_grade'],q['valid_progress'],q['current_from_fallback']]):
        labelled_metric(col,label,f'{value:,}')
    st.caption(f'Of {q["records"]:,} subject records, {q["both_grade_fields"]:,} have both grade fields and {q["valid_progress"]:,} produce comparable progress. {q["baseline_from_fallback"]:,} baseline results came from the fallback. A valid grade pair is not automatically a valid cross-grade-set comparison.')
    if records.duplicated(['student_id','year','subject']).any():
        st.error('Duplicate student/year/subject combinations found in the upload. Resolve these before sharing reports.')

if view=='School Overview':
    st.markdown('## School overview')
    st.caption('A leadership summary for the uploaded year groups, not an official whole-school total unless all year groups are included.')
    all_stats=filtered_cohort_summary(combined,method)
    kpis=[('Meeting or above',percentage_label(all_stats.get('at_or_above'))),('Exceeding',percentage_label(all_stats.get('above'))),('Expected or better',percentage_label(all_stats.get('expected_plus'))),('Better than expected',percentage_label(all_stats.get('better')))]
    cols=st.columns(4)
    for col,(label,value) in zip(cols,kpis):labelled_metric(col,label,value)
    stats=summarise(combined,('category',),method)
    a,b=st.columns([1.6,1])
    with a:
        st.markdown('#### Subject performance')
        measure=st.radio('Show',['Attainment','Progress'],horizontal=True,key='overview_graph_measure')
        order=st.radio('Show first',['Needs attention','Highest performance'],horizontal=True,key='overview_chart_order')
        st.plotly_chart(metric_bars(stats,measure.lower(),priority='lowest' if order=='Needs attention' else 'highest'),use_container_width=True,config={'displaylogo':False})
    with b:
        st.markdown('#### KHDA judgement mix')
        st.caption('Number of reporting subjects in each judgement band.')
        st.plotly_chart(judgement_mix(stats,'attainment_judgement' if measure=='Attainment' else 'progress_judgement'),use_container_width=True,config={'displaylogo':False})
    with st.expander('Key findings from the selected data',expanded=True):
        for finding in narrative_findings(stats):st.markdown('• '+finding)
        st.caption('Descriptive findings only. Investigate the underlying students and assessments before deciding on interventions.')
    st.markdown('### Detailed results')
    show_performance_tables(combined,('category',),'overview')

elif view=='Subject Analysis':
    st.markdown('## Subject analysis')
    st.caption('Compare individual subjects, subject combinations or year groups. Change the focus without re-uploading.')
    scope=st.radio('Breakdown',['Subject by year','Combined subject by year','Year-group comparison'],horizontal=True)
    by={'Subject by year':('subject','year'),'Combined subject by year':('category','year'),'Year-group comparison':('year','category')}[scope]
    frame=data if scope=='Subject by year' else combined
    stats=summarise(frame,by,method)
    if not stats.empty:
        c1,c2=st.columns([2,1])
        with c1:
            st.markdown('#### At or above curriculum standard')
            plotted=stats.copy()
            plotted['label']=[f"{r.get('subject',r.get('category',''))} · Y{r['year']}" for _,r in plotted.iterrows()]
            chart=plotted.rename(columns={'label':'category'}) if 'category' not in plotted else plotted
            # Use unique subject/year labels for comparative plots.
            chart=plotted.drop(columns=['category'],errors='ignore').rename(columns={'label':'category'})
            priority=st.radio('Sort by',['Needs attention','Highest performance'],horizontal=True,key='subject_chart_order')
            st.plotly_chart(metric_bars(chart,'attainment',limit=16,priority='lowest' if priority=='Needs attention' else 'highest'),use_container_width=True,config={'displaylogo':False})
        with c2:
            st.markdown('#### Assessment coverage')
            st.metric('Students',f'{frame.student_id.nunique():,}')
            st.metric('Valid current grades',f'{frame.attainment.notna().sum():,}')
            st.metric('Valid progress pairs',f'{frame.progress.notna().sum():,}')
            st.caption('The counts may differ because a progress result requires both comparable assessments.')
    with st.expander('Explore the grade distribution for one subject', expanded=False):
        subject_choices=sorted(data.subject.dropna().unique())
        chosen_sub=st.selectbox('Subject',subject_choices,key='distribution_subject')
        year_choices=sorted(int(y) for y in data.loc[data.subject.eq(chosen_sub),'year'].unique())
        chosen_y=st.selectbox('Year group',year_choices,key='distribution_year')
        sample=data.loc[data.subject.eq(chosen_sub)&data.year.eq(chosen_y)]
        counts=attained_grade_counts(sample)
        if counts.empty:
            st.info('No valid grade distribution for this subject and year group.')
        else:
            st.plotly_chart(grade_distribution_chart(counts),use_container_width=True,config={'displaylogo':False})
            st.caption(f'{len(sample):,} assessment records in scope · {int(counts.Count.sum()):,} valid graded results. Different grade sets must be interpreted using their approved qualification definitions.')
    st.markdown('### Subject breakdown')
    show_performance_tables(frame,by,'subjects')

elif view=='PPM & Interventions':
    st.markdown('## PPM & Interventions')
    st.caption('Find students who may need discussion. These are assessment indicators, not risk diagnoses.')
    concerns=['Below standard','Below target','Less progress','Grade decline']
    k=st.columns(4)
    for col,flag in zip(k,concerns):
        count=int(data['concerns'].fillna('').str.contains(re.escape(flag),regex=True).sum())
        labelled_metric(col,flag,str(count))
    with st.expander('Which subjects have the most students with concerns?', expanded=False):
        hotspots=ppm_subject_hotspots(data)
        if hotspots.empty:st.info('No recorded concerns in the selection.')
        else:
            hot=hotspots.iloc[::-1]
            chart=go.Figure(go.Bar(y=hot['Subject'],x=hot['Students with concerns'],orientation='h',marker_color='#367f95',text=hot['Students with concerns'],textposition='outside',hovertemplate='%{y}: %{x} distinct students<extra></extra>'))
            chart.update_layout(template='plotly_white',height=max(260,65+len(hot)*36),margin=dict(l=6,r=30,t=8,b=8),paper_bgcolor='rgba(0,0,0,0)')
            chart.update_xaxes(title='Students with at least one concern',dtick=1,showgrid=True,gridcolor='#eef1f5')
            st.plotly_chart(chart,use_container_width=True,config={'displaylogo':False})
            st.caption('These are distinct students per subject. A student may appear in more than one subject, so do not sum the bars to estimate distinct students across the school.')
    st.markdown('### Prioritise students')
    c1,c2=st.columns([2,1])
    with c1:selected_concerns=st.multiselect('Show concern types',concerns,default=concerns)
    with c2:minimum=st.selectbox('Minimum subjects with concerns',[1,2,3,4],index=0)
    if selected_concerns:
        selection=data.loc[data.concerns.fillna('').map(lambda c:any(x in c.split(', ') for x in selected_concerns))].copy()
    else:selection=data.iloc[0:0].copy()
    ranked=ppm_subject_counts(selection)
    ranked=ranked.loc[ranked['Subjects with concerns']>=minimum]
    st.caption(f'{len(ranked):,} students identified within the selected filters · Multiple concern flags may relate to the same student.')
    st.dataframe(ranked.rename(columns={'student_id':'Student ID','year':'Year'}),hide_index=True,use_container_width=True,height=min(420,115+len(ranked)*34))
    c1,c2=st.columns([2,1])
    with c1:
        st.markdown('#### Students behind the findings')
        view_list=selection[selection.student_id.isin(ranked.student_id)]
        cols=['student_id','year','subject','baseline_grade','current_grade','target_grade','challenge_grade','attainment','progress','concerns']
        rename={'student_id':'Student ID','year':'Year','subject':'Subject','baseline_grade':'Baseline','current_grade':'Current','target_grade':'Target','challenge_grade':'Challenge','attainment':'Attainment','progress':'Progress','concerns':'Reason for discussion'}
        shown=view_list[cols].rename(columns=rename)
        st.dataframe(shown,hide_index=True,use_container_width=True,height=min(500,130+len(shown)*34))
    with c2:
        st.markdown('#### PPM meeting support')
        st.write('Start with students appearing across multiple subjects. Then inspect the source grades and select appropriate actions.')
        st.download_button('Download PPM list · Excel',excel_bytes(shown),'DBSJP_PPM_Students.xlsx',key='ppm_rows_dl')
        st.download_button('Download student priorities · Excel',excel_bytes(ranked),'DBSJP_PPM_Priorities.xlsx',key='ppm_rank_dl')
    with st.expander('Inspect one student and their subject evidence', expanded=False):
        if ranked.empty:
            st.info('No students meet the selected intervention criteria.')
        else:
            choices=ranked.student_id.astype(str).tolist()
            chosen_student=st.selectbox('Student identifier',choices,key='ppm_inspect_student')
            evidence=data.loc[data.student_id.astype(str).eq(chosen_student)].copy()
            detailcols=['year','subject','baseline_grade','current_grade','target_grade','challenge_grade','attainment','progress','decline','concerns','baseline_source','current_source']
            st.dataframe(evidence[detailcols].rename(columns={'year':'Year','subject':'Subject','baseline_grade':'Baseline','current_grade':'Current','target_grade':'Target','challenge_grade':'Challenge','attainment':'Attainment','progress':'Progress','decline':'Grade decline','concerns':'Concern indicators','baseline_source':'Baseline source','current_source':'Current source'}),hide_index=True,use_container_width=True)
            st.caption('Source columns are shown for auditability. An intervention decision should be made by staff, not by the dashboard.')
    st.caption('Student-level exports are for synthetic data only in this development build. Production requires role-based permissions and school-approved infrastructure.')

elif view=='Student Groups':
    st.markdown('## Student groups')
    options=[c for c in GROUP_FIELDS if c in data and data[c].notna().any()]
    if not options:st.info('No populated student-group columns were found in these uploads.')
    else:
        dimension=st.selectbox('Compare student groups',options)
        measure=st.radio('Measure',['At / above standard','Above standard','Expected or better','Better than expected'],horizontal=True)
        metric=dict(zip(['At / above standard','Above standard','Expected or better','Better than expected'],['at_or_above','above','expected_plus','better']))[measure]
        work=combined.copy();work[dimension]=work[dimension].fillna('Not recorded').astype(str)
        overview=summarise(work,(dimension,'category'),method)
        st.plotly_chart(group_compare(overview,dimension,metric),use_container_width=True,config={'displaylogo':False})
        cols=[dimension,'category','students',metric,metric+'_n','attainment_judgement' if metric in ('at_or_above','above') else 'progress_judgement']
        table=overview[cols].copy()
        pct=metric
        table[pct]=table[pct].map(percentage_label)
        table=table.rename(columns={dimension:'Student group','category':'Subject','students':'Students',metric:measure,metric+'_n':'Valid results',cols[-1]:'KHDA grade'})
        st.markdown(grade_legend_html(),unsafe_allow_html=True)
        table_display(table)
        st.download_button('Download group comparison · Excel',excel_bytes(table),'DBSJP_Groups.xlsx',key='groups_dl')
        st.caption('Groups can overlap. Small cohorts require appropriate confidentiality safeguards; a calculated KHDA judgement requires five eligible assessment records.')

elif view=='Value Added & CAT4':
    st.markdown('## Value Added & CAT4')
    st.caption('Standard and challenge targets use separate valid denominators. Value added is actual minus target grade points.')
    summary=summarise(combined,('category','year'),method)
    if not summary.empty:
        chosen=summary.copy()
        chosen['Subject']=chosen['category'];chosen['Year']=chosen['year']
        chosen['Met CAT4']=chosen['met_cat4'].map(percentage_label)
        chosen['Met challenge']=chosen['met_cat4_75'].map(percentage_label)
        chosen['Mean VA']=chosen['va'].map(lambda x: '—' if pd.isna(x) else f'{x:+.2f}')
        shown=chosen[['Subject','Year','met_cat4_n','Met CAT4','met_cat4_75_n','Met challenge','Mean VA']].rename(columns={'met_cat4_n':'Target pairs','met_cat4_75_n':'Challenge pairs'})
        st.dataframe(shown,hide_index=True,use_container_width=True)
        st.markdown('#### Mean grade difference by subject')
        good=summary.loc[summary.va.notna()].copy()
        if not good.empty:
            good['label']=good.category.astype(str)+' · Y'+good.year.astype(str)
            good=good.sort_values('va').tail(18)
            fig=go.Figure(go.Bar(y=good.label,x=good.va,orientation='h',marker_color=['#cc7878' if x<0 else '#328c8c' for x in good.va],text=good.va.map(lambda x:f'{x:+.2f}'),textposition='outside'))
            fig.update_layout(template='plotly_white',height=max(300,70+len(good)*36),margin=dict(l=8,r=60,t=25,b=5),paper_bgcolor='rgba(0,0,0,0)')
            fig.update_xaxes(zeroline=True,zerolinewidth=2,zerolinecolor='#7b8b99')
            st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False})
        st.download_button('Download CAT4 analysis · Excel',excel_bytes(shown),'DBSJP_CAT4_VA.xlsx',key='cat_dl')

elif view=='Exam Results':
    st.markdown('## Examination results')
    st.info('Public examination analysis is planned. This version does not present internal DCPro grades as official GCSE, IGCSE, BTEC or A Level outcomes.')
    st.write('The next import will support exact-grade distributions, cumulative thresholds and the selected examination session.')

else:
    st.markdown('## Reports & Data Pack')
    st.warning('The historical 87-table Data Pack is not yet implemented. The available PDF is an aggregate assessment summary for the selected uploaded data.')
    s=summarise(combined,('category','year'),method)
    shown=s[['category','year','students','at_or_above','above','expected_plus','better','attainment_judgement','progress_judgement']].copy().rename(columns={'category':'Subject','year':'Year','students':'Students','at_or_above':'Meeting+','above':'Exceeding','expected_plus':'Expected+','better':'Better+','attainment_judgement':'Attainment grade','progress_judgement':'Progress grade'})
    for col in ['Meeting+','Exceeding','Expected+','Better+']:shown[col]=shown[col].map(percentage_label)
    st.dataframe(shown,hide_index=True,use_container_width=True)
    meta=f'Generated {datetime.now().strftime("%d %b %Y %H:%M")} · Baseline {base} · Current {cur} · {method} method · Uploaded years {", ".join(map(str,sorted(selected_years)))}'
    a,b=st.columns(2)
    with a:st.download_button('Download assessment PDF',pdf_summary(s,meta),'DBSJP_Assessment_Summary.pdf',mime='application/pdf',key='pdf_dl')
    with b:st.download_button('Download results Excel',excel_bytes(shown),'DBSJP_Assessment_Summary.xlsx',key='summary_excel_dl')
    st.radio('Future full Data Pack: empty tables',['Include empty tables','Remove completely empty tables'],horizontal=True)
    st.caption('The empty-table option is a specification for the future Data Pack Builder and does not affect the current summary PDF.')

with st.expander('Methodology, caveats and access restrictions'):
    st.markdown('''- **Upload scope:** these results are for uploaded year groups, not automatically whole-school data.
- **Counts:** *Number* counts unique students with valid grades; combined category percentages may count multiple valid subject-assessment records per student.
- **Judgements:** DBSJP KHDA-style calculations round half-up to whole percentages and require at least five valid assessment results; they are not official inspection grades.
- **Progress:** unsupported grade-system comparisons remain unclassified. KS3 ME → GCSE 4 is an approved expected-progress case.
- **Grade conversions:** cross-qualification mappings remain provisional and require approval before live use.
- **Privacy:** student-level information is not approved for deployment here. No Microsoft 365 login or role-based authorisation has been implemented. Use synthetic data only until IT approval.''')
