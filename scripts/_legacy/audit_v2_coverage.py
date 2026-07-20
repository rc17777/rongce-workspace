#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
CATALOG = VAULT / '审计资料清单.json'
V2 = VAULT / '审计案例库-OCR' / '融策标准作业体系 v2.0'
TRAINING = V2 / '01-训练清单' / '场景-审计逻辑-可复用方法训练清单 v2.0.md'

GENERATED_MARKERS = ['案例卡片', '模板', '标准作业包', '实战试点包', '训练清单', '方法词典', '资料总览', '老板版', '融策标准作业体系']
CORE_SCENES = {
    '工程审计', '政策落实审计', '国企审计', '信息系统审计', '农业农村审计',
    '预算执行审计', '绩效审计', '经济责任审计', '社保民生审计', '资源环境审计',
    '专项资金审计', '金融审计', '内部审计', '教科文卫审计', '其他审计'
}

def is_generated(x):
    s = (x.get('path','') + ' ' + x.get('title','') + ' ' + x.get('filename',''))
    return any(m in s for m in GENERATED_MARKERS) or x.get('scene') not in CORE_SCENES

def main():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    real = [x for x in data if not is_generated(x)]
    generated = [x for x in data if is_generated(x)]
    training = TRAINING.read_text(encoding='utf-8', errors='replace') if TRAINING.exists() else ''

    covered = []
    missed = []
    for x in real:
        path = x['path']
        title = x.get('title') or x.get('filename')
        if path in training or title in training:
            covered.append(x)
        else:
            missed.append(x)

    print('TOTAL_CATALOG', len(data))
    print('REAL_CASES', len(real))
    print('GENERATED_OR_NONCASE', len(generated))
    print('TRAINING_COVERED', len(covered))
    print('TRAINING_MISSED', len(missed))
    print('V2_FILES', len(list(V2.rglob('*.md'))) if V2.exists() else 0)
    print('\nREAL_BY_SCENE')
    for scene, count in Counter(x['scene'] for x in real).most_common():
        print(scene, count)
    print('\nMISSED_SAMPLE')
    for x in missed[:30]:
        print(x['scene'], '|', x.get('title'), '|', x['path'])

if __name__ == '__main__':
    main()
