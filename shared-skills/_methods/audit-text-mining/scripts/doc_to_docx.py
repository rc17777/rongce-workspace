"""
审计文本挖掘 - 格式转换工具
将目录中所有 .doc 文件批量转换为 .docx 格式。

用法：python doc_to_docx.py <文档目录路径>
依赖：pip install pywin32（需本机安装 Microsoft Word）
"""

import os
import sys
import glob

def convert_doc_to_docx(directory):
    """批量转换 .doc → .docx"""
    try:
        import win32com.client as win32
    except ImportError:
        print("❌ 缺少 pywin32 库，请执行：pip install pywin32")
        print("   注意：此脚本需要本机安装 Microsoft Word")
        return

    word = None
    try:
        word = win32.Dispatch("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        doc_files = glob.glob(os.path.join(directory, "*.doc"))
        # 排除已经是 .docx 的文件
        doc_files = [f for f in doc_files if not f.endswith(".docx")]

        if not doc_files:
            print("📭 目录中没有找到 .doc 文件")
            return

        print(f"📄 找到 {len(doc_files)} 个 .doc 文件，开始转换...")
        converted = 0
        failed = []

        for doc_path in doc_files:
            try:
                doc = word.Documents.Open(doc_path)
                new_path = doc_path + "x"  # .doc → .docx
                doc.SaveAs2(new_path, FileFormat=16)  # 16 = wdFormatXMLDocument
                doc.Close()
                converted += 1
                print(f"  ✅ {os.path.basename(doc_path)} → {os.path.basename(new_path)}")
            except Exception as e:
                failed.append((os.path.basename(doc_path), str(e)))
                print(f"  ❌ {os.path.basename(doc_path)}: {e}")

        print(f"\n📊 转换完成：成功 {converted}/{len(doc_files)}")

        if failed:
            print(f"⚠️  失败 {len(failed)} 个：")
            for name, err in failed:
                print(f"     - {name}: {err}")

    finally:
        if word:
            word.Quit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python doc_to_docx.py <文档目录路径>")
        print("示例：python doc_to_docx.py D:\\审计项目\\会议纪要\\")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"❌ 目录不存在：{directory}")
        sys.exit(1)

    convert_doc_to_docx(directory)
