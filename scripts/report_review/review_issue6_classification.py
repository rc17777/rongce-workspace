#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from pathlib import Path

IDX = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault\中国审计第6期-OCR归档索引.json')

def main():
    data = json.loads(IDX.read_text(encoding='utf-8'))
    print('=== LOW CONFIDENCE / REVIEW CANDIDATES ===')
    rows = []
    for x in data:
        scores = sorted(x['scene_scores'].items(), key=lambda kv: kv[1], reverse=True)
        top1, top2 = scores[0], scores[1]
        margin = top1[1] - top2[1]
        rows.append((margin, top1[1], top2[1], top1[0], top2[0], x['title'], x['archive_path']))
    for row in sorted(rows, key=lambda r: (r[0], -r[1], r[5])):
        margin, s1, s2, sc1, sc2, title, path = row
        if margin <= 8 or title in {'信息窗'}:
            print(f'{margin}\t{s1}\t{s2}\t{sc1}\t{sc2}\t{title}\t{path}')

    print('\n=== BY SCENE ===')
    by_scene = defaultdict(list)
    for x in data:
        by_scene[x['scene']].append(x)
    for scene in sorted(by_scene):
        print(f'## {scene} ({len(by_scene[scene])})')
        for item in by_scene[scene]:
            print(f"- {item['title']}\t{item['archive_path']}")

if __name__ == '__main__':
    main()
