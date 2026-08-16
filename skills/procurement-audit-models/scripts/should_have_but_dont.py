"""技能④ LEFT JOIN + IS NULL → "应有未有"异常检测
来源：潍坊救助"儿童应享未享→LEFT JOIN孤儿表=NULL"
核心模式：资格名单 LEFT JOIN 发生名单 → 有资格但没发生 = 疑点
"""
import sys, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')


def should_have_but_dont(qualify_list, occur_list, key_field, 
                         qualify_label="资格名单", occur_label="发生名单"):
    """【核心】LEFT JOIN + IS NULL
    
    输入:
      qualify_list: 资格/权利名单（应该有的）
      occur_list: 实际发生/发放名单（实际发生的）
      key_field: 关联字段名
    
    输出:
      在qualify中但不在occur中的记录 → "应享未享"
    """
    # 构建occur的key集合
    occur_keys = {r.get(key_field) for r in occur_list if r.get(key_field)}
    
    missing = []
    for record in qualify_list:
        key = record.get(key_field)
        if key and key not in occur_keys:
            missing.append({
                **record,
                "_标志": f"应在{occur_label}中但缺失",
                "_来源": qualify_label
            })
    
    return missing


def shouldnt_have_but_have(qualify_list, occur_list, key_field,
                           qualify_label="资格名单", occur_label="发生名单"):
    """【镜像】INNER JOIN 异常
    
    在实际发生中但不在资格名单中 → "不该拿的拿了"
    """
    qualify_keys = {r.get(key_field) for r in qualify_list if r.get(key_field)}
    
    extra = []
    for record in occur_list:
        key = record.get(key_field)
        if key and key not in qualify_keys:
            extra.append({
                **record,
                "_标志": f"不在{qualify_label}中但出现在{occur_label}",
                "_来源": occur_label
            })
    
    return extra


def both_lists_analysis(qualify_list, occur_list, key_field,
                        qualify_label="资格名单", occur_label="发生名单"):
    """【完整分析】两表对比
    
    三态分析：
    1. 该拿的拿了（正常）
    2. 该拿的没拿（漏保/应享未享）
    3. 不该拿的拿了（骗补/违规）
    """
    missing = should_have_but_dont(qualify_list, occur_list, key_field,
                                   qualify_label, occur_label)
    extra = shouldnt_have_but_have(qualify_list, occur_list, key_field,
                                   qualify_label, occur_label)
    
    qualify_keys = {r.get(key_field) for r in qualify_list if r.get(key_field)}
    
    normal = [r for r in occur_list 
              if r.get(key_field) and r.get(key_field) in qualify_keys]
    
    return {
        "总资格数": len(qualify_list),
        "总发生数": len(occur_list),
        "正常（有资格且有发生）": len(normal),
        "应享未享（有资格无发生）": len(missing),
        "不该得（无资格有发生）": len(extra),
        "应享未享详单": missing,
        "不该得详单": extra
    }


# ===== 融策业务场景专用函数 =====

def check_should_bid_but_didnt(proj_quota, actual_bids):
    """【专项债/招投标】应招标未招标检测
    
    proj_quota: 项目达到招标限额标准的清单
      [{"项目名称":"XX","投资额":500,"限额":400,"是否应招标":"是"},...]
    actual_bids: 实际进行了招标的项目清单
      [{"项目名称":"XX","招标编号":"TQ-2025-001"},...]
    
    返回: 达到限额但未进行招标的项目
    """
    qualified = [p for p in proj_quota if p.get("是否应招标") == "是" 
                 or p.get("投资额", 0) >= p.get("限额", 999999)]
    
    missing = should_have_but_dont(qualified, actual_bids, "项目名称",
                                   "应招标项目", "已招标项目")
    
    return {
        "应招标项目数": len(qualified),
        "已招标项目数": len(actual_bids),
        "应招标未招标": len(missing),
        "详情": missing
    }


def check_asset_accounting(asset_ledger, physical_check):
    """【资产清查】账实不符检测
    
    asset_ledger: 固定资产台账（账上有）
    physical_check: 实际盘点记录（实际有）
    
    返回:
      账上有但盘亏的 + 账无但盘盈的
    """
    result = both_lists_analysis(asset_ledger, physical_check, "资产编号",
                                 "固定资产台账", "实际盘点")
    # 重命名
    result["盘亏（账有实无）"] = result.pop("应享未享（有资格无发生）", 0)
    result["盘盈（账无实有）"] = result.pop("不该得（无资格有发生）", 0)
    return result


def check_policy_coverage(policy_targets, actual_beneficiaries):
    """【绩效评价】政策覆盖率检测
    
    policy_targets: 政策应覆盖的目标对象
    actual_beneficiaries: 实际享受了政策的受益人
    
    返回: 政策覆盖率 + 未覆盖名单
    """
    result = both_lists_analysis(policy_targets, actual_beneficiaries, 
                                 "对象标识", "政策应覆盖", "实际受益")
    coverage = result["正常（有资格且有发生）"] / result["总资格数"] * 100 \
               if result["总资格数"] > 0 else 0
    result["政策覆盖率%"] = round(coverage, 1)
    return result


# ===== 示例 =====
if __name__ == "__main__":
    print("=" * 60)
    print("LEFT JOIN + IS NULL — '应有未有'异常检测")
    print("=" * 60)
    
    # 示例1：专项债应招标未招标
    print("\n【场景1】专项债：应招标未招标")
    proj_quota = [
        {"项目名称":"老旧小区改造A","投资额":800,"限额":400,"是否应招标":"是"},
        {"项目名称":"老旧小区改造B","投资额":600,"限额":400,"是否应招标":"是"},
        {"项目名称":"道路维修C","投资额":300,"限额":400,"是否应招标":"否"},
        {"项目名称":"管网更新D","投资额":500,"限额":400,"是否应招标":"是"},
    ]
    actual_bids = [
        {"项目名称":"老旧小区改造A","招标编号":"TQ-2025-001"},
        {"项目名称":"道路维修C","招标编号":"TQ-2025-002"},
    ]
    
    r = check_should_bid_but_didnt(proj_quota, actual_bids)
    print(f"  应招标: {r['应招标项目数']} | 已招标: {r['已招标项目数']}")
    print(f"  ⚠️ 应招标未招标: {r['应招标未招标']}")
    for d in r['详情']:
        print(f"    · {d['项目名称']} (投资额:{d['投资额']}万) {d['_标志']}")
    
    # 示例2：资产清查账实不符
    print("\n【场景2】资产清查：账实不符")
    asset_ledger = [
        {"资产编号":"ZC-001","资产名称":"服务器A"},
        {"资产编号":"ZC-002","资产名称":"服务器B"},
        {"资产编号":"ZC-003","资产名称":"打印机C"},
        {"资产编号":"ZC-004","资产名称":"投影仪D"},
        {"资产编号":"ZC-005","资产名称":"空调E"},
    ]
    physical_check = [
        {"资产编号":"ZC-001","资产名称":"服务器A"},
        {"资产编号":"ZC-003","资产名称":"打印机C"},
        {"资产编号":"ZC-005","资产名称":"空调E"},
        {"资产编号":"ZC-006","资产名称":"笔记本电脑F"},
    ]
    
    r = check_asset_accounting(asset_ledger, physical_check)
    print(f"  账上: {r['总资格数']} | 实盘: {r['总发生数']}")
    print(f"  ⚠️ 盘亏: {r['盘亏（账有实无）']} | 盘盈: {r['盘盈（账无实有）']}")
    
    # 示例3：绩效评价政策覆盖率
    print("\n【场景3】绩效评价：政策覆盖率")
    policy_targets = [
        {"对象标识":"H001"}, {"对象标识":"H002"}, {"对象标识":"H003"},
        {"对象标识":"H004"}, {"对象标识":"H005"}, {"对象标识":"H006"},
    ]
    actual_beneficiaries = [
        {"对象标识":"H001"}, {"对象标识":"H003"}, {"对象标识":"H005"},
        {"对象标识":"H007"},  # 不应属于但实际受益
    ]
    
    r = check_policy_coverage(policy_targets, actual_beneficiaries)
    print(f"  应覆盖: {r['总资格数']} | 实际受益: {r['总发生数']}")
    print(f"  政策覆盖率: {r['政策覆盖率%']}%")
    print(f"  ⚠️ 漏保: {r['应享未享（有资格无发生）']} | 错保: {r['不该得（无资格有发生）']}")
