"""
Build script for PyInstaller packaging.
Usage: python build_exe.py
Output: dist/zhixi_collector.exe
"""
import subprocess
import sys
import io
from pathlib import Path

# Force UTF-8 for console output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 依赖列表（PyInstaller 可能漏掉的 hidden import）
HIDDEN_IMPORTS = [
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "pymysql",
    "sqlalchemy.dialects.mysql.pymysql",
    "sqlalchemy.dialects.postgresql",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.mssql",
    "sqlalchemy.dialects.mssql.pyodbc",
    "flask",
    "flask.json",
    "werkzeug",
    "jinja2",
]

# 需要随 exe 一起打包的文件
def build():
    src = Path(__file__).parent / "web_collector.py"
    dist = Path(__file__).parent / "dist"
    name = "智析智能数据采集器"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        f"--name={name}",
        "--clean",
        "--add-data", f"{src.parent / 'profiles'}{os.pathsep}profiles",
    ]

    for imp in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", imp])

    cmd.append(str(src))

    print(f"📦 开始打包: {name}.exe")
    print(f"   源文件: {src}")
    print(f"   输出目录: {dist}")
    print(f"   命令: {' '.join(cmd)}")
    print()

    subprocess.run(cmd, cwd=str(src.parent), check=True)

    output = dist / f"{name}.exe"
    if output.exists():
        size_mb = output.stat().st_size / (1024 * 1024)
        print(f"\n✅ 打包完成: {output}")
        print(f"   文件大小: {size_mb:.1f} MB")
        print(f"\n   使用说明:")
        print(f"   1. 将 {name}.exe 复制到目标电脑")
        print(f"   2. 双击运行，自动打开浏览器")
        print(f"   3. 访问 http://127.0.0.1:5000 开始使用")
        print(f"   4. profiles/ 和 collected_data/ 会自动在 exe 所在目录创建")
    else:
        print("\n❌ 打包失败，请检查上方错误信息")

if __name__ == "__main__":
    import os
    build()
