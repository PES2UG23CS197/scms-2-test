import mysql.connector
import os

def get_connection():
    # Detect if running in GitHub Actions CI
    is_ci = os.getenv("CI") == "true"

    if is_ci:
        # CI/CD environment (matches ci.yml)
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="root",
            database="scms"
        )
    else:
        # Local development
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="REPLACE_WITH_YOUR_LOCAL_SQL_PASSWORD",
            database="scms"
        )