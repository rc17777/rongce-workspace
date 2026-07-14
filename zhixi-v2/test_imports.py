import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing imports...")

try:
    from skills.penetrating_audit.tool import PenetratingAuditTool
    print("OK penetrating_audit")
except Exception as e:
    print(f"FAIL penetrating_audit: {e}")

try:
    from skills.special_bond_audit.tool import SpecialBondAuditTool
    print("OK special_bond_audit")
except Exception as e:
    print(f"FAIL special_bond_audit: {e}")

try:
    from skills.bim_engineering_audit.tool import BIMEngineeringAuditTool
    print("OK bim_engineering_audit")
except Exception as e:
    print(f"FAIL bim_engineering_audit: {e}")

try:
    from skills.audit_risk_portrait.tool import AuditRiskPortraitTool
    print("OK audit_risk_portrait")
except Exception as e:
    print(f"FAIL audit_risk_portrait: {e}")

try:
    from skills.dynamic_audit_alert.tool import DynamicAuditAlertTool
    print("OK dynamic_audit_alert")
except Exception as e:
    print(f"FAIL dynamic_audit_alert: {e}")

print("Done")
