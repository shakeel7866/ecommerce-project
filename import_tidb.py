import getpass
import mysql.connector

HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
PORT = 4000
USER = "2kKC61ejBsqb8kJ.root"
DB = "ecommerce_db"
CA = r"C:\Users\shake\Downloads\isrgrootx1.pem"
SQL_FILE = "ecommerce_db_backup.sql"

password = getpass.getpass("TiDB password: ")

conn = mysql.connector.connect(
    host=HOST,
    port=PORT,
    user=USER,
    password=password,
    database=DB,
    ssl_ca=CA,
    ssl_verify_cert=True,
    ssl_verify_identity=True
)

cursor = conn.cursor()

print("Connected to TiDB.")

# Disable foreign-key checks during import
cursor.execute("SET FOREIGN_KEY_CHECKS=0")
conn.commit()

# Remove tables from the previous partial import
print("Cleaning previous partial import...")

cursor.execute("SHOW TABLES")
existing_tables = [row[0] for row in cursor.fetchall()]

for table in existing_tables:
    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")

conn.commit()

print(f"Removed {len(existing_tables)} existing tables.")

# Read SQL dump
with open(SQL_FILE, "r", encoding="utf-16") as f:
    sql = f.read()

# Split SQL statements
statements = []
current = []

for line in sql.splitlines():
    stripped = line.strip()

    # Skip normal comments
    if stripped.startswith("--"):
        continue

    # Skip MariaDB sandbox comment
    if stripped.startswith("/*M!"):
        continue

    # Skip dump configuration statements
    if stripped.startswith("/*!"):
        continue

    current.append(line)

    if stripped.endswith(";"):
        statement = "\n".join(current).strip()

        if statement:
            statements.append(statement)

        current = []

if current:
    statement = "\n".join(current).strip()
    if statement:
        statements.append(statement)

print(f"Found {len(statements)} SQL statements.")
print("Starting import...")

success = 0

for i, statement in enumerate(statements, 1):

    try:
        cursor.execute(statement)
        conn.commit()
        success += 1

        if i % 10 == 0:
            print(f"Imported {i}/{len(statements)} statements...")

    except Exception as e:
        print(f"\nERROR at statement {i}:")
        print(str(e))
        print("\nSQL:")
        print(statement[:1000])

        conn.rollback()
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()

        raise

# Re-enable foreign-key checks
cursor.execute("SET FOREIGN_KEY_CHECKS=1")
conn.commit()

# Verify tables
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

print()
print("===================================")
print("IMPORT COMPLETE")
print("===================================")
print(f"SQL statements imported: {success}")
print(f"Tables in TiDB: {len(tables)}")

for table in tables:
    print(" -", table[0])

cursor.close()
conn.close()
