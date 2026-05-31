#!/usr/bin/env python3
"""
Markdown → PDF converter using fpdf 1.7.2 (pure Python, no fonttools dependency).
Usage: python md_to_pdf_v1.py input.md output.pdf --title "TITLE" --author "AUTHOR"
"""

import sys
import os
import re
import argparse
from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def __init__(self, title, author):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(True, 20)
        self.report_title = title
        self.report_author = author
        self.set_margins(20, 15, 20)
        
        # Add Unicode font
        # Try to find Chinese TTF fonts
        font_paths = [
            r'C:\Windows\Fonts\msyh.ttf',           # Microsoft YaHei
            r'C:\Windows\Fonts\simsun.ttc',         # SimSun
            r'C:\Windows\Fonts\simhei.ttf',         # SimHei
            r'C:\Windows\Fonts\Deng.ttf',           # DengXian
            r'C:\Windows\Fonts\STSONG.TTF',         # STSong
            r'C:\Windows\Fonts\msyhl.ttc',          # Microsoft YaHei Light
            r'C:\Windows\Fonts\mingliu.ttc',        # MingLiU
            r'C:\Windows\Fonts\kaiu.ttf',           # KaiTi
        ]
        # Filter out .ttc files and non-existent files
        font_paths = [p for p in font_paths if os.path.exists(p) and not p.lower().endswith('.ttc')]
        
        cn_font = None
        cn_font_bold = None
        for p in font_paths:
            if os.path.exists(p):
                if 'bold' in p.lower() or 'bd' in p.lower() or p.endswith('b.ttf'):
                    cn_font_bold = p
                elif cn_font is None:
                    cn_font = p
        
        if cn_font_bold is None:
            cn_font_bold = cn_font
        
        if cn_font:
            self.add_font('CJK', '', cn_font, uni=True)
            if cn_font_bold:
                self.add_font('CJK', 'B', cn_font_bold, uni=True)
            else:
                self.add_font('CJK', 'B', cn_font, uni=True)
            print(f"Using CJK font: {os.path.basename(cn_font)}")
        else:
            print("WARNING: No Chinese font found, using built-in fonts")
        
    def title_page(self):
        self.add_page()
        self.ln(30)
        self.set_font('CJK', 'B', 24)
        self.multi_cell(0, 12, self.report_title, align='C')
        self.ln(8)
        self.set_font('CJK', '', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, self.report_author, align='C')
        self.ln()
        self.cell(0, 8, datetime.now().strftime('%Y%%m月%d日'), align='C')
        self.ln()

    def section_heading(self, level, text):
        sizes = {1: 18, 2: 15, 3: 13, 4: 11.5}
        colors = {1: (26, 82, 118), 2: (26, 82, 118), 3: (44, 62, 80), 4: (44, 62, 80)}
        size = sizes.get(level, 12)
        color = colors.get(level, (44, 62, 80))
        self.ln(4)
        self.set_font('CJK', 'B', size)
        self.set_text_color(*color)
        self.multi_cell(0, 8, text.strip(), align='L')
        self.set_text_color(44, 62, 80)
        self.set_font('CJK', '', 10)
        self.ln(2)

    def paragraph(self, text):
        self.set_font('CJK', '', 10.5)
        self.set_text_color(44, 62, 80)
        self.multi_cell(0, 5.5, text.strip(), align='L')
        self.ln(1)

    def bullet(self, text):
        self.set_font('CJK', '', 10)
        indent = 10
        x = self.get_x()
        self.set_x(x + indent)
        # Check for bold markers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        self.multi_cell(170, 5, text.strip(), align='L')
        self.set_x(x)

    def table(self, headers, rows):
        self.ln(2)
        n = len(headers)
        w = 170 / n
        
        # Header
        self.set_fill_color(26, 82, 118)
        self.set_text_color(255, 255, 255)
        self.set_font('CJK', 'B', 8.5)
        for h in headers:
            self.cell(w, 7, h, border=1, fill=True, align='C')
        self.ln()
        
        # Rows
        fill = False
        self.set_text_color(44, 62, 80)
        self.set_font('CJK', '', 8)
        for row in rows:
            if fill:
                self.set_fill_color(236, 240, 241)
            else:
                self.set_fill_color(255, 255, 255)
            for cell in row:
                self.cell(w, 6, cell, border=1, fill=True, align='L')
            self.ln()
            fill = not fill
        self.ln(3)
        self.set_text_color(44, 62, 80)


def md_to_pdf(md_path, pdf_path, title, author):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    pdf = PDFReport(title, author)
    pdf.add_page()
    pdf.title_page()
    pdf.add_page()
    
    i = 0
    in_table = False
    table_rows = []
    table_headers = []
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Headings
        if line.startswith('# '):
            pdf.section_heading(1, re.sub(r'^#+\s+', '', line))
        elif line.startswith('## '):
            pdf.section_heading(2, re.sub(r'^##+\s+', '', line))
        elif line.startswith('### '):
            pdf.section_heading(3, re.sub(r'^###+\s+', '', line))
        elif line.startswith('#### '):
            pdf.section_heading(4, re.sub(r'^####+\s+', '', line))
        
        # Tables
        elif line.startswith('|') and line.endswith('|') and not re.match(r'^\|[\s\-:]+\|$', line):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if not table_headers and not in_table:
                table_headers = cells
                in_table = True
            elif in_table:
                table_rows.append(cells)
        elif in_table and not (line.startswith('|') and line.endswith('|')):
            if table_headers and table_rows:
                # Check if we can fit the table on the current page
                pdf.table(table_headers, table_rows)
            table_headers = []
            table_rows = []
            in_table = False
        
        # Separator line
        elif re.match(r'^\|[\s\-:]+\|$', line):
            pass
        
        # HR
        elif line.strip() == '---' and i > 0 and i < len(lines) - 1:
            pass
        
        # Bullet
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            text = re.sub(r'^[\*\-\+]\s+', '', line.strip())
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            pdf.bullet(text)
        
        # Numbered
        elif re.match(r'^\d+[\.\、]', line.strip()):
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', line.strip())
            pdf.paragraph(text)
        
        # Blockquote
        elif line.strip().startswith('> '):
            text = re.sub(r'^>\s+', '', line.strip())
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            pdf.set_text_color(100, 100, 100)
            pdf.set_font('CJK', '', 9.5)
            pdf.multi_cell(0, 5, text, align='L')
            pdf.set_text_color(44, 62, 80)
            pdf.set_font('CJK', '', 10)
        
        # Empty line
        elif line.strip() == '':
            pass
        
        # Regular paragraph
        elif line.strip():
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', line.strip())
            text = re.sub(r'\*(.*?)\*', r'\1', text)
            pdf.paragraph(text)
        
        i += 1
    
    # Flush remaining table
    if table_headers and table_rows:
        pdf.table(table_headers, table_rows)
    
    pdf.output(pdf_path)
    print(f"PDF saved: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('output', help='Output PDF file')
    parser.add_argument('--title', default='Report', help='Report title')
    parser.add_argument('--author', default='AI Assistant', help='Author name')
    args = parser.parse_args()
    
    md_to_pdf(args.input, args.output, args.title, args.author)
