#!/usr/bin/env python3
"""
Fallback Markdown → PDF converter using fpdf2 (pure Python, no DLL issues).
Usage: python md_to_pdf_fallback.py input.md output.pdf [--title "TITLE"] [--author "AUTHOR"]
"""

import sys
import os
import re
import argparse
from fpdf import FPDF
import markdown
from html.parser import HTMLParser
from html import unescape

# Simple HTML to PDF-friendly text converter
class HTMLToText:
    def __init__(self):
        self.text_parts = []
        self.in_bold = False
        self.in_em = False
        self.in_code = False
        self.in_li = False
        self.in_a = False
        self.link_text = ""
        self.link_href = ""
        self.skip_tag = False
        self.skip_depth = 0
        self.list_depth = 0
        self.in_table = False
        self.table_cells = []
        self.current_row = []
        self.current_cell = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ('script', 'style'):
            self.skip_tag = True
            self.skip_depth = 1
            return
        if self.skip_tag:
            self.skip_depth += 1
            return

        if tag == 'h1':
            self.text_parts.append(('\n\n', 'h1'))
        elif tag == 'h2':
            self.text_parts.append(('\n\n', 'h2'))
        elif tag == 'h3':
            self.text_parts.append(('\n\n', 'h3'))
        elif tag == 'h4':
            self.text_parts.append(('\n\n', 'h4'))
        elif tag == 'p':
            pass
        elif tag == 'br':
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'strong' or tag == 'b':
            self.in_bold = True
        elif tag == 'em' or tag == 'i':
            self.in_em = True
        elif tag == 'code':
            self.in_code = True
        elif tag == 'ul':
            self.list_depth += 1
        elif tag == 'ol':
            self.list_depth += 1
        elif tag == 'li':
            prefix = '  ' * (self.list_depth - 1) + '- ' if self.list_depth > 0 else '  '
            self.text_parts.append((prefix, 'li'))
        elif tag == 'a':
            self.in_a = True
            self.link_text = ""
            self.link_href = dict(attrs).get('href', '')
        elif tag == 'table':
            self.in_table = True
            self.table_cells = []
        elif tag == 'tr':
            self.current_row = []
        elif tag in ('th', 'td'):
            self.current_cell = ""
        elif tag == 'hr':
            self.text_parts.append(('\n---\n', 'normal'))
        elif tag in ('blockquote', 'pre'):
            self.text_parts.append(('\n', 'blockquote'))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.skip_tag:
            self.skip_depth -= 1
            if self.skip_depth == 0:
                self.skip_tag = False
            return
        if tag == 'h1':
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'h2':
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'h3':
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'h4':
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'p':
            self.text_parts.append(('\n\n', 'normal'))
        elif tag == 'strong' or tag == 'b':
            self.in_bold = False
        elif tag == 'em' or tag == 'i':
            self.in_em = False
        elif tag == 'code':
            self.in_code = False
        elif tag == 'ul' or tag == 'ol':
            self.list_depth -= 1
            if self.list_depth <= 0:
                self.text_parts.append(('\n', 'normal'))
        elif tag == 'li':
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'a':
            self.in_a = False
            if self.link_href and self.link_href.startswith('http'):
                self.text_parts.append((f' ({self.link_href}) ', 'link'))
            self.link_href = ''
            self.link_text = ''
        elif tag == 'table':
            self.in_table = False
            self.text_parts.append(('\n', 'normal'))
        elif tag == 'tr':
            if self.current_row:
                self.table_cells.append(self.current_row)
            self.current_row = []
        elif tag in ('th', 'td'):
            if self.in_table:
                self.current_row.append(self.current_cell.strip())
                self.current_cell = ""
        elif tag in ('blockquote', 'pre'):
            self.text_parts.append(('\n', 'normal'))

    def handle_data(self, data):
        if self.skip_tag:
            return
        if self.in_a:
            self.link_text += data
        if self.in_table and (hasattr(self, 'current_cell')):
            self.current_cell += data

        style = 'normal'
        if self.in_bold and self.in_em:
            style = 'bold_italic'
        elif self.in_bold:
            style = 'bold'
        elif self.in_em:
            style = 'italic'
        elif self.in_code:
            style = 'code'

        self.text_parts.append((data, style))

    def get_structured_text(self):
        """Return list of (text, style) tuples."""
        return self.text_parts


class PDFReport(FPDF):
    def __init__(self, title="Report", author="AI Assistant"):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.title_text = title
        self.author_text = author
        
        # Try to add Chinese font
        self.add_font_path()
        
    def add_font_path(self):
        """Try to find a Chinese font on Windows."""
        import glob
        # Common Chinese font locations on Windows
        font_dirs = [
            'C:\\Windows\\Fonts',
            'C:\\Windows\\WinSxS\\*\\fonts',
        ]
        chinese_fonts = [
            'msyh.ttf', 'msyhbd.ttf',  # Microsoft YaHei
            'simsun.ttc', 'simsun.ttf',  # SimSun
            'simhei.ttf',  # SimHei
            'STSONG.TTF', 'STKAITI.TTF',
            'Deng.ttf',  # DengXian
        ]
        
        for font_name in chinese_fonts:
            for font_dir in font_dirs:
                matches = glob.glob(os.path.join(font_dir, font_name))
                if matches:
                    try:
                        self.add_font('CJK', '', matches[0], uni=True)
                        # Try bold variant
                        bold_name = font_name.replace('.ttf', 'bd.ttf').replace('.ttc', 'bd.ttc')
                        bold_matches = glob.glob(os.path.join(font_dir, bold_name))
                        if bold_matches:
                            self.add_font('CJK', 'B', bold_matches[0], uni=True)
                        else:
                            self.add_font('CJK', 'B', matches[0], uni=True)
                        print(f"Using font: {matches[0]}")
                        return
                    except Exception as e:
                        print(f"Font {matches[0]} failed: {e}")
                        continue
        
        # Last resort - try any ttf in Windows\Fonts
        try:
            ttf_files = glob.glob('C:\\Windows\\Fonts\\*.ttf')
            for ttf in ttf_files[:10]:
                try:
                    self.add_font('CJK', '', ttf, uni=True)
                    print(f"Using fallback font: {ttf}")
                    return
                except:
                    continue
        except:
            pass
        
        print("WARNING: No CJK font found, PDF may not render Chinese characters correctly.")
        self.add_font('CJK', '', '', uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font('CJK', '', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, self.title_text, align='L')
            self.cell(0, 5, f'第 {self.page_no()} 页', align='R', new_x='LMARGIN', new_y='NEXT')
            self.line(10, 12, 200, 12)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('CJK', '', 8)
        self.set_text_color(128, 128, 128)
        if self.page_no() > 1:
            self.cell(0, 10, f'— {self.page_no()} —', align='C')

    def add_title_page(self):
        self.add_page()
        self.ln(40)
        self.set_font('CJK', 'B', 22)
        self.multi_cell(0, 12, self.title_text, align='C')
        self.ln(10)
        self.set_font('CJK', '', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, f'作者：{self.author_text}', align='C', new_x='LMARGIN', new_y='NEXT')
        from datetime import datetime
        self.cell(0, 8, f'生成日期：{datetime.now().strftime("%Y年%m月%d日")}', align='C', new_x='LMARGIN', new_y='NEXT')

    def add_content_page(self, parts):
        """Add a content page with styled text parts."""
        self.add_page()
        self.set_font('CJK', '', 10.5)
        self.set_text_color(44, 62, 80)
        
        line_width = 190  # A4 width minus margins
        
        current_text = ""
        current_style = "normal"
        
        def flush_text():
            nonlocal current_text
            if not current_text.strip():
                current_text = ""
                return
            
            text = current_text.rstrip()
            
            # Handle headings
            if current_style in ('h1', 'h2', 'h3', 'h4'):
                self.ln(2)
                font_size = {'h1': 16, 'h2': 14, 'h3': 12, 'h4': 11}.get(current_style, 11)
                self.set_font('CJK', 'B', font_size)
                self.set_text_color(26, 82, 118)
                # Remove markdown heading markers
                text = re.sub(r'^#+\s*', '', text)
                text = re.sub(r'\*\*', '', text)
                self.multi_cell(line_width, 7, text.strip(), align='L')
                self.set_text_color(44, 62, 80)
                self.ln(2)
            elif current_style == 'bold':
                self.set_font('CJK', 'B', 10.5)
                self.write(5.5, text)
                self.set_font('CJK', '', 10.5)
            elif current_style == 'italic':
                self.set_font('CJK', '', 10.5)
                self.write(5.5, text)
            elif current_style == 'code':
                self.set_font('Courier', '', 9)
                self.set_text_color(44, 62, 80)
                bg_x = self.get_x()
                bg_y = self.get_y()
                self.write(5, text)
                self.set_font('CJK', '', 10.5)
            elif current_style == 'link':
                self.set_font('CJK', '', 9)
                self.set_text_color(41, 128, 185)
                self.write(5, text)
                self.set_text_color(44, 62, 80)
                self.set_font('CJK', '', 10.5)
            elif current_style == 'li':
                self.set_font('CJK', '', 10.5)
                text = text.replace('\n', '')
                self.multi_cell(line_width, 5.5, text, align='L')
            elif current_style == 'blockquote':
                self.set_font('CJK', '', 9.5)
                self.set_text_color(100, 100, 100)
                # Indent
                x = self.get_x()
                self.set_x(x + 5)
                self.multi_cell(line_width - 5, 5, text.strip(), align='L')
                self.set_x(x)
                self.set_text_color(44, 62, 80)
            else:
                self.set_font('CJK', '', 10.5)
                self.write(5.5, text)
            
            self.set_font('CJK', '', 10.5)
            current_text = ""

        for text, style in parts:
            if text == '\n\n' and current_style == 'normal':
                current_text += text
                flush_text()
                self.ln(3)
            elif style != current_style and current_text:
                flush_text()
                current_style = style
                current_text = text
            else:
                current_style = style
                current_text += text
        
        if current_text:
            flush_text()

    def add_table(self, headers, rows):
        """Add a formatted table."""
        self.ln(3)
        
        # Calculate column widths
        col_width = 190 / len(headers)
        
        # Header row
        self.set_font('CJK', 'B', 9)
        self.set_fill_color(26, 82, 118)
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_width, 7, header.strip(), border=1, fill=True, align='C')
        self.ln()
        
        # Data rows
        self.set_font('CJK', '', 8.5)
        self.set_text_color(44, 62, 80)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(236, 240, 241)
            else:
                self.set_fill_color(255, 255, 255)
            
            max_h = 7
            for i, cell in enumerate(row):
                self.cell(col_width, max_h, cell.strip(), border=1, fill=True, align='L')
            self.ln()
            fill = not fill
        
        self.ln(3)


def md_to_pdf(md_path, pdf_path, title="Report", author="AI Assistant"):
    """Convert Markdown file to PDF."""
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Remove HTML comments
    md_text = re.sub(r'<!--.*?-->', '', md_text, flags=re.DOTALL)
    
    # Handle tables manually - convert to HTML tables
    # fpdf2 doesn't handle markdown tables well through HTML conversion
    # We'll keep the markdown table syntax and handle it separately
    
    # Convert markdown to HTML
    md_html = markdown.markdown(md_text, extensions=['extra', 'tables', 'fenced_code'])
    
    # Parse HTML
    parser = HTMLToText()
    html_parser = HTMLParser()
    html_parser.handle_starttag = parser.handle_starttag
    html_parser.handle_endtag = parser.handle_endtag
    html_parser.handle_data = parser.handle_data
    html_parser.feed(md_html)
    html_parser.close()
    
    parts = parser.get_structured_text()
    
    # Create PDF
    pdf = PDFReport(title, author)
    pdf.add_title_page()
    
    # Split into content parts for multiple pages if needed
    # For simplicity, add all text content in pages
    # First identify table positions (they're mixed with text in the HTML output)
    
    pdf.add_content_page(parts)
    
    # Try to handle tables from the markdown directly
    # Parse tables from original markdown
    table_pattern = re.compile(r'^\|(.+)\|$', re.MULTILINE)
    tables = []
    lines = md_text.split('\n')
    in_table = False
    table_lines = []
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|'):
            in_table = True
            table_lines.append(line)
        else:
            if in_table and table_lines:
                tables.append(table_lines)
                table_lines = []
            in_table = False
    
    if table_lines:
        tables.append(table_lines)
    
    print(f"Found {len(tables)} tables in markdown")
    
    # Add tables after text content
    for table_lines in tables:
        if len(table_lines) >= 2:
            # Parse header from first line
            header_cells = [c.strip() for c in table_lines[0].split('|') if c.strip()]
            # Parse data from remaining lines (skip separator line)
            rows = []
            for line in table_lines[2:]:
                if line.strip().startswith('|'):
                    cells = [c.strip() for c in line.split('|') if c.strip()]
                    if cells:
                        rows.append(cells)
            
            if header_cells and rows:
                pdf.add_page()
                pdf.set_font('CJK', 'B', 10)
                pdf.cell(0, 8, '附表', align='C', new_x='LMARGIN', new_y='NEXT')
                pdf.add_table(header_cells, rows)
    
    pdf.output(pdf_path)
    print(f"PDF saved: {pdf_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert Markdown to PDF')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('output', help='Output PDF file')
    parser.add_argument('--title', default='Report', help='Report title')
    parser.add_argument('--author', default='AI Assistant', help='Author name')
    args = parser.parse_args()
    
    md_to_pdf(args.input, args.output, args.title, args.author)
