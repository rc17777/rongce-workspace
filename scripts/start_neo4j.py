import subprocess
import os

# Set Java path for Neo4j
os.environ['JAVA_HOME'] = r'C:\Users\scrccpa\.Neo4jDesktop\distributions\java\zulu17.58.21-ca-jdk17.0.15'
os.environ['PATH'] = os.environ['JAVA_HOME'] + r'\bin;' + os.environ.get('PATH', '')

# Start Neo4j as background process
neo4j_home = r'C:\neo4j\neo4j-enterprise-5.24.0'
process = subprocess.Popen(
    [os.path.join(neo4j_home, 'bin', 'neo4j.bat'), 'console'],
    cwd=neo4j_home,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
)

print(f"Neo4j started with PID: {process.pid}")
print(f"Bolt: bolt://localhost:7687")
print(f"HTTP: http://localhost:7474")
print("Default user: neo4j/neo4j")
