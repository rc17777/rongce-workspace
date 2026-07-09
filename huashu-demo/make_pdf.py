# -*- coding: utf-8 -*-
"""Embed A4-ratio screenshots into A4 PDF — full bleed, no margins."""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fpdf import FPDF

output_dir = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\output'
pngs = sorted(
    [f for f in os.listdir(output_dir) if f.startswith('page-') and f.endswith('.png')],
    key=lambda x: int(x.replace('page-','').replace('.png',''))
)

if not pngs:
    print('ERROR: No PNGs found. Run export-pngs.js first.')
    sys.exit(1)

print(f'Found {len(pngs)} screenshots')

A4_W, A4_H = 297, 210  # mm, landscape

# Viewport is 1920x1358 → exact A4 ratio → full-bleed, no offsets
print(f'Full-bleed A4: {A4_W} x {A4_H} mm')

pdf = FPDF(orientation='L', unit='mm', format='A4')
pdf.set_auto_page_break(False)

for png in pngs:
    png_path = os.path.join(output_dir, png)
    pdf.add_page()
    pdf.image(png_path, x=0, y=0, w=A4_W, h=A4_H)

out = os.path.join(output_dir, '融策-政府审计宣传册-final.pdf')
pdf.output(out)
size_mb = os.path.getsize(out) / 1024 / 1024
print(f'\nDone: {out} ({size_mb:.1f} MB)')
