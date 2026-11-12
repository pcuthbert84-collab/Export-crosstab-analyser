"""DBSJP Data Intelligence — working V1 prototype. Sensitive-data approval required for production."""
import io
import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from engine import parse_dcpro, derive, summarise, english_overlap, GROUP_FIELDS
from overview_tables import summary_tables, compact_table, detail_table

st.set_page_config(page_title='DBSJP Data Intelligence',page_icon='📊',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
:root {--accent:#0b7285;} .block-container {padding-top:1.25rem;max-width:1440px}
[data-testid="stMetric"]{border:1px solid #dbe6eb;border-radius:14px;padding:14px}
h1,h2,h3{letter-spacing:-.02em} .stButton button{border-radius:9px}
[data-testid="stSidebar"]{border-right:1px solid #dbe6eb}
</style>''',unsafe_allow_html=True)

def load_excel(content, filename):
    book=pd.ExcelFile(io.BytesIO(content))
    dfs=[pd.read_excel(book,sheet_name=sheet,dtype=object) for sheet in book.sheet_names]
    return [(sheet,df) for sheet,df in zip(book.sheet_names,dfs)]

def grade_fields(df):
    return sorted({str(c).split(',',1)[1].strip() for c in df.columns if ',' in str(c) and any(x in str(c).lower() for x in ('cpl','/ ag','target','exam','mock'))})

def auto_select(items,match,default=0):
    for i,x in enumerate(items):
        if match.lower() in str(x).lower():return i
    return min(default,len(items)-1)

def ebytes(df):
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine='openpyxl') as w:df.to_excel(w,index=False,sheet_name='Results')
    return output.getvalue()

def pdf_summary(summary,metadata):
    b=io.BytesIO();doc=SimpleDocTemplate(b,pagesize=landscape(A4),leftMargin=35,rightMargin=35,topMargin=38,bottomMargin=38)
    styles=getSampleStyleSheet();elements=[Paragraph('DBSJP | Assessment Intelligence Summary',styles['Title']),Spacer(1,10),Paragraph(metadata,styles['Normal']),Spacer(1,16)]
    if summary.empty:
        elements.append(Paragraph('No calculable results available.',styles['Normal']))
    else:
        columns=[x for x in ('category','year','subject','records','students','at_or_above','above','expected_plus','better','met_cat4','met_cat4_75','va','attainment_judgement','progress_judgement') if x in summary.columns]
        headers={'category':'Category','year':'Year','subject':'Subject','records':'Results','students':'Students','at_or_above':'At+ %','above':'Above %','expected_plus':'Expected+ %','better':'Better %','met_cat4':'Met CAT4 %','met_cat4_75':'CAT4 75 %','va':'Mean VA','attainment_judgement':'Attainment','progress_judgement':'Progress'}
        for start in range(0,len(summary),23):
            chunk=summary.iloc[start:start+23]
            cells=[[headers.get(c,c) for c in columns]]
            for _,r in chunk.iterrows():
                vals=[]
                for c in columns:
                    v=r[c]
                    if pd.isna(v):v=''
                    elif isinstance(v,float):v=f'{v:.1f}'
                    vals.append(str(v)[:32])
                cells.append(vals)
            widths=[min(105, 760/len(columns)) for _ in columns]
            t=Table(cells,repeatRows=1,colWidths=widths,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0c6174')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),0.3,colors.HexColor('#e5e7eb')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f8fa')])]))
            elements.append(t)
            if start+23<len(summary):elements.append(PageBreak())
    doc.build(elements);return b.getvalue()

def display_kpis(summary):
    if summary.empty:return
    keys=[('at_or_above','At / above standard'),('above','Above standard'),('expected_plus','Expected+ progress'),('better','Better progress')]
    cols=st.columns(4)
    for panel,(k,label) in zip(cols,keys):
        vals=summary[k].dropna()
        # A single category chart is not an official pooled whole-school aggregate.
        panel.metric(label,f'{vals.iloc[0]:.0f}%' if len(vals)==1 else 'See breakdown')


def judgement_row_style(df):
    color_map = {
        'Outstanding': '#cfe2ff',
        'Very Good': '#d9ead3',
        'Good': '#fff2cc',
        'Acceptable': '#fce5cd',
        'Weak': '#f4cccc',
    }
    khda_col = 'KHDA grade' if 'KHDA grade' in df.columns else None
    def style_row(row):
        grade = row.get(khda_col, '') if khda_col else ''
        bg = color_map.get(grade, '')
        return [f'background-color: {bg}' if bg else '' for _ in row]
    return df.style.apply(style_row, axis=1)


def show_table(df, height=None):
    st.dataframe(judgement_row_style(df), hide_index=True, use_container_width=True, height=height)

st.title('DBSJP Data Intelligence')
st.caption('V1 prototype · Subject analysis · PPM & Interventions · Group analysis · CAT4 & Value Added · Session-only data')
st.info('DEVELOPMENT PROTOTYPE: Use fictional or properly anonymised data only. Microsoft 365 access controls and approved live-data hosting are not implemented. Do not upload identifiable student records to a public Streamlit Community Cloud deployment.',icon='🔒')

with st.sidebar:
    st.header('1 · Upload DCPro')
    uploads=st.file_uploader('Year-group Excel files',type=['xlsx'],accept_multiple_files=True,help='One workbook per year group. Supported input: DCPro crosstab exports.')
    st.caption('Uploaded files are used for this session. The app itself does not save student spreadsheets to disk.')
    st.divider()
    st.header('2 · Workspace')
    view=st.radio('Choose dashboard',['School Overview','Subject Analysis','PPM & Interventions','Student Groups','Value Added & CAT4','Exam Results (preview)','Reports & Data Pack'],label_visibility='collapsed')

if not uploads:
    st.subheader('Getting started')
    st.write('Upload one or more DCPro Excel workbooks using the sidebar. Confirm the year group for each file, then select the preferred and fallback assessment points. The app builds subject-level results and PPM intervention lists without storing student data.')
    left,right=st.columns(2)
    with left:
        st.markdown('**Available in this first build**')
        st.markdown('- Individual subject and combined-category analysis\n- Preferred/fallback baseline and current grades\n- Attainment, progress and DBSJP KHDA-style judgements\n- Met CAT4, Met CAT4 75 and mean grade value added\n- PPM student concern lists and Excel export\n- Basic aggregate PDF summary')
    with right:
        st.markdown('**Planned subsequent versions**')
        st.markdown('- Fully mapped historical Data Pack PDF\n- EYFS, GL and NGRT data\n- Microsoft 365 authentication and approved production hosting\n- Complete GCSE/BTEC/A Level exam imports\n- Approved cross-qualification mappings')
    st.stop()

st.subheader('Upload confirmation')
loaded=[]
for i,file in enumerate(uploads):
    try:sheets=load_excel(file.getvalue(),file.name)
    except Exception as e:st.error(f'{file.name}: Unable to read workbook ({e})');continue
    with st.expander(f'{file.name} · {len(sheets)} sheet(s)',expanded=len(uploads)<=2):
        year=st.selectbox('Confirm year group',list(range(1,14)),index=min([5,8,11,12][i%4]-1,12),key=f'y_{i}')
        chosen_sheets=st.multiselect('Sheets to include',[name for name,_ in sheets],default=[sheets[0][0]],key=f's_{i}')
        for name,df in sheets:
            if name in chosen_sheets:
                st.caption(f'Sheet {name}: {len(df)} student rows, {len(df.columns)} columns')
                loaded.append(parse_dcpro(df,year,file.name))
if not loaded or not any(not x.empty for x in loaded):st.warning('No usable subject assessment columns found.');st.stop()
records=pd.concat(loaded,ignore_index=True)
if records.duplicated(['student_id','year','subject']).any():
    st.warning('Duplicate student/year/subject records found across uploads. Check that overlapping files or sheets have not been uploaded twice.')

fields=sorted({x for x in records.columns if x not in ('student_id','year','phase','subject','category','source',*GROUP_FIELDS) and any(s in x.lower() for s in ('cpl','ag','exam','mock','target'))})
assess=[x for x in fields if 'target' not in x.lower()]
targets=[x for x in fields if 'target' in x.lower()]
if not assess:st.error('No assessment-grade columns detected.');st.stop()

with st.expander('3 · Assessment-point and target configuration',expanded=True):
    st.caption('Priority 2 is used only when Priority 1 has no valid grade for a particular student and subject.')
    a,b,c,d=st.columns(4)
    with a:base=st.selectbox('Baseline · priority 1',assess,index=auto_select(assess,'DP3'))
    with b:base2=st.selectbox('Baseline · priority 2',['None']+assess,index=1+auto_select(assess,'exam') if any('exam' in x.lower() for x in assess) else 0)
    with c:cur=st.selectbox('Current · priority 1',assess,index=auto_select(assess,'DP1'))
    with d:cur2=st.selectbox('Current · priority 2',['None']+assess,index=1+auto_select(assess,'mock') if any('mock' in x.lower() for x in assess) else 0)
    a,b=st.columns(2)
    with a:tar=st.selectbox('CAT4 target (standard)', ['None']+targets,index=next((i+1 for i,x in enumerate(targets) if x.lower().startswith('target')),0))
    with b:cha=st.selectbox('CAT4 75 (challenge)', ['None']+targets,index=1+auto_select(targets,'Challenge') if targets else 0)
    st.caption('Some grade equivalences are awaiting approval. Cross-grade-set cases without approved rules are left unclassified.')

computed=derive(records,base,None if base2=='None' else base2,cur,None if cur2=='None' else cur2,None if tar=='None' else tar,None if cha=='None' else cha)
if computed.empty:st.warning('No calculations available.');st.stop()

with st.expander('Filters',expanded=False):
    phase_labels = {1:'Phase 1 · FS1–FS2 (Version 2)', 2:'Phase 2 · Years 1–6', 3:'Phase 3 · Years 7–11', 4:'Phase 4 · Years 12–13'}
    selected_phases=st.multiselect('Phases',options=[1,2,3,4],default=[1,2,3,4],format_func=lambda p:phase_labels[p],help='Select one or more school phases. Phase 1 (EYFS) data processing is planned for Version 2.')
    selected_years=st.multiselect('Year groups',sorted(computed.year.unique()),default=sorted(computed.year.unique()))
    selected_cats=st.multiselect('Subject categories',sorted(computed.category.unique()),default=sorted(computed.category.unique()))
    selected_subs=st.multiselect('Individual subjects',sorted(computed.subject.unique()),default=sorted(computed.subject.unique()))
    method=st.radio('Combined-category calculation',['Pooled subject results','Unweighted subject percentages'],horizontal=True)
    group_filters={}
    grpcols=[c for c in GROUP_FIELDS if c in computed.columns and computed[c].notna().any()]
    if grpcols:
        st.caption('Additional student-group filters (combine filters to narrow the population)')
        for col in grpcols:
            values=sorted(computed[col].dropna().astype(str).unique())
            choice=st.multiselect(col,values,key=f'gf_{col}')
            if choice:group_filters[col]=choice

data=computed[computed.phase.isin(selected_phases)&computed.year.isin(selected_years)&computed.category.isin(selected_cats)&computed.subject.isin(selected_subs)].copy()
for col,choices in group_filters.items():data=data[data[col].astype(str).isin(choices)]
if data.empty:
    if selected_phases==[1]:
        st.info('Phase 1 (FS1–FS2) has been selected. EYFS assessment processing will be added in Version 2, so no Phase 1 results are available in this version.')
    else:
        st.warning('No subject results match the selected phase, year group, subject and student-group filters.')
    st.stop()

# Suppress duplicate Reading and Writing records in the combined English headline only.
combined=pd.concat([data[data.category!='English'],english_overlap(data)],ignore_index=True)
met=('unweighted' if method.startswith('Unweighted') else 'pooled')

def clean_performance_tables(source, by, selector_key):
    """Compact/detailed attainment and progress, each using its own valid denominator."""
    att,prog,grade_dist=summary_tables(source,by,met)
    if att.empty:
        st.info('No results match the current filters.')
        return
    t_att,t_prog=st.tabs(['Attainment','Progress'])
    with t_att:
        mode=st.radio('Table view',['Compact','Detailed'],horizontal=True,key=f'{selector_key}_att_view')
        shown=compact_table(att,by,'attainment') if mode=='Compact' else detail_table(att,by,'attainment')
        show_table(shown,height=min(580,95+len(shown)*36))
        if mode=='Detailed':
            st.caption('Grade columns show the number of valid current results in each recorded grade. Target-predicted percentages use valid standard target grades, not current results.')
            with st.expander('Grade counts and percentages (one row per grade)'):
                st.dataframe(grade_dist,hide_index=True,use_container_width=True)
        st.download_button('Download attainment Excel',ebytes(shown),'DBSJP_Attainment.xlsx',key=f'{selector_key}_att_dl')
    with t_prog:
        mode=st.radio('Table view',['Compact','Detailed'],horizontal=True,key=f'{selector_key}_prog_view')
        shown=compact_table(prog,by,'progress') if mode=='Compact' else detail_table(prog,by,'progress')
        show_table(shown,height=min(580,95+len(shown)*36))
        if mode=='Detailed':
            st.caption('Progress counts require valid, comparable baseline and current grades. CAT4 percentages use only results with the relevant target, so denominators may differ.')
            with st.expander('Current grade counts and percentages'):
                st.dataframe(grade_dist,hide_index=True,use_container_width=True)
        st.download_button('Download progress Excel',ebytes(shown),'DBSJP_Progress.xlsx',key=f'{selector_key}_prog_dl')
    st.caption('Number of students counts unique students with eligible grades. Grade results count assessment records; combined categories can contain multiple results for one student. A KHDA judgement requires at least five valid results.')

if view=='School Overview':
    st.header('School overview')
    st.caption('Results for uploaded year groups only — not automatically whole-school totals.')
    clean_performance_tables(combined,('category',),'overview')
elif view=='Subject Analysis':
    st.header('Subject analysis')
    scope=st.radio('Break down by',['Subject and year','Category and year','Year and category'],horizontal=True)
    by={'Subject and year':('subject','year'),'Category and year':('category','year'),'Year and category':('year','category')}[scope]
    targetdata=data if scope=='Subject and year' else combined
    clean_performance_tables(targetdata,by,'subject')
elif view=='PPM & Interventions':
    st.header('PPM & Interventions')
    st.caption('Individual results, not a diagnosis or automated risk score. Several concern indicators may overlap.')
    x,y,z=st.columns(3)
    x.metric('Below standard',int((data.attainment=='Below').sum()))
    y.metric('Below target',int((data.met_cat4==False).sum()))
    z.metric('Grade declines',int((data.decline==True).sum()))
    concerns=['Below standard','Below target','Less progress','Grade decline']
    selected=st.multiselect('Concern types',concerns,default=concerns)
    selectedrows=data[data.concerns.apply(lambda s:any(tag in str(s).split(', ') for tag in selected))] if selected else data
    st.dataframe(selectedrows[['student_id','year','subject','baseline_grade','current_grade','target_grade','challenge_grade','attainment','progress','value_added','concerns','concern_count']].sort_values('concern_count',ascending=False),hide_index=True,use_container_width=True)
    st.subheader('Multi-subject student summary')
    students=selectedrows.groupby(['student_id','year'],as_index=False).agg(subjects=('subject','nunique'),subject_concerns=('concern_count','sum'))
    st.dataframe(students.sort_values('subject_concerns',ascending=False),hide_index=True,use_container_width=True)
    st.download_button('Download PPM intervention list',ebytes(selectedrows),'DBSJP_PPM_Interventions.xlsx')
elif view=='Student Groups':
    st.header('Student group analysis')
    available=[c for c in grpcols if c in data.columns]
    if not available:st.info('No populated student-group columns were found.')
    else:
        group=st.selectbox('Compare by',available)
        copy=data.copy();copy[group]=copy[group].fillna('Not recorded').astype(str)
        summary=summarise(copy,(group,'category'),met)
        st.dataframe(summary,hide_index=True,use_container_width=True)
        st.caption('Judgements are withheld where fewer than five valid assessment records exist. Apply school privacy rules before distributing small-cohort reports.')
        st.download_button('Download group analysis',ebytes(summary),'DBSJP_Groups.xlsx')
elif view=='Value Added & CAT4':
    st.header('Value Added & CAT4 target analysis')
    st.caption('Met CAT4 uses the standard target; Met CAT4 75 uses the challenge target. Denominators differ when target availability differs.')
    summary=summarise(combined,('category','year'),met)
    st.dataframe(summary[['category','year','records','met_cat4','met_cat4_n','met_cat4_75','met_cat4_75_n','va']],hide_index=True,use_container_width=True)
    st.download_button('Download target and VA analysis',ebytes(summary),'DBSJP_CAT4_Value_Added.xlsx')
elif view=='Exam Results (preview)':
    st.header('Examination Results — early preview')
    st.info('Dedicated public-examination import, validated qualification-specific grade sets and official distributions are scheduled for the next build. Do not treat internal DP grades as confirmed GCSE/A Level outcomes.')
    st.write('The planned release will support exact grade percentages, cumulative thresholds and one selected exam session, including ordered Combined Science grade pairs.')
else:
    st.header('Reports & Data Pack')
    st.warning('The complete 87-table historical Data Pack is not yet implemented. This build exports an accurate summary of the data actually uploaded; it does not present itself as a completed inspection Data Pack.')
    summary=summarise(combined,('category','year'),met)
    st.dataframe(summary,hide_index=True,use_container_width=True)
    pdf=pdf_summary(summary,f'Generated {datetime.now().strftime("%d %b %Y %H:%M")} · Current: {cur} · Baseline: {base} · {method}')
    st.download_button('Download assessment summary PDF',pdf,'DBSJP_Assessment_Summary.pdf',mime='application/pdf')
    st.download_button('Download summary Excel',ebytes(summary),'DBSJP_Assessment_Summary.xlsx')
    include=st.radio('Future full Data Pack export: empty tables',['Include empty tables','Remove completely empty tables'],horizontal=True)
    st.caption(f'Saved design preference for the future Data Pack Builder: {include}. This setting does not alter the current summary PDF.')

with st.expander('Methods and important limitations'):
    st.markdown('''- **Percentages** exclude records without a valid grade for the particular measure. Counts for combined categories represent assessment records, not necessarily unique students.
- **Whole-number KHDA-style judgements** use half-up rounding and a minimum of five valid assessment records. They are calculated DBSJP indicators, not official KHDA verdicts.
- **Progress** is not calculated for unsupported cross-qualification comparisons. The approved exception KS3 ME → GCSE 4 is treated as expected.
- **Grade mapping** is provisional for non-GCSE qualifications until the school's complete equivalences and curriculum-year transition rules are approved.
- **Data protection**: session processing is a design goal, not a guarantee that public deployment satisfies school data protection requirements. Use fictitious/synthetic data until production controls are approved.''')
