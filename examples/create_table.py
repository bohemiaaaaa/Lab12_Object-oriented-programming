#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3

con = sqlite3.connect('mydatabase.db')
cursor = con.cursor()
cursor.execute("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, salary REAL, department TEXT, position TEXT, hireDate TEXT)")
cursor.close()
con.close()