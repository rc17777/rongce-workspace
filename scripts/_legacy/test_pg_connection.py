import sys
sys.path.insert(0, 'data-platform')
from config.settings import db_config
import psycopg2

print(f'Connecting to: {db_config.host}:{db_config.port}/{db_config.database}')
conn = psycopg2.connect(**db_config.to_dict())
cursor = conn.cursor()
cursor.execute('SELECT version();')
print(f'PostgreSQL version: {cursor.fetchone()[0]}')
cursor.execute("SELECT datname FROM pg_database WHERE datname='rongce_data_platform';")
print(f'Database exists: {cursor.fetchone() is not None}')
conn.close()
print('Connection OK!')
