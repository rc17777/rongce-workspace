from neo4j import GraphDatabase

# Connect with default password and change it
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'neo4j'))
with driver.session(database='system') as session:
    session.run("ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'rongce123'")
print('Password changed successfully!')
driver.close()
