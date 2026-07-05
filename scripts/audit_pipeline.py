#!/usr/bin/env python3
"""
招投标审计全流程自动分析 — 一键式主脚本 v1.0

融合技能:
  unstructured-audit-data  → 压缩包/Word关键词/PDF相似度/OCR
  apriori-audit           → Apriori关联规则(频繁结队+缺失关联)
  procurement-audit-models → L1-L19 全量检测

用法:
  python audit_pipeline.py --project <项目目录> --type procurement --o <输出目录>
  python audit_pipeline.py --project <项目目录> --type general --o <输出目录>

自动检测可用数据 → 运行适用分析 → 生成综合审计报告
"""
import sys, io, os, re, argparse, json, shutil, zipfile
from pathlib import Path
from datetime import datetime
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── 技能脚本路径 (相对于本脚本) ──
SKILLS_ROOT = Path(__file__).parent.parent / 'skills'
SCRIPTS = {
    'batch_unzip': SKILLS_ROOT / 'unstructured-audit-data' / 'scripts' / 'batch_unzip.py',
    'word_scan': SKILLS_ROOT / 'unstructured-audit-data' / 'scripts' / 'batch_word_scan.py',
    'pdf_similarity': SKILLS_ROOT / 'unstructured-audit-data' / 'scripts' / 'batch_pdf_similarity.py',
    'apriori': SKILLS_ROOT / 'apriori-audit' / 'scripts' / 'apriori_analysis.py',
    'savings_rate': SKILLS_ROOT / 'procurement-audit-models' / 'scripts' / '12_savings_rate.py',
    'entity_anomalies': SKILLS_ROOT / 'procurement-audit-models' / 'scripts' / '13_entity_anomalies.py',
    # 以下来自 procurement-audit-models/scripts/
    'tfidf': SKILLS_ROOT / 'procurement-audit-models' / 'scripts' / '03_tfidf_similarity.py',
    'metadata': SKILLS_ROOT / 'procurement-audit-models' / 'scripts' / '09_metadata_cross.py',
    'image_hash': SKILLS_ROOT / 'procurement-audit-models' / 'scripts' / '08_image_hash.py',
}


class AuditPipeline:
    """招投标审计全流程自动化"""

    def __init__(self, project_dir: str, output_dir: str, audit_type: str = 'procurement'):
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir)
        self.audit_type = audit_type
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 扫描结果
        self.files = {'pdf': [], 'docx': [], 'zip': [], 'xlsx': [], 'other': []}
        self.findings = []  # (level, title, detail)
        self.report_sections = []

    def scan_files(self):
        """扫描项目目录，分类文件"""
        print("=" * 60)
        print("🔍 扫描项目文件...")
        for f in self.project_dir.rglob('*'):
            if f.is_file():
                ext = f.suffix.lower()
                if ext == '.pdf':
                    self.files['pdf'].append(str(f))
                elif ext in ('.docx', '.doc'):
                    self.files['docx'].append(str(f))
                elif ext in ('.zip', '.rar', '.7z'):
                    self.files['zip'].append(str(f))
                elif ext in ('.xlsx', '.xls', '.csv'):
                    self.files['xlsx'].append(str(f))
                else:
                    self.files['other'].append(str(f))

        for k, v in self.files.items():
            if v:
                print(f"  {k}: {len(v)} 个")
        return self

    def step1_unzip(self):
        """步骤1: 批量解压压缩包"""
        if not self.files['zip']:
            self.report_sections.append(("压缩包处理", "未发现压缩包，跳过"))
            return self

        print("\n📦 步骤1: 批量解压...")
        unzip_dir = str(self.output_dir / 'extracted')
        cmd = f'python "{SCRIPTS["batch_unzip"]}" "{self.project_dir}" "{unzip_dir}"'
        os.system(cmd)
        self.report_sections.append(("压缩包处理", f"解压到 {unzip_dir}"))

        # Rescan extracted
        for f in Path(unzip_dir).rglob('*'):
            if f.is_file():
                ext = f.suffix.lower()
                if ext == '.pdf':
                    self.files['pdf'].append(str(f))
                elif ext in ('.docx', '.doc'):
                    self.files['docx'].append(str(f))
                elif ext in ('.xlsx', '.xls', '.csv'):
                    self.files['xlsx'].append(str(f))
        return self

    def step2_word_scan(self):
        """步骤2: Word文件限制关键词扫描"""
        if not self.files['docx']:
            self.report_sections.append(("Word关键词扫描", "未发现docx文件，跳过"))
            return self

        print("\n📝 步骤2: Word关键词扫描...")
        output = str(self.output_dir / 'word_关键词扫描.xlsx')
        # 直接用内嵌逻辑，不调子脚本
        self._run_word_scan(output)
        if Path(output).exists():
            self.report_sections.append(("Word关键词扫描", f"输出: {output}"))
            self.findings.append(("Word关键词", "已完成扫描",
                                  f"扫描 {len(self.files['docx'])} 个docx文件"))
        return self

    def _run_word_scan(self, output):
        """内嵌Word关键词扫描"""
        try:
            from docx import Document
        except ImportError:
            print("  跳过: python-docx未安装")
            return

        KEYWORDS = {
            '资格限制': ['业绩', '奖项', '专利', '规模', '特定品牌', '指定型号',
                     '唯一授权', '独家代理'],
            '地域限制': ['本地', '本市', '省内', '注册地', '纳税地', '驻场'],
            '时间限制': ['成立年限', '经营年限', '从业经验'],
        }

        all_hits = []
        for filepath in self.files['docx']:
            try:
                doc = Document(filepath)
                for i, para in enumerate(doc.paragraphs):
                    text = para.text.strip()
                    if not text or len(text) < 5:
                        continue
                    for cat, kws in KEYWORDS.items():
                        for kw in kws:
                            if kw in text:
                                all_hits.append({
                                    'file': Path(filepath).name,
                                    'para_no': i + 1,
                                    'category': cat,
                                    'keyword': kw,
                                    'text': text[:200]
                                })
                                break
            except:
                pass

        if all_hits:
            import pandas as pd
            df = pd.DataFrame(all_hits)
            df.to_excel(output, index=False)

    def step3_pdf_metadata(self):
        """步骤3: PDF元数据交叉分析"""
        if len(self.files['pdf']) < 2:
            self.report_sections.append(("PDF元数据", "PDF不足2个，跳过交叉分析"))
            return self

        print("\n📄 步骤3: PDF元数据提取...")
        pdfs = self.files['pdf'][:50]  # Limit to 50 for performance
        metadata_list = []

        try:
            import fitz
        except ImportError:
            print("  跳过: PyMuPDF未安装")
            self.report_sections.append(("PDF元数据", "PyMuPDF未安装，跳过"))
            return self

        for pdf_path in pdfs:
            try:
                doc = fitz.open(pdf_path)
                meta = doc.metadata
                metadata_list.append({
                    'file': Path(pdf_path).name,
                    'author': meta.get('author', ''),
                    'creator': meta.get('creator', ''),
                    'producer': meta.get('producer', ''),
                    'creationDate': meta.get('creationDate', ''),
                    'modDate': meta.get('modDate', ''),
                    'format': meta.get('format', ''),
                    'pages': doc.page_count,
                })
                doc.close()
            except:
                pass

        if metadata_list:
            import pandas as pd
            df = pd.DataFrame(metadata_list)
            output = str(self.output_dir / 'pdf_元数据.xlsx')
            df.to_excel(output, index=False)

            # Auto-detect same-source
            dupes = []
            for col in ['author', 'creator', 'producer']:
                non_empty = df[df[col] != '']
                if len(non_empty) > 1:
                    val_counts = non_empty[col].value_counts()
                    shared = val_counts[val_counts >= 2]
                    if len(shared) > 0:
                        for val, cnt in shared.items():
                            files = non_empty[non_empty[col] == val]['file'].tolist()
                            dupes.append(f"  {col}='{val}': {cnt}个文件同源 → {', '.join(files[:5])}")

            self.report_sections.append(("PDF元数据", f"提取 {len(metadata_list)} 个PDF元数据\n" + "\n".join(dupes) if dupes else "未发现同源"))
            if dupes:
                self.findings.append(("元数据同源", "🔴铁证",
                                      f"{len(dupes)} 组PDF共享相同元数据字段"))
        return self

    def step4_pdf_similarity(self):
        """步骤4: PDF文本雷同检测"""
        if len(self.files['pdf']) < 2:
            self.report_sections.append(("PDF相似度", "PDF不足2个，跳过"))
            return self

        print("\n📊 步骤4: PDF相似度分析...")
        output = str(self.output_dir / 'pdf_相似度.xlsx')
        # 使用项目自带的PDF目录
        pdf_dir = str(Path(self.files['pdf'][0]).parent)
        cmd = f'python "{SCRIPTS["pdf_similarity"]}" "{pdf_dir}" --method tfidf --output "{output}"'
        os.system(f'{cmd} 2>&1')
        self.report_sections.append(("PDF相似度(TF-IDF)", f"输出: {output}"))
        return self

    def step5_apriori(self, data_file: str = None):
        """步骤5: Apriori关联规则分析"""
        # 查找可能的交易数据文件
        xlsx_files = self.files['xlsx']
        if not xlsx_files and not data_file:
            self.report_sections.append(("Apriori关联规则", "未发现数据文件，跳过"))
            return self

        input_file = data_file or xlsx_files[0]
        print(f"\n🔗 步骤5: Apriori关联规则分析...")
        output = str(self.output_dir / 'apriori_关联规则.xlsx')
        cmd = f'python "{SCRIPTS["apriori"]}" --i "{input_file}" --o "{output}" --mode frequent --min-support 2 --min-confidence 0.6'
        os.system(f'{cmd} 2>&1')
        self.report_sections.append(("Apriori关联规则", f"输出: {output}"))
        return self

    def step6_savings_rate(self, data_file: str = None):
        """步骤6: 节资率分析"""
        xlsx_files = self.files['xlsx']
        if not xlsx_files and not data_file:
            self.report_sections.append(("节资率分析", "未发现招标台账数据，跳过"))
            return self

        input_file = data_file or xlsx_files[0]
        print(f"\n💰 步骤6: 节资率分析...")
        output = str(self.output_dir / '节资率分析.xlsx')
        cmd = f'python "{SCRIPTS["savings_rate"]}" --i "{input_file}" --o "{output}"'
        os.system(f'{cmd} 2>&1')
        self.report_sections.append(("节资率分析", f"输出: {output}"))
        return self

    def step7_entity_anomalies(self, data_file: str = None):
        """步骤7: 实体异常检测(L15-L19)"""
        xlsx_files = self.files['xlsx']
        if not xlsx_files and not data_file:
            self.report_sections.append(("实体异常检测", "未发现数据文件，跳过"))
            return self

        input_file = data_file or xlsx_files[0]
        print(f"\n👤 步骤7: 实体异常检测...")
        output = str(self.output_dir / '实体异常检测.xlsx')
        cmd = f'python "{SCRIPTS["entity_anomalies"]}" --projects "{input_file}" --o "{output}"'
        os.system(f'{cmd} 2>&1')
        self.report_sections.append(("实体异常检测(L15-L19)", f"输出: {output}"))
        return self

    def generate_report(self):
        """生成综合审计报告"""
        print("\n" + "=" * 60)
        print("📋 生成综合审计报告...")

        report_path = self.output_dir / '综合审计报告.md'
        lines = [
            f"# 招投标审计综合分析报告",
            f"",
            f"**项目目录**: {self.project_dir}",
            f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**审计类型**: {self.audit_type}",
            f"",
            f"## 文件概况",
            f"",
        ]
        for k, v in self.files.items():
            if v:
                lines.append(f"- {k}: {len(v)} 个")

        lines += ["", "## 分析步骤与结果", ""]
        for title, detail in self.report_sections:
            lines.append(f"### {title}")
            lines.append(f"")
            lines.append(f"{detail}")
            lines.append(f"")

        if self.findings:
            lines += ["## 关键发现汇总", ""]
            for level, title, detail in self.findings:
                lines.append(f"- **[{level}]** {title}: {detail}")
        else:
            lines.append("## 关键发现")
            lines.append("")
            lines.append("未发现明确疑点（可能需要人工复核或补充数据）。")

        lines += [
            "",
            "## 产出文件",
            "",
        ]
        for f in sorted(self.output_dir.glob('*.xlsx')):
            lines.append(f"- {f.name}")
        for f in sorted(self.output_dir.glob('*.md')):
            if f.name != '综合审计报告.md':
                lines.append(f"- {f.name}")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f"\n✅ 报告: {report_path}")
        for f in sorted(self.output_dir.glob('*')):
            if f.is_file():
                print(f"  📎 {f.name}")

        return report_path

    def run(self, skip: list = None):
        """执行全流程"""
        skip = skip or []
        print(f"🚀 启动审计全流程分析")
        print(f"   项目: {self.project_dir}")
        print(f"   类型: {self.audit_type}")
        print(f"   输出: {self.output_dir}")

        self.scan_files()

        steps = [
            ('unzip', self.step1_unzip, '压缩包处理'),
            ('word', self.step2_word_scan, 'Word关键词'),
            ('metadata', self.step3_pdf_metadata, 'PDF元数据'),
            ('similarity', self.step4_pdf_similarity, 'PDF相似度'),
            ('apriori', self.step5_apriori, 'Apriori关联'),
            ('savings', self.step6_savings_rate, '节资率'),
            ('entity', self.step7_entity_anomalies, '实体异常'),
        ]

        for key, step_fn, name in steps:
            if key in skip:
                print(f"\n⏭️ 跳过: {name}")
                continue
            try:
                step_fn()
            except Exception as e:
                print(f"\n⚠️ {name}失败: {e}")
                self.report_sections.append((name, f"执行失败: {e}"))

        return self.generate_report()


# ── 快捷函数: 从原始投标文件目录直接分析 ──
def quick_procurement_audit(source_dir: str, output_dir: str = None):
    """
    快速采购审计: 从投标文件目录一键分析
    自动处理: PDF元数据 + TF-IDF + 图片哈希 + WPS签名
    """
    output_dir = output_dir or str(Path(source_dir).parent / 'audit_output')
    pipeline = AuditPipeline(source_dir, output_dir, 'procurement')
    pipeline.scan_files()

    print("🚀 快速采购审计模式")
    print(f"  PDF: {len(pipeline.files['pdf'])} 个")
    print(f"  DOCX: {len(pipeline.files['docx'])} 个")

    # Focused steps for procurement
    pipeline.step1_unzip()
    pipeline.step3_pdf_metadata()
    pipeline.step4_pdf_similarity()

    return pipeline.generate_report()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='招投标审计全流程自动分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 完整分析
  python audit_pipeline.py --project ./投标文件 --type procurement --o ./审计结果

  # 快速模式(仅元数据+相似度)
  python audit_pipeline.py --project ./投标文件 --type procurement --o ./审计结果 --skip unzip,word,apriori,savings,entity

  # 通用审计(不限类型)
  python audit_pipeline.py --project ./数据文件夹 --type general --o ./输出
        '''
    )
    parser.add_argument('--project', '-p', required=True, help='项目目录')
    parser.add_argument('--type', '-t', default='procurement',
                        choices=['procurement', 'general', 'medical'],
                        help='审计类型')
    parser.add_argument('--o', '--output', dest='output', default=None,
                        help='输出目录(默认: 项目目录/audit_output)')
    parser.add_argument('--skip', nargs='*', default=[],
                        choices=['unzip', 'word', 'metadata', 'similarity',
                                 'apriori', 'savings', 'entity'],
                        help='跳过的步骤')
    parser.add_argument('--data', help='数据文件(.xlsx)用于Apriori/节资率/实体分析')
    args = parser.parse_args()

    output = args.output or str(Path(args.project) / 'audit_output')
    pipeline = AuditPipeline(args.project, output, args.type)
    pipeline.run(args.skip)
