#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, DateTime, ForeignKey, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

Base = declarative_base()


class Airport(Base):
    __tablename__ = "airports"

    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)

    departing_flights = relationship(
        "Flight",
        foreign_keys="Flight.departure_airport_code",
        back_populates="departure_airport",
    )
    arriving_flights = relationship(
        "Flight",
        foreign_keys="Flight.arrival_airport_code",
        back_populates="arrival_airport",
    )


class Flight(Base):
    __tablename__ = "flights"

    number = Column(String, primary_key=True)
    departure_airport_code = Column(String, ForeignKey("airports.code"), nullable=False)
    arrival_airport_code = Column(String, ForeignKey("airports.code"), nullable=False)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)

    departure_airport = relationship(
        "Airport",
        foreign_keys=[departure_airport_code],
        back_populates="departing_flights",
    )
    arrival_airport = relationship(
        "Airport",
        foreign_keys=[arrival_airport_code],
        back_populates="arriving_flights",
    )


class FlightRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_session(self) -> Session:
        return self.Session()

    def add_airport(self, code: str, name: str, city: str) -> None:
        with self._get_session() as session:
            airport = Airport(code=code, name=name, city=city)
            session.add(airport)
            session.commit()

    def add_flight(
        self,
        number: str,
        departure_airport_code: str,
        arrival_airport_code: str,
        departure_time_str: str,
        arrival_time_str: str,
    ) -> None:
        with self._get_session() as session:
            departure_time = datetime.strptime(departure_time_str, "%Y-%m-%d %H:%M")
            arrival_time = datetime.strptime(arrival_time_str, "%Y-%m-%d %H:%M")

            flight = Flight(
                number=number,
                departure_airport_code=departure_airport_code,
                arrival_airport_code=arrival_airport_code,
                departure_time=departure_time,
                arrival_time=arrival_time,
            )
            session.add(flight)
            session.commit()

    def get_all_flights(self):
        with self._get_session() as session:
            flights = session.query(Flight).all()
            return flights

    def get_flights_by_destination(self, airport_code: str):
        with self._get_session() as session:
            flights = (
                session.query(Flight)
                .filter(Flight.arrival_airport_code == airport_code)
                .all()
            )
            return flights

    def get_all_airports(self):
        with self._get_session() as session:
            airports = session.query(Airport).all()
            return airports


def display_flights(flights: list[Flight]) -> None:
    if not flights:
        print("Список рейсов пуст.")
        return

    line = "+{}+{}+{}+{}+{}+".format("-" * 10, "-" * 20, "-" * 20, "-" * 16, "-" * 16)

    print(line)
    print(
        "|{:^10}|{:^20}|{:^20}|{:^16}|{:^16}|".format(
            "Номер",
            "Аэропорт вылета",
            "Аэропорт прибытия",
            "Время вылета",
            "Время прибытия",
        )
    )
    print(line)

    for flight in flights:
        departure_time = flight.departure_time.strftime("%Y-%m-%d %H:%M")
        arrival_time = flight.arrival_time.strftime("%Y-%m-%d %H:%M")

        print(
            "|{:<10}|{:<20}|{:<20}|{:<16}|{:<16}|".format(
                flight.number,
                flight.departure_airport_code,
                flight.arrival_airport_code,
                departure_time,
                arrival_time,
            )
        )

    print(line)


def display_airports(airports: list[Airport]) -> None:
    if not airports:
        print("Список аэропортов пуст.")
        return

    line = "+{}+{}+{}+".format("-" * 6, "-" * 30, "-" * 20)

    print(line)
    print("|{:^6}|{:^30}|{:^20}|".format("Код", "Название", "Город"))
    print(line)

    for airport in airports:
        print("|{:<6}|{:<30}|{:<20}|".format(airport.code, airport.name, airport.city))

    print(line)


def main():
    parser = argparse.ArgumentParser(
        description="Управление авиарейсами (SQLAlchemy)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--db",
        default="airports_sa.db",
        help="Путь к файлу базы данных (по умолчанию: airports_sa.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Команды")

    airport_parser = subparsers.add_parser(
        "add-airport", help="Добавить новый аэропорт"
    )
    airport_parser.add_argument("--code", required=True, help="Код аэропорта")
    airport_parser.add_argument("--name", required=True, help="Название аэропорта")
    airport_parser.add_argument("--city", required=True, help="Город")

    flight_parser = subparsers.add_parser("add-flight", help="Добавить новый рейс")
    flight_parser.add_argument("--number", required=True, help="Номер рейса")
    flight_parser.add_argument(
        "--departure", required=True, help="Код аэропорта вылета"
    )
    flight_parser.add_argument(
        "--arrival", required=True, help="Код аэропорта прибытия"
    )
    flight_parser.add_argument(
        "--departure-time",
        required=True,
        help="Время вылета (Формат: ГГГГ-ММ-ДД ЧЧ:ММ)",
    )
    flight_parser.add_argument(
        "--arrival-time",
        required=True,
        help="Время прибытия (Формат: ГГГГ-ММ-ДД ЧЧ:ММ)",
    )

    subparsers.add_parser("show-flights", help="Показать все рейсы")

    subparsers.add_parser("show-airports", help="Показать все аэропорты")

    select_parser = subparsers.add_parser(
        "select-by-destination", help="Выборка рейсов по аэропорту назначения"
    )
    select_parser.add_argument(
        "--airport", required=True, help="Код аэропорта назначения"
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
            args.arrival_time,
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
