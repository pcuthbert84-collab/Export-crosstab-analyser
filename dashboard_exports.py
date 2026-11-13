"""Safe in-memory Excel and aggregate PDF exports for the development prototype."""
from __future__ import annotations
import io
import pandas as pd
from html import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from dashboard_analytics import percentage_label

def excel_bytes(df):
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as writer:
        df.to_excel(writer,sheet_name='Results',index=False)
        sheet=writer.sheets['Results']
        sheet.freeze_panes='B2';sheet.auto_filter.ref=sheet.dimensions
        from openpyxl.styles import Font,PatternFill,Alignment
        for cell in sheet[1]:
            cell.fill=PatternFill('solid',fgColor='15364D')
            cell.font=Font(color='FFFFFF',bold=True)
            cell.alignment=Alignment(wrap_text=True,vertical='center')
        sheet.row_dimensions[1].height=28
        for col in sheet.columns:
            header=str(col[0].value or '')
            width=max(len(header)+3,max((len(str(c.value or '')) for c in col[1:]),default=0)+2)
            sheet.column_dimensions[col[0].column_letter].width=min(45,max(12,width))
        fills={'Outstanding':'DBEAFE','Very Good':'DCFCE7','Good':'FEF9C3','Acceptable':'FFEDD5','Weak':'FEE2E2'}
        if 'KHDA grade' in df.columns:
            col_i=list(df.columns).index('KHDA grade')
            for i,grade in enumerate(df['KHDA grade'],start=2):
                if grade in fills:
                    for cell in sheet[i]:cell.fill=PatternFill('solid',fgColor=fills[grade])
    return out.getvalue()


def pdf_summary(summary,metadata):
    """An aggregate summary PDF — deliberately NOT the unimplemented 87-table Data Pack."""
    b=io.BytesIO()
    doc=SimpleDocTemplate(b,pagesize=landscape(A4),leftMargin=34,rightMargin=34,topMargin=38,bottomMargin=38)
    styles=getSampleStyleSheet()
    elements=[Paragraph('DBSJP | Assessment Intelligence Summary',styles['Title']),Spacer(1,8),Paragraph(escape(metadata),styles['Normal']),Spacer(1,14)]
    columns=[x for x in ('category','year','subject','students','at_or_above','above','expected_plus','better','met_cat4','met_cat4_75','va','attainment_judgement','progress_judgement') if x in summary.columns]
    labels={'category':'Subject','year':'Year','subject':'Subject','students':'Students','at_or_above':'Meeting+','above':'Exceeding','expected_plus':'Expected+','better':'Better+','met_cat4':'Met CAT4','met_cat4_75':'Challenge','va':'Mean VA','attainment_judgement':'Attainment','progress_judgement':'Progress'}
    if summary.empty:elements.append(Paragraph('No eligible aggregate results.',styles['Normal']))
    else:
        for start in range(0,len(summary),22):
            chunk=summary.iloc[start:start+22]
            rows=[[labels.get(c,c) for c in columns]]
            for _,row in chunk.iterrows():
                vals=[]
                for col in columns:
                    v=row[col]
                    if v is None or pd.isna(v):v=''
                    elif col in ('at_or_above','above','expected_plus','better','met_cat4','met_cat4_75'):v=percentage_label(v)
                    elif col=='va' and isinstance(v,(float,int)):v=f'{v:+.2f}'
                    vals.append(str(v)[:29])
                rows.append(vals)
            t=Table(rows,repeatRows=1,colWidths=[min(115,770/max(1,len(columns)))]*len(columns),hAlign='LEFT')
            styles_list=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#15364d')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTSIZE',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#dce5ec'))]
            judg_col=next((i for i,c in enumerate(columns) if c=='attainment_judgement'),None)
            palette={'Outstanding':'#dbeafe','Very Good':'#dcfce7','Good':'#fef9c3','Acceptable':'#ffedd5','Weak':'#fee2e2'}
            if judg_col is not None:
                for ri,(_,row) in enumerate(chunk.iterrows(),start=1):
                    color=palette.get(row['attainment_judgement'])
                    if color:styles_list.append(('BACKGROUND',(0,ri),(-1,ri),colors.HexColor(color)))
            t.setStyle(TableStyle(styles_list));elements.append(t)
            if start+22<len(summary):elements.append(PageBreak())
    doc.build(elements)
    return b.getvalue()


