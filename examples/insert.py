#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sqlite3

con = sqlite3.connect('mydatabase.db')
cursor_obj = con.cursor()
cursor_obj.execute("INSERT INTO employees VALUES(1, 'John', 700, 'HR', 'Manager', '2017-01-04')")
con.close()