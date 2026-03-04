"""Utility for copying a local SQLite database into a MySQL server.

Usage from the project root:

    python migrate_sqlite_to_mysql.py --sqlite bibliography.db \
            --mysql-host localhost --mysql-user root \
            --mysql-password secret --mysql-db biblioteca

It will create the target database if it doesn't exist, then recreate each table
with a very simple translation of types and finally copy all rows.  The code is
intended for the small schema of this project (libro, prestamo, rese\u00f1a,
"biblioteca_virtual", etc) and performs only minimal datatype conversion.

You can also use MySQL Workbench yourself by running the `CREATE DATABASE`
statement shown in the comments below and then executing this script to
populate it.

Note: depending on your sqlite file the generated schema may need manual
adjustment; review the printed SQL before importing.
"""

import argparse
import re
import sqlite3
import sys

import mysql.connector


def translate_type(sql):
    # naive rewrite: replace "INTEGER PRIMARY KEY AUTOINCREMENT" with
    # "INT AUTO_INCREMENT PRIMARY KEY"; strip "AUTOINCREMENT" otherwise
    sql = sql.replace("AUTOINCREMENT", "AUTO_INCREMENT")
    # sqlite allows "TEXT", "INTEGER", etc; leave them as-is since mysql
    # understands them.  ensure TEXT -> TEXT CHARACTER SET utf8mb4
    sql = re.sub(r"TEXT", "TEXT CHARACTER SET utf8mb4", sql, flags=re.I)
    return sql


def main():
    parser = argparse.ArgumentParser(description="Copy SQLite DB into MySQL")
    parser.add_argument("--sqlite", required=True, help="path to sqlite file")
    parser.add_argument("--mysql-host", default="localhost")
    parser.add_argument("--mysql-user", required=True)
    parser.add_argument("--mysql-password", default="")
    parser.add_argument("--mysql-db", required=True)

    args = parser.parse_args()

    sq = sqlite3.connect(args.sqlite)
    sq.row_factory = sqlite3.Row
    cur = sq.cursor()

    # connect to mysql server (without specifying database yet)
    admin = mysql.connector.connect(
        host=args.mysql_host,
        user=args.mysql_user,
        password=args.mysql_password,
    )
    admin_cur = admin.cursor()
    admin_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{args.mysql_db}` "
                      "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    admin.commit()
    admin_cur.close()
    admin.close()

    # connect to the target database
    my = mysql.connector.connect(
        host=args.mysql_host,
        user=args.mysql_user,
        password=args.mysql_password,
        database=args.mysql_db,
        charset='utf8mb4',
    )
    my_cur = my.cursor()

    # iterate tables from sqlite
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cur.fetchall()
    for row in tables:
        name = row[0]
        create_sql = row[1]
        print("\ncreating table", name)
        print(create_sql)
        create_sql = translate_type(create_sql)
        # MySQL doesn't like "IF NOT EXISTS" inside the field list for
        # TEXT columns; rely on the clause at the front instead.
        my_cur.execute(f"DROP TABLE IF EXISTS `{name}`")
        my_cur.execute(create_sql)
        my.commit()

        # copy the data
        sel = sq.execute(f"SELECT * FROM `{name}`")
        rows = sel.fetchall()
        if not rows:
            continue
        cols = rows[0].keys()
        cols_list = ",".join(f"`{c}`" for c in cols)
        placeholders = ",".join(["%s"] * len(cols))
        insert_sql = f"INSERT INTO `{name}` ({cols_list}) VALUES ({placeholders})"
        print(f"  inserting {len(rows)} rows")
        for r in rows:
            my_cur.execute(insert_sql, tuple(r))
        my.commit()

    my_cur.close()
    sq.close()
    print("\nDone. your MySQL database is populated.")


if __name__ == "__main__":
    main()
