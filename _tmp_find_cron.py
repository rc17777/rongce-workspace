#!/usr/bin/env python3
import json
with open(r'C:\Users\scrccpa\.openclaw\openclaw.json', 'r', encoding='utf-8') as f:
    c = json.load(f)

def find_cron(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ('cron', 'crons', 'schedule', 'schedules'):
                print(f'Found at {path}.{k}')
            find_cron(v, f'{path}.{k}')
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, dict):
                has_cron = 'schedule' in v or 'cron' in v
                if has_cron:
                    name = v.get('name', '?')
                    sched = v.get('schedule', '?')
                    print(f'Found at {path}[{i}]: {name} | {sched}')
                find_cron(v, f'{path}[{i}]')

find_cron(c)