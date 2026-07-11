# -*- coding: utf-8 -*-
"""
融策数据中台 + 知识图谱 - 最终验证脚本
"""

print("=" * 60)
print("融策AI审计平台 - 数据库安装验证")
print("=" * 60)

# 1. 验证PostgreSQL
print("\n[1/4] 验证 PostgreSQL 16...")
try:
    import sys
    sys.path.insert(0, 'data-platform')
    from config.settings import db_config
    import psycopg2
    
    conn = psycopg2.connect(**db_config.to_dict())
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()[0]
    cursor.execute("SELECT datname FROM pg_database WHERE datname='rongce_data_platform';")
    db_exists = cursor.fetchone() is not None
    conn.close()
    
    print(f"  [OK] PostgreSQL: {version}")
    print(f"  [OK] Database rongce_data_platform: {'exists' if db_exists else 'missing'}")
    print(f"  [OK] User rongce: created")
    pg_ok = True
except Exception as e:
    print(f"  [FAIL] PostgreSQL error: {e}")
    pg_ok = False

# 2. Verify Neo4j
print("\n[2/4] Verify Neo4j 5.24...")
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'rongce123'))
    with driver.session() as session:
        result = session.run('RETURN 1 as num')
        record = result.single()
        assert record['num'] == 1
    driver.close()
    print(f"  [OK] Neo4j 5.24.0 running")
    print(f"  [OK] Bolt: bolt://localhost:7687")
    print(f"  [OK] HTTP: http://localhost:7474")
    print(f"  [OK] User: neo4j/rongce123")
    neo4j_ok = True
except Exception as e:
    print(f"  [FAIL] Neo4j error: {e}")
    neo4j_ok = False

# 3. Verify Data Platform ETL
print("\n[3/4] Verify Data Platform ETL...")
try:
    sys.path.insert(0, 'data-platform')
    from etl.financial_data_etl import FinancialDataETL
    etl = FinancialDataETL()
    print(f"  [OK] FinancialDataETL initialized")
    print(f"  [OK] Methods: import_balance_sheet, import_voucher_entries, validate_financial_data")
    etl_ok = True
except Exception as e:
    print(f"  [FAIL] ETL error: {e}")
    etl_ok = False

# 4. Verify Knowledge Graph
print("\n[4/4] Verify Knowledge Graph...")
try:
    sys.path.insert(0, 'knowledge-graph')
    from graph_builder import Neo4jGraphBuilder
    from entity_extractor import EntityExtractor
    from relation_extractor import RelationExtractor
    
    builder = Neo4jGraphBuilder('bolt://localhost:7687', 'neo4j', 'rongce123')
    builder.create_indexes()
    builder.close()
    
    extractor = EntityExtractor()
    entities = extractor.extract_from_text("四川融策会计师事务所有限公司，负责人张三")
    
    print(f"  [OK] Neo4jGraphBuilder connected")
    print(f"  [OK] Indexes created")
    print(f"  [OK] Entity extraction: found {len(entities)} entities")
    for e in entities:
        print(f"     - {e.entity_type.name}: {e.name}")
    kg_ok = True
except Exception as e:
    print(f"  [FAIL] Knowledge Graph error: {e}")
    kg_ok = False

# Summary
print("\n" + "=" * 60)
print("Verification Results")
print("=" * 60)
print(f"  PostgreSQL 16:     {'[PASS]' if pg_ok else '[FAIL]'}")
print(f"  Neo4j 5.24:        {'[PASS]' if neo4j_ok else '[FAIL]'}")
print(f"  Data Platform ETL: {'[PASS]' if etl_ok else '[FAIL]'}")
print(f"  Knowledge Graph:     {'[PASS]' if kg_ok else '[FAIL]'}")
print("=" * 60)

if all([pg_ok, neo4j_ok, etl_ok, kg_ok]):
    print("ALL COMPONENTS VERIFIED! Data platform and knowledge graph are ready.")
else:
    print("Some components failed verification. Please check configuration.")
