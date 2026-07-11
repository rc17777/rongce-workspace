from neo4j import GraphDatabase

try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'rongce123'))
    with driver.session() as session:
        result = session.run('RETURN 1 as num')
        record = result.single()
        print(f'Neo4j connection OK: {record["num"]}')
    driver.close()
    print('Neo4j is running and accessible!')
except Exception as e:
    print(f'Error: {e}')
