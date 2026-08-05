# -*- coding: utf-8 -*-
"""
API 适配器 — 配置驱动的分页拉取 → SDF
适用: 被审计单位对外开放的数据接口(极少见, 但保留入口)

配置JSON示例 (--config):
{
  "url": "https://api.example.com/v1/records",
  "method": "GET",
  "headers": {"Authorization": "Bearer xxx"},
  "params": {"dept": "财务处"},
  "pagination": {
    "type": "page",                 // page | offset | none
    "param": "page",                // 页码参数名
    "page_size_param": "page_size",
    "page_size": 100,
    "max_pages": 100,
    "stop_when_empty": true
  },
  "data_path": "data.items",        // 点路径定位记录列表
  "fields": [                       // 可选; 缺省自动发现首个记录字段
    {"name": "凭证号", "path": "voucher_no"},
    {"name": "金额", "path": "amount"}
  ],
  "rate_limit_seconds": 1
}

用法: python api_adapter.py --config cfg.json --out sdf.json [--label 数据集名]
"""
import sys, os, json, argparse, time, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from common import build_sdf, save_sdf, print_sdf_summary, now_iso

try:
    import requests
except ImportError:
    requests = None


def get_by_path(obj, path):
    """点路径取值: 'data.items' / 'records[0].name' 简化版(支持列表下标)"""
    for part in path.split('.'):
        if '[' in part and part.endswith(']'):
            key, idx = part.split('[', 1)
            idx = int(idx.rstrip(']'))
            if key:
                obj = obj.get(key, [])
            obj = obj[idx]
        elif isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.isdigit():
            obj = obj[int(part)]
        else:
            return None
        if obj is None:
            return None
    return obj


def discover_fields(record):
    """自动发现字段: 顶层key + 嵌套dict扁平化(用.连接)"""
    fields = []

    def walk(obj, prefix=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f'{prefix}.{k}' if prefix else k
                if isinstance(v, (dict, list)):
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        fields.append({'name': path, 'path': path})
                    else:
                        walk(v, path)
                else:
                    fields.append({'name': path, 'path': path})
    walk(record)
    return fields


def fetch_all(cfg):
    """分页拉取全部记录 → [dict...]"""
    if requests is None:
        raise RuntimeError('缺少 requests 库: pip install requests')
    url = cfg['url']
    method = cfg.get('method', 'GET').upper()
    headers = cfg.get('headers', {})
    params = dict(cfg.get('params', {}))
    pag = cfg.get('pagination', {}) or {}
    pag_type = pag.get('type', 'none')
    data_path = cfg.get('data_path', '')
    fields_cfg = cfg.get('fields', [])
    rate = cfg.get('rate_limit_seconds', 0)

    session = requests.Session()
    session.headers.update(headers)

    page = 1
    offset = 0
    all_records = []
    max_pages = int(pag.get('max_pages', 100))

    while True:
        req_params = dict(params)
        if pag_type == 'page':
            req_params[pag.get('param', 'page')] = page
            if pag.get('page_size_param'):
                req_params[pag['page_size_param']] = pag.get('page_size', 100)
        elif pag_type == 'offset':
            req_params[pag.get('offset_param', 'offset')] = offset
            if pag.get('page_size_param'):
                req_params[pag['page_size_param']] = pag.get('page_size', 100)

        # 重试3次
        resp = None
        for attempt in range(3):
            try:
                if method == 'GET':
                    resp = session.get(url, params=req_params, timeout=60)
                else:
                    resp = session.request(method, url, json=req_params, timeout=60)
                resp.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f'API请求失败({attempt+1}次): {e}')
                time.sleep(2 * (attempt + 1))

        data = resp.json()
        if data_path:
            records = get_by_path(data, data_path) or []
        elif isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = next((v for v in data.values() if isinstance(v, list)), [])
        else:
            records = []

        # 字段映射
        if not fields_cfg and records:
            fields_cfg = discover_fields(records[0])
        for r in records:
            rec = {}
            for f in fields_cfg:
                rec[f['name']] = get_by_path(r, f['path'])
            all_records.append(rec)

        print(f'  📡 第{page}页: 本页{len(records)}条, 累计{len(all_records)}条', flush=True)

        # 分页终止判断
        if pag_type == 'none':
            break
        stop_empty = pag.get('stop_when_empty', True)
        if stop_empty and not records:
            break
        if pag_type == 'page':
            page += 1
            if page > max_pages:
                print(f'  ⚠️ 达到最大页数 {max_pages}, 停止')
                break
        elif pag_type == 'offset':
            offset += len(records)
            if not records:
                break
            if offset >= pag.get('max_records', 10 ** 9):
                break
        if rate:
            time.sleep(rate)

    return all_records, fields_cfg


def convert(cfg_path, out_path=None, label='api'):
    """主入口: 返回 sdf"""
    with open(cfg_path, encoding='utf-8') as f:
        cfg = json.load(f)
    url = cfg['url']
    records, fields = fetch_all(cfg)
    if not records:
        raise ValueError(f'API未返回任何记录: {url}')

    columns = [{'name': f['name'], 'type': 'string'} for f in fields]
    sdf = build_sdf('api', url, records, columns=columns,
                    extra_source={'api_method': cfg.get('method', 'GET'),
                                  'fetch_time': now_iso()})
    if out_path:
        save_sdf(sdf, out_path)
    return sdf


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='API 适配器')
    p.add_argument('--config', required=True, help='API配置JSON路径')
    p.add_argument('--out', help='SDF输出路径')
    p.add_argument('--label', default='api', help='数据集标签')
    args = p.parse_args()

    sdf = convert(args.config, args.out, args.label)
    print_sdf_summary(sdf)
