#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Airport:
    code: str
    name: str
    city: str


@dataclass
class Flight:
    number: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str


class FlightRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._create_tables()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS airports (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                city TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS flights (
                number TEXT PRIMARY KEY,
                departure_airport TEXT NOT NULL,
                arrival_airport TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                FOREIGN KEY(departure_airport) REFERENCES airports(code),
                FOREIGN KEY(arrival_airport) REFERENCES airports(code)
            )
            """
        )

        conn.commit()
        conn.close()

    def add_airport(self, code: str, name: str, city: str) -> None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO airports (code, name, city)
            VALUES (?, ?, ?)
            """,
            (code, name, city)
        )

        conn.commit()
        conn.close()

    def add_flight(self, number: str, departure_airport: str,
                   arrival_airport: str, departure_time: str,
                   arrival_time: str) -> None:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO flights (
                number, departure_airport, arrival_airport,
                departure_time, arrival_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (number, departure_airport, arrival_airport,
             departure_time, arrival_time)
        )

        conn.commit()
        conn.close()

    def get_all_flights(self) -> list[Flight]:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                f.number,
                f.departure_airport,
                f.arrival_airport,
                f.departure_time,
                f.arrival_time
            FROM flights f
            """
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            Flight(
                number=row[0],
                departure_airport=row[1],
                arrival_airport=row[2],
                departure_time=row[3],
                arrival_time=row[4]
            )
            for row in rows
        ]

    def get_flights_by_destination(self, airport_code: str) -> list[Flight]:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                f.number,
                f.departure_airport,
                f.arrival_airport,
                f.departure_time,
                f.arrival_time
            FROM flights f
            WHERE f.arrival_airport = ?
            """,
            (airport_code,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            Flight(
                number=row[0],
                departure_airport=row[1],
                arrival_airport=row[2],
                departure_time=row[3],
                arrival_time=row[4]
            )
            for row in rows
        ]

    def get_all_airports(self) -> list[Airport]:
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT code, name, city
            FROM airports
            """
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            Airport(code=row[0], name=row[1], city=row[2])
            for row in rows
        ]


def display_flights(flights: list[Flight]) -> None:
    if not flights:
        print("Список рейсов пуст.")
        return

    line = "+{}+{}+{}+{}+{}+".format(
        "-" * 10, "-" * 20, "-" * 20, "-" * 16, "-" * 16
    )

    print(line)
    print("|{:^10}|{:^20}|{:^20}|{:^16}|{:^16}|".format(
        "Номер", "Аэропорт вылета", "Аэропорт прибытия",
        "Время вылета", "Время прибытия"
    ))
    print(line)

    for flight in flights:
        print("|{:<10}|{:<20}|{:<20}|{:<16}|{:<16}|".format(
            flight.number, flight.departure_airport,
            flight.arrival_airport, flight.departure_time,
            flight.arrival_time
        ))

    print(line)


def display_airports(airports: list[Airport]) -> None:
    if not airports:
        print("Список аэропортов пуст.")
        return

    line = "+{}+{}+{}+".format("-" * 6, "-" * 30, "-" * 20)

    print(line)
    print("|{:^6}|{:^30}|{:^20}|".format(
        "Код", "Название", "Город"
    ))
    print(line)

    for airport in airports:
        print("|{:<6}|{:<30}|{:<20}|".format(
            airport.code, airport.name, airport.city
        ))

    print(line)


def main():
    parser = argparse.ArgumentParser(
        description="Управление авиарейсами",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--db",
        default="airports.db",
        help="Путь к файлу базы данных (по умолчанию: airports.db)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # Команда добавления аэропорта
    airport_parser = subparsers.add_parser(
        "add-airport",
        help="Добавить новый аэропорт"
    )
    airport_parser.add_argument("--code", required=True, help="Код аэропорта")
    airport_parser.add_argument("--name", required=True, help="Название аэропорта")
    airport_parser.add_argument("--city", required=True, help="Город")

    # Команда добавления рейса
    flight_parser = subparsers.add_parser(
        "add-flight",
        help="Добавить новый рейс"
    )
    flight_parser.add_argument("--number", required=True, help="Номер рейса")
    flight_parser.add_argument(
        "--departure",
        required=True,
        help="Код аэропорта вылета"
    )
    flight_parser.add_argument(
        "--arrival",
        required=True,
        help="Код аэропорта прибытия"
    )
    flight_parser.add_argument(
        "--departure-time",
        required=True,
        help="Время вылета (Формат: ГГГГ-ММ-ДД ЧЧ:ММ)"
    )
    flight_parser.add_argument(
        "--arrival-time",
        required=True,
        help="Время прибытия (Формат: ГГГГ-ММ-ДД ЧЧ:ММ)"
    )

    # Команда отображения всех рейсов.
    subparsers.add_parser(
        "show-flights",
        help="Показать все рейсы"
    )

    # Команда отображения всех аэропортов
    subparsers.add_parser(
        "show-airports",
        help="Показать все аэропорты"
    )

    # Команда выборки рейсов по аэропорту назначения
    select_parser = subparsers.add_parser(
        "select-by-destination",
        help="Выборка рейсов по аэропорту назначения"
    )
    select_parser.add_argument(
        "--airport",
        required=True,
        help="Код аэропорта назначения"
    )

    args = parser.parse_args()

    repo = FlightRepository(Path(args.db))

    if args.command == "add-airport":
        repo.add_airport(args.code, args.name, args.city)
        print(f"Аэропорт {args.code} добавлен.")

    elif args.command == "add-flight":
        repo.add_flight(
            args.number,
            args.departure,
            args.arrival,
            args.departure_time,
            args.arrival_time
        )
        print(f"Рейс {args.number} добавлен.")

    elif args.command == "show-flights":
        flights = repo.get_all_flights()
        display_flights(flights)

    elif args.command == "show-airports":
        airports = repo.get_all_airports()
        display_airports(airports)

    elif args.command == "select-by-destination":
        flights = repo.get_flights_by_destination(args.airport)
        if flights:
            print(f"Рейсы с прибытием в аэропорт {args.airport}:")
            display_flights(flights)
        else:
            print(f"Рейсов с прибытием в аэропорт {args.airport} не найдено.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()