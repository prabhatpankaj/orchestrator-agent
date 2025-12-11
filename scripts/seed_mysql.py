import pandas as pd
import pymysql
import os
import time

# Config
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DB = os.getenv("MYSQL_DB", "jobs_db")
CSV_PATH = "jobs.csv"

def wait_for_mysql():
    print("Waiting for MySQL...")
    for _ in range(30):
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD
            )
            conn.close()
            print("MySQL is ready.")
            return
        except Exception:
            time.sleep(2)
    raise Exception("MySQL failed to start.")

def seed_data():
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cursor = conn.cursor()

    # Create DB if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
    cursor.execute(f"USE {MYSQL_DB}")

    # Read init.sql
    with open("init_db.sql", "r") as f:
        sql = f.read()
        cursor.execute(sql)
    
    conn.commit()

    # Load CSV
    print(f"Loading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)

    # Insert data
    print("Inserting data...")
    sql = """
    INSERT IGNORE INTO jobs (job_id, title, description, location, experience, skills)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    values = []
    for _, row in df.iterrows():
        values.append((
            str(row["job_id"]),
            row["title"],
            row["description"],
            row["location"],
            row["experience"],
            row["skills"] if pd.notna(row["skills"]) else ""
        ))
    
    cursor.executemany(sql, values)
    conn.commit()
    print(f"✅ Seeded {len(values)} jobs into MySQL.")

    conn.close()

if __name__ == "__main__":
    wait_for_mysql()
    seed_data()
