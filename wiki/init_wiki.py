"""
融策审计中台 - Wiki 协作知识库初始化 & 自动索引
================================================
团队Wiki结构 + 项目模板 + 自动RAG索引

用法:
    python wiki/init_wiki.py          # 初始化Wiki目录结构
    python wiki/init_wiki.py --project "XX县教育局预算执行审计"  # 创建项目工作区
    python wiki/index_wiki.py         # 自动索引Wiki内容到RAG
"""

import os, sys, json, datetime, shutil, argparse

sys.stdout.reconfigure(encoding='utf-8')
WORKSPACE = r'C:\Users\scrccpa\.openclaw\workspace'
WIKI_DIR = os.path.join(WORKSPACE, 'wiki')
os.makedirs(WIKI_DIR, exist_ok=True)

# ====== Wiki 目录结构 ======
WIKI_STRUCTURE = {
    '01-法规库': {
        'desc': '审计相关法律法规、部门规章、政策文件',
        'sources': '自动从 knowledge/laws/ 同步',
        'subdirs': ['法律', '行政法规', '部门规章', '地方性法规', '政策文件'],
    },
    '02-方法论': {
        'desc': '融策自研审计方法论、SOP、操作指引',
        'subdirs': ['招投标审计', '绩效评价', '经济责任审计', '专项资金审计', '预算执行审计', 
                   '国企审计', '工程审计', '补贴审计', '监督检查'],
    },
    '03-案例库': {
        'desc': '典型审计发现、问题清单、整改案例',
        'subdirs': ['围标串标', '资金违规', '程序违规', '履约异常', '关联交易', '绩效不达标'],
    },
    '04-报告模板': {
        'desc': '各类审计报告标准模板',
        'subdirs': ['绩效评价', '经济责任', '预算执行', '专项资金', '工程决算', '监督检查'],
    },
    '05-工具与脚本': {
        'desc': '审计工具使用手册、脚本说明',
        'subdirs': ['异常检测', '数据分析', '报告复核', 'RAG查询'],
    },
    '06-项目工作区': {
        'desc': '在审项目文档、底稿索引、进度看板',
    },
    '07-培训与规范': {
        'desc': '人员培训材料、执业标准、质量管理制度',
        'subdirs': ['入职培训', '专业技能', '职业道德', '质量管理'],
    },
}

# ====== 项目模板 ======
PROJECT_TEMPLATE = """---
project_name: "{project_name}"
project_type: "{project_type}"  # 经责/预算执行/专项资金/绩效评价/工程/国企/补贴/监督检查/招投标/其他
client: "{client}"
audit_period: "{audit_period}"
status: "进行中"  # 进行中/报告撰写/复核中/已完成/归档
lead: "{lead}"
team: []
start_date: "{start_date}"
tags: [{tags}]
---

# {project_name}

## 一、项目概况

- **被审计单位**：{client}
- **审计类型**：{project_type}
- **审计期间**：{audit_period}
- **项目负责人**：{lead}
- **进场日期**：{start_date}
- **计划完成日期**：

## 二、审计目标与范围

（填写审计委托书/实施方案中的审计目标和范围）

## 三、资料清单与获取状态

| 序号 | 资料名称 | 状态 | 获取日期 | 备注 |
|:--|:--|:--|:--|:--|
| 1 |  | □已获取 □待提供 □不适用 |  |  |
| 2 |  | □已获取 □待提供 □不适用 |  |  |

## 四、审计发现台账

| 编号 | 发现描述 | 坐标系 | 严重程度 | E规则 | 状态 |
|:--|:--|:--|:--|:--|:--|
| F-001 |  | 时空/物理/社会关系/行为/时间序列 | P0/P1/P2 |  | 待核实/已确认/已写入报告 |

## 五、进度看板

- [ ] 数据采集完成
- [ ] 标前审计(十必审)
- [ ] 疑点检测(E01-E35)
- [ ] 取证核查
- [ ] 报告初稿
- [ ] 三级复核(十必查)
- [ ] 征求意见
- [ ] 正式报告

## 六、方法引用

本项目的审计方法引用融策方法论：

- 招投标审计 SOP v1.1
- 三级复核清单 v1.1
- 5坐标系 × 27层检测体系
- RAG知识库 (实时检索)

## 七、相关链接

- 法规依据：[[01-法规库]]
- 参考案例：[[03-案例库]]
- 报告模板：[[04-报告模板/{project_type}]]
- 工具脚本：[[05-工具与脚本]]
"""

PROJECT_INDEX_TEMPLATE = """---
title: "项目索引"
updated: "{date}"
---

# 项目索引

## 进行中

| 项目名称 | 类型 | 客户 | 负责人 | 进场日期 |
|:--|:--|:--|:--|:--|

## 已完成

| 项目名称 | 类型 | 客户 | 完成日期 | 归档状态 |
|:--|:--|:--|:--|:--|

*最后更新: {date}*
"""

def init_wiki():
    """初始化Wiki目录结构"""
    for dirname, config in WIKI_STRUCTURE.items():
        dirpath = os.path.join(WIKI_DIR, dirname)
        os.makedirs(dirpath, exist_ok=True)
        
        # Create README
        readme = f"""---
title: "{dirname}"
desc: "{config.get('desc', '')}"
created: "{datetime.date.today()}"
---

# {dirname}

{config.get('desc', '')}

"""
        with open(os.path.join(dirpath, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme)
        
        # Create subdirectories
        for subdir in config.get('subdirs', []):
            subpath = os.path.join(dirpath, subdir)
            os.makedirs(subpath, exist_ok=True)
            
            # Create .gitkeep or README
            with open(os.path.join(subpath, '.gitkeep'), 'w') as f:
                f.write('')
        
        print(f'  ✅ {dirname} ({len(config.get("subdirs", []))} 子目录)')
    
    # Create project index
    with open(os.path.join(WIKI_DIR, '06-项目工作区', '项目索引.md'), 'w', encoding='utf-8') as f:
        f.write(PROJECT_INDEX_TEMPLATE.format(date=datetime.date.today()))
    
    # Create main README
    main_readme = f"""---
title: "融策审计Wiki"
updated: "{datetime.date.today()}"
---

# 融策审计Wiki

团队共享审计知识库。结构：

| 目录 | 内容 | 访问控制 |
|:--|:--|:--|
| 01-法规库 | 法律法规、政策文件 → 自动从RAG同步 | 全员只读 |
| 02-方法论 | 审计SOP、操作指引、技术标准 | 合伙人可编辑 |
| 03-案例库 | 典型审计发现、整改案例 | 项目负责人+ |
| 04-报告模板 | 各类型报告标准模板 | 全员只读 |
| 05-工具与脚本 | 审计工具使用手册 | 技术负责人可编辑 |
| 06-项目工作区 | 在审项目文档和进度 → 独立权限 | 项目组+ |
| 07-培训与规范 | 培训材料、执业标准 | 质控可编辑 |

## 使用规则

1. **项目文档**在 06-项目工作区 中创建独立子目录
2. **方法论更新**由项目负责人沉淀后提交审核
3. **案例入库**须隐去敏感信息后归档
4. **法规更新**由 RAG 系统自动同步

## 与RAG联动

Wiki内容变更后自动触发RAG重索引：
```bash
python wiki/index_wiki.py
```
"""
    with open(os.path.join(WIKI_DIR, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(main_readme)
    
    print(f'\nWiki 初始化完成: {WIKI_DIR}')
    print(f'  7 个一级目录')
    print(f'  可访问: file:///{WIKI_DIR.replace(chr(92), "/")}')


def create_project(project_name, project_type='其他', client='', audit_period='', lead=''):
    """创建项目工作区"""
    # Sanitize project name for directory
    safe_name = project_name.replace('/', '-').replace('\\', '-').replace(':', '-')
    proj_dir = os.path.join(WIKI_DIR, '06-项目工作区', safe_name)
    os.makedirs(proj_dir, exist_ok=True)
    
    # Create subdirs
    for sub in ['01-原始资料', '02-审计底稿', '03-取证单', '04-报告', '05-沟通记录']:
        os.makedirs(os.path.join(proj_dir, sub), exist_ok=True)
        with open(os.path.join(proj_dir, sub, '.gitkeep'), 'w') as f:
            f.write('')
    
    # Project type mapping
    type_map = {
        '经责': '经济责任审计', '预算': '预算执行审计', '专项': '专项资金审计',
        '绩效': '预算绩效管理', '工程': '工程竣工决算', '国企': '国企审计',
        '补贴': '政府补贴审计', '检查': '监督检查', '招投标': '招投标审计',
    }
    ptype = type_map.get(project_type, project_type)
    
    # Create project README
    today = datetime.date.today().strftime('%Y-%m-%d')
    readme = PROJECT_TEMPLATE.format(
        project_name=project_name,
        project_type=ptype,
        client=client or '待填写',
        audit_period=audit_period or '待填写',
        lead=lead or '待指定',
        start_date=today,
        tags=project_type,
    )
    
    with open(os.path.join(proj_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme)
    
    # Update project index
    idx_path = os.path.join(WIKI_DIR, '06-项目工作区', '项目索引.md')
    if os.path.exists(idx_path):
        with open(idx_path, 'r', encoding='utf-8') as f:
            idx_content = f.read()
        
        new_line = f'| {project_name} | {ptype} | {client} | {lead} | {today} |'
        # Insert after "进行中" table header
        idx_content = idx_content.replace(
            '| 项目名称 | 类型 | 客户 | 负责人 | 进场日期 |\n',
            f'| 项目名称 | 类型 | 客户 | 负责人 | 进场日期 |\n{new_line}\n'
        )
        
        with open(idx_path, 'w', encoding='utf-8') as f:
            f.write(idx_content)
    
    print(f'\n项目工作区已创建: {proj_dir}')
    print(f'  类型: {ptype}')
    print(f'  模板: 5个子目录 + README')

def index_wiki():
    """扫描Wiki内容，输出索引到RAG可用的格式"""
    import glob
    
    files = []
    for root, dirs, fnames in os.walk(WIKI_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in fnames:
            if fname.endswith('.md') and fname != 'README.md':
                files.append(os.path.join(root, fname))
    
    index = []
    for fpath in files:
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            rel = os.path.relpath(fpath, WIKI_DIR)
            # Extract YAML frontmatter
            import re
            fm = {}
            m = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if m:
                for line in m.group(1).split('\n'):
                    kv = line.split(':', 1)
                    if len(kv) == 2:
                        fm[kv[0].strip()] = kv[1].strip().strip('"')
            index.append({
                'path': rel,
                'title': fm.get('title', fname.replace('.md', '')),
                'type': fm.get('project_type', rel.split('/')[0]),
                'tags': fm.get('tags', '').split(','),
                'size': len(content),
            })
        except:
            pass
    
    # Save index
    idx_path = os.path.join(WIKI_DIR, '.wiki_index.json')
    with open(idx_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f'Wiki索引: {len(index)} 文件')
    print(f'索引文件: {idx_path}')
    return index

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='融策Wiki管理工具')
    parser.add_argument('action', nargs='?', default='init', choices=['init', 'project', 'index'], help='操作')
    parser.add_argument('--project', type=str, help='项目名称')
    parser.add_argument('--type', type=str, default='其他', help='项目类型')
    parser.add_argument('--client', type=str, default='', help='客户名称')
    parser.add_argument('--period', type=str, default='', help='审计期间')
    parser.add_argument('--lead', type=str, default='', help='项目负责人')
    args = parser.parse_args()
    
    if args.action == 'init':
        init_wiki()
    elif args.action == 'project':
        if not args.project:
            print('Usage: python wiki/init_wiki.py project --project "项目名"')
            sys.exit(1)
        create_project(args.project, args.type, args.client, args.period, args.lead)
    elif args.action == 'index':
        index_wiki()
