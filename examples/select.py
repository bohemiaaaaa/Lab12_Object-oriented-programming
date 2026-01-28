#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3

con = sqlite3.connect('mydatabase.db')

def sql_fetch(con):
    cursor_obj = con.cursor()
    cursor_obj.execute("SELECT * FROM employees")
    rows = cursor_obj.fetchall()
    for row in rows:
        print(row)

sql_fetch(con)