#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Post:
    id: int
    title: str


@dataclass(frozen=True)
class Worker:
    name: str
    post: str
    year: int


class StaffRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._create_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _create_db(self) -> None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_title TEXT NOT NULL UNIQUE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workers (
                worker_id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_name TEXT NOT NULL,
                post_id INTEGER NOT NULL,
                worker_year INTEGER NOT NULL,
                FOREIGN KEY(post_id) REFERENCES posts(post_id)
            )
            """
        )

        conn.commit()
        conn.close()

    def get_or_create_post(self, title: str) -> int | None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT post_id FROM posts WHERE post_title = ?", (title,))
        row = cursor.fetchone()

        if row is None:
            cursor.execute("INSERT INTO posts (post_title) VALUES (?)", (title,))
            post_id = cursor.lastrowid
            conn.commit()
        else:
            post_id = row[0]

        conn.close()
        return post_id

    def add_worker(self, name: str, post: str, year: int) -> None:
        post_id = self.get_or_create_post(post)

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO workers (worker_name, post_id, worker_year)
            VALUES (?, ?, ?)
            """,
            (name, post_id, year),
        )

        conn.commit()
        conn.close()

    def get_all_workers(self) -> list[Worker]:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT workers.worker_name,
                   posts.post_title,
                   workers.worker_year
            FROM workers
            JOIN posts ON posts.post_id = workers.post_id
            """
        )

        rows = cursor.fetchall()
        conn.close()

        return [Worker(row[0], row[1], row[2]) for row in rows]

    def select_by_period(self, period: int) -> list[Worker]:
        current_year = datetime.now().year

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT workers.worker_name,
                   posts.post_title,
                   workers.worker_year
            FROM workers
            JOIN posts ON posts.post_id = workers.post_id
            WHERE (? - workers.worker_year) >= ?
            """,
            (current_year, period),
        )

        rows = cursor.fetchall()
        conn.close()

        return [Worker(row[0], row[1], row[2]) for row in rows]


def display_workers(workers: list[Worker]) -> None:
    if not workers:
        print("Список работников пуст.")
        return

    line = "+-{}-+-{}-+-{}-+-{}-+".format("-" * 4, "-" * 30, "-" * 20, "-" * 8)

    print(line)
    print(
        "| {:^4} | {:^30} | {:^20} | {:^8} |".format("№", "Ф.И.О.", "Должность", "Год")
    )
    print(line)

    for idx, w in enumerate(workers, 1):
        print("| {:>4} | {:<30} | {:<20} | {:>8} |".format(idx, w.name, w.post, w.year))

    print(line)


def main(command_line=None):
    BASE_DIR = Path(__file__).resolve().parent.parent
    DB_PATH = BASE_DIR / "workers.db"

    parser = argparse.ArgumentParser("workers")

    parser.add_argument("--db", default=str(DB_PATH), help="Файл базы данных")

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command")

    add = subparsers.add_parser("add", help="Добавить работника")
    add.add_argument("-n", "--name", required=True)
    add.add_argument("-p", "--post", required=True)
    add.add_argument("-y", "--year", required=True, type=int)

    subparsers.add_parser("display", help="Показать всех работников")

    select = subparsers.add_parser("select", help="Выборка по стажу")
    select.add_argument("-p", "--period", required=True, type=int)

    args = parser.parse_args(command_line)

    repo = StaffRepository(Path(args.db))

    if args.command == "add":
        repo.add_worker(args.name, args.post, args.year)
        print(f"Работник {args.name} успешно добавлен.")

    elif args.command == "display":
        display_workers(repo.get_all_workers())

    elif args.command == "select":
        display_workers(repo.select_by_period(args.period))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()