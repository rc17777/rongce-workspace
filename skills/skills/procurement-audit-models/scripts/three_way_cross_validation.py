"""技能⑦ 三维交叉验证通用框架
来源：潍坊救助"低保表+公积金表+死亡表三维JOIN"
     莆田食堂"餐饮数据+贫困认定+宿舍确认"
用途：任意三个维度的数据交叉比对，发现不一致
"""
import sys, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')


class ThreeWayCrossValidator:
    """三维交叉验证通用引擎
    
    三维 = 资格维度 + 行为维度 + 排除维度
    
    原则：
    - 资格+行为 = 应该有（正常）
    - 资格+行为+排除 = 异常（不该有但发生了）
    - 资格+无行为 = 漏的（应该发生但没发生）
    - 无资格+行为 = 骗的（不该发生但发生了）
    """
    
    def __init__(self):
        self.issues = []
    
    def load_dimensions(self, dim_a, dim_b, dim_c, join_key):
        """加载三个维度数据
        
        dim_a: 资格/权利维度   {"实体A": {...资格信息...}}
        dim_b: 行为/发生维度   {"实体A": [...行为记录...]}
        dim_c: 排除/限制维度   {"实体A": {...排除信息...}}
        join_key: 关联键
        
        返回: 交叉结果矩阵
        """
        all_entities = set(dim_a.keys()) | set(dim_b.keys()) | set(dim_c.keys())
        
        results = []
        for entity in sorted(all_entities):
            a = entity in dim_a  # 有资格？
            b = entity in dim_b  # 有行为？
            c = entity in dim_c  # 被排除？
            
            result = {
                "实体": entity,
                "资格维度": a,
                "行为维度": b,
                "排除维度": c,
                "状态": self._classify(a, b, c),
                "资格详情": dim_a.get(entity),
                "行为详情": dim_b.get(entity),
                "排除详情": dim_c.get(entity)
            }
            results.append(result)
        
        return results
    
    def _classify(self, has_qual, has_action, is_excluded):
        """八态分类"""
        if has_qual and has_action and not is_excluded:
            return "正常"
        elif has_qual and has_action and is_excluded:
            return "🔴 异常：被排除但仍有资格和行为"
        elif has_qual and not has_action and not is_excluded:
            return "🟡 漏保：有资格无行为"
        elif has_qual and not has_action and is_excluded:
            return "正常排除（有资格但被排除，无行为）"
        elif not has_qual and has_action and not is_excluded:
            return "🔴 骗补：无资格有行为"
        elif not has_qual and has_action and is_excluded:
            return "🔴 异常：无资格且被排除但有行为"
        elif not has_qual and not has_action and not is_excluded:
            return "无关联"
        else:
            return "无关"
    
    def summary(self, results, dim_a_label="资格", dim_b_label="行为", 
                dim_c_label="排除"):
        """生成摘要统计"""
        stats = defaultdict(int)
        for r in results:
            stats[r["状态"]] += 1
        
        print(f"\n{'='*60}")
        print(f"三维交叉验证: {dim_a_label} × {dim_b_label} × {dim_c_label}")
        print(f"{'='*60}")
        print(f"总实体数: {len(results)}")
        for status, count in sorted(stats.items(), key=lambda x: -x[1]):
            print(f"  {status}: {count}个")
        
        return dict(stats)


# ===== 融策场景适配函数 =====

def bidder_3way_check(bidders, bid_records, blacklist):
    """【招投标】投标人三维验证
    
    资格维: 投标人资质/营业执照
    行为维: 实际投标记录
    排除维: 黑名单/失信名单/处罚记录
    
    发现:
    - 失信企业在黑名单中但仍参与投标 → 🔴
    - 有资质但从没投过标 → 为什么？
    """
    dim_a = {b["名称"]: b for b in bidders}
    dim_b = defaultdict(list)
    for r in bid_records:
        dim_b[r["投标人"]].append(r)
    dim_c = {b["名称"]: b for b in blacklist}
    
    cv = ThreeWayCrossValidator()
    results = cv.load_dimensions(dim_a, dim_b, dim_c, "名称")
    cv.summary(results, "投标资质", "投标行为", "黑名单")
    
    # 重点标记
    flagged = [r for r in results if "🔴" in r["状态"]]
    return flagged


def subsidy_3way_check(eligible_list, payment_records, dead_relocated):
    """【绩效评价】补贴三维验证
    
    资格维: 符合条件的受益人
    行为维: 补贴发放记录
    排除维: 死亡/迁出/已就业
    
    发现:
    - 已死亡但仍在领补贴 → 🔴
    - 符合条件但从未领补贴 → 🟡 政策落实不到位
    - 不符合条件但在领补贴 → 🔴 骗补
    """
    dim_a = {p["身份证号"]: p for p in eligible_list}
    dim_b = defaultdict(list)
    for r in payment_records:
        dim_b[r["身份证号"]].append(r)
    dim_c = {p["身份证号"]: p for p in dead_relocated}
    
    cv = ThreeWayCrossValidator()
    results = cv.load_dimensions(dim_a, dim_b, dim_c, "身份证号")
    cv.summary(results, "补贴资格", "发放记录", "排除名单(死亡/迁出)")
    
    flagged = [r for r in results if "🔴" in r["状态"]]
    missed = [r for r in results if "漏保" in r["状态"]]
    return flagged, missed


def debt_3way_check(project_plan, fund_usage, progress_check):
    """【专项债】资金使用三维验证
    
    资格维: 专项债项目计划（资金用途）
    行为维: 资金实际使用记录
    排除维: 项目进度（完工/暂停/撤销）
    
    发现:
    - 已完工项目继续使用资金 → 🔴 虚报进度
    - 有资金计划但无使用记录 → 🟡 资金闲置
    - 无计划有使用 → 🔴 挪用
    """
    dim_a = {p["项目"]: p for p in project_plan}
    dim_b = defaultdict(list)
    for r in fund_usage:
        dim_b[r["项目"]].append(r)
    dim_c = {p["项目"]: p for p in progress_check}
    
    cv = ThreeWayCrossValidator()
    results = cv.load_dimensions(dim_a, dim_b, dim_c, "项目")
    cv.summary(results, "资金计划", "实际使用", "项目进度")
    
    flagged = [r for r in results if "🔴" in r["状态"]]
    return flagged


# ===== 示例 =====
if __name__ == "__main__":
    # 【场景1】投标人三维验证
    print("【场景1】招投标：投标人三维验证")
    bidders = [
        {"名称":"A建设","资质":"建筑一级"},
        {"名称":"B建设","资质":"建筑一级"},
        {"名称":"C建设","资质":"建筑二级"},
        {"名称":"D建设","资质":"建筑一级"},  # 有资质但从没投过标
        {"名称":"E建设","资质":"建筑一级"},
    ]
    bid_records = [
        {"投标人":"A建设","项目":"P1"},
        {"投标人":"A建设","项目":"P2"},
        {"投标人":"B建设","项目":"P1"},
        {"投标人":"E建设","项目":"P2"},
        {"投标人":"F建设","项目":"P1"},  # F不在资质库中
    ]
    blacklist = [
        {"名称":"B建设","原因":"2024年失信处罚"},
    ]
    
    flagged = bidder_3way_check(bidders, bid_records, blacklist)
    if flagged:
        print(f"\n⚠️ 重点关注:")
        for f in flagged:
            print(f"  {f['实体']}: {f['状态']}")
    
    # 【场景2】补贴三维验证
    print(f"\n{'='*60}")
    print("【场景2】绩效评价：补贴三维验证")
    
    eligible = [
        {"身份证号":"510101","姓名":"张三"},
        {"身份证号":"510102","姓名":"李四"},
        {"身份证号":"510103","姓名":"王五"},
        {"身份证号":"510104","姓名":"赵六"},
    ]
    payments = [
        {"身份证号":"510101","金额":500},
        {"身份证号":"510102","金额":500},
        {"身份证号":"510102","金额":500},
        {"身份证号":"510105","金额":500},  # 不应在名单中
    ]
    dead = [
        {"身份证号":"510102","死亡日期":"2025-01-01"},  # 已死亡
    ]
    
    flagged, missed = subsidy_3way_check(eligible, payments, dead)
    print(f"\n🔴 骗补: {len(flagged)} | 🟡 漏补: {len(missed)}")
