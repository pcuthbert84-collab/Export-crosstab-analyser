"""DBSJP presentation building blocks. Charts intentionally contain aggregate data only."""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from dashboard_analytics import GRADE_COLORS, GRADE_TEXT

NAV_ITEMS=[
    ('School Overview','layout-dashboard','Headline results, judgements and trends'),
    ('Subject Analysis','bar-chart-3','Compare subjects and year groups'),
    ('PPM & Interventions','users','Find students and action priorities'),
    ('Student Groups','users-round','Compare cohorts fairly'),
    ('Value Added & CAT4','target','Track performance against targets'),
    ('Exam Results','graduation-cap','Public results — planned'),
    ('Reports & Data Pack','file-text','Download leadership summaries'),
]

THEME_CSS="""
<style>
:root{--db-navy:#15364d;--db-teal:#087f8c;--db-muted:#5f7183;--db-line:#e2eaf1;--db-bg:#f6f9fc}
.block-container{max-width:1600px;padding-top:1.4rem;padding-bottom:2rem}
[data-testid="stAppViewContainer"]{background:#f8fafc}
[data-testid="stSidebar"]{background:#f0f5f8;border-right:1px solid #dce6ed}
[data-testid="stSidebar"] [data-testid="stRadio"] label{font-size:0.92rem}
[data-testid="stVerticalBlockBorderWrapper"]:has(.db-section){border-radius:14px}
h1,h2,h3{color:#173a50;letter-spacing:-0.025em}
h1{font-weight:750}h2{font-weight:730}h3{font-weight:680}
[data-testid="stMetric"]{background:#fff;padding:0.85rem 1rem;border:1px solid #e0e8f0;border-radius:14px;box-shadow:0 3px 12px rgba(20,44,70,.035)}
[data-testid="stMetricLabel"]{color:#567084}
[data-testid="stMetricValue"]{color:#183c52;font-size:1.9rem}
.stButton button,.stDownloadButton button{border-radius:10px;font-weight:600}
[data-testid="stExpander"]{border-color:#dce6ed;background:#fff;border-radius:13px}
[data-testid="stTabs"] [data-baseweb="tab-list"]{gap:1rem}
[data-testid="stTabs"] [data-baseweb="tab"]{font-weight:650}
.db-eyebrow{color:#087f8c;font-weight:750;font-size:.77rem;letter-spacing:.12em;text-transform:uppercase}
.db-hero{background:linear-gradient(115deg,#113952,#1c6773);padding:24px 28px;border-radius:19px;color:#fff;margin-bottom:18px}
.db-hero h1{color:white;font-size:2rem;margin:0 0 .25rem 0}
.db-hero p{color:#dcedf0;margin:0;font-size:.95rem}
.db-section{font-size:1.2rem;font-weight:750;color:#173a50;margin-top:9px}
.db-note{color:#607387;font-size:.88rem;line-height:1.5}
.db-legend{display:flex;flex-wrap:wrap;gap:7px 12px;margin:.5rem 0 1rem}
.db-pill{display:inline-block;border-radius:999px;padding:5px 11px;font-size:.78rem;font-weight:650}
.db-strip{background:#eaf4f5;border-left:4px solid #1a8290;padding:12px 14px;border-radius:0 10px 10px 0;margin:.65rem 0 1rem}
.db-small{font-size:.8rem;color:#627789}
</style>
"""


def row_style(df):
    """Colours entire KHDA-rated row; unmatched rows remain neutral."""
    col='KHDA grade' if 'KHDA grade' in df.columns else 'Attainment grade' if 'Attainment grade' in df.columns else 'Progress grade' if 'Progress grade' in df.columns else None
    def per_row(row):
        grade = str(row[col]) if col else ''
        bg=GRADE_COLORS.get(grade)
        css=f'background-color: {bg}; color: {GRADE_TEXT.get(grade,"#26394b")};' if bg else ''
        return [css for _ in row]
    return df.style.apply(per_row,axis=1)


def grade_legend_html():
    return '<div class="db-legend">'+''.join(
        f'<span class="db-pill" style="background:{GRADE_COLORS[g]};color:{GRADE_TEXT[g]}">{g}</span>'
        for g in ['Outstanding','Very Good','Good','Acceptable','Weak'])+'</div>'


def _layout(fig, height=360, *, horizontal=True):
    fig.update_layout(
        template='plotly_white',height=height,margin=dict(l=8,r=26,t=16,b=10),
        font=dict(family='Arial, sans-serif',color='#2d4458',size=12),
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h',yanchor='bottom',y=1.02,x=0),
        hoverlabel=dict(bgcolor='white',font_size=12),
        bargap=.24,
    )
    fig.update_xaxes(showgrid=False,zeroline=False,showline=False)
    fig.update_yaxes(showgrid=False,zeroline=False,showline=False)
    return fig


def metric_bars(summary, mode='attainment', limit=12, priority='lowest'):
    """Comparative horizontal bars, with a clear axis and valid-denominator hover."""
    if summary is None or summary.empty:return go.Figure()
    a,b=('at_or_above','above') if mode=='attainment' else ('expected_plus','better')
    alabel,blabel=('Meeting or above','Exceeding') if mode=='attainment' else ('Expected or better','Better than expected')
    labelcol='category' if 'category' in summary else 'subject' if 'subject' in summary else summary.columns[0]
    # For leadership reviews, default to the lowest-performing subjects first.
    part=summary.loc[summary[a].notna()].sort_values(a,ascending=(priority=='lowest')).head(limit).iloc[::-1]
    labels=part[labelcol].astype(str).tolist()
    fig=go.Figure()
    fig.add_trace(go.Bar(y=labels,x=part[a],name=alabel,orientation='h',marker_color='#2e8191',customdata=part[a+'_n'],hovertemplate='%{y}: %{x:.1f}%<br>Valid assessment results: %{customdata}<extra></extra>'))
    fig.add_trace(go.Bar(y=labels,x=part[b],name=blabel,orientation='h',marker_color='#86b1d1',customdata=part[b+'_n'],hovertemplate='%{y}: %{x:.1f}%<br>Valid assessment results: %{customdata}<extra></extra>'))
    fig.update_xaxes(range=[0,105],ticksuffix='%',dtick=25,showgrid=True,gridcolor='#e9eff4')
    fig.update_layout(barmode='group')
    return _layout(fig,height=max(270, min(650,100+len(labels)*41)))


def judgement_mix(summary, grade_col='attainment_judgement'):
    if summary is None or summary.empty or grade_col not in summary:return go.Figure()
    counts=summary[grade_col].value_counts()
    ordered=['Outstanding','Very Good','Good','Acceptable','Weak']
    names=[k for k in ordered if k in counts]
    fig=go.Figure(go.Bar(x=names,y=[counts[n] for n in names],marker_color=[GRADE_TEXT[n] for n in names],text=[int(counts[n]) for n in names],textposition='outside',hovertemplate='%{x}: %{y} subject rows<extra></extra>'))
    fig.update_yaxes(dtick=1,rangemode='tozero',showgrid=True,gridcolor='#e9eff4')
    return _layout(fig,255)


def progress_mix(data):
    if data.empty:return go.Figure()
    counts=data['progress'].value_counts()
    names=['Less','Expected','Better']
    values=[int(counts.get(n,0)) for n in names]
    fig=go.Figure(go.Bar(x=names,y=values,marker_color=['#e7a2a2','#8ec5b3','#5b9aba'],text=values,textposition='outside',hovertemplate='%{x}: %{y} assessment results<extra></extra>'))
    fig.update_yaxes(dtick=max(1,round(max(values)/5)),showgrid=True,gridcolor='#e9eff4')
    return _layout(fig,265)


def group_compare(summary, group_col, metric='at_or_above', limit=15):
    if summary.empty:return go.Figure()
    s=summary.loc[summary[metric].notna()].sort_values(metric,ascending=True).tail(limit)
    labels=s[group_col].astype(str)+' · '+s['category'].astype(str) if 'category' in s else s[group_col].astype(str)
    fig=go.Figure(go.Bar(y=labels,x=s[metric],orientation='h',marker_color='#38899b',customdata=s[metric+'_n'],hovertemplate='%{y}: %{x:.1f}%<br>Records: %{customdata}<extra></extra>'))
    fig.update_xaxes(range=[0,105],ticksuffix='%',showgrid=True,gridcolor='#e9eff4')
    return _layout(fig,max(275,45*len(s)+100))


def grade_distribution_chart(grade_counts):
    """Show the current-grade distribution without mixing grading systems silently."""
    if grade_counts.empty:return go.Figure()
    from overview_tables import grade_sort_key
    s=grade_counts.copy()
    s['order']=s['Grade'].map(grade_sort_key)
    s=s.sort_values('order',ascending=False)
    fig=go.Figure(go.Bar(x=s['Grade'].astype(str),y=s['Count'],marker_color='#348b9b',text=s['Count'],textposition='outside',customdata=s['Percent'],hovertemplate='Grade %{x}: %{y} results<br>% of valid results: %{customdata:.1f}%<extra></extra>'))
    fig.update_yaxes(showgrid=True,gridcolor='#e9eff4',rangemode='tozero')
    return _layout(fig,max(265,275))
