#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from tasks.task2 import (
    Airport,
    Flight,
    FlightRepository,
    display_airports,
    display_flights,
)


class TestFlightRepositorySQLAlchemy:
    @pytest.fixture
    def temp_db_path(self):
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield Path(db_path)
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except (OSError, PermissionError):
            pass

    @pytest.fixture
    def repo(self, temp_db_path):
        return FlightRepository(temp_db_path)

    def test_create_tables(self, repo):
        repo.add_airport("TEST", "Тестовый аэропорт", "Тестовый город")
        airports = repo.get_all_airports()
        assert len(airports) == 1
        assert airports[0].code == "TEST"

    def test_add_airport(self, repo):
        repo.add_airport("SVO", "Шереметьево", "Москва")
        airports = repo.get_all_airports()
        assert len(airports) == 1
        airport = airports[0]
        assert isinstance(airport, Airport)
        assert airport.code == "SVO"
        assert airport.name == "Шереметьево"
        assert airport.city == "Москва"

    def test_add_multiple_airports(self, repo):
        airports_data = [
            ("SVO", "Шереметьево", "Москва"),
            ("LED", "Пулково", "Санкт-Петербург"),
            ("DME", "Домодедово", "Москва"),
        ]
        for code, name, city in airports_data:
            repo.add_airport(code, name, city)
        airports = repo.get_all_airports()
        assert len(airports) == 3
        codes = {a.code for a in airports}
        assert codes == {"SVO", "LED", "DME"}

    def test_add_flight(self, repo):
        repo.add_airport("SVO", "Шереметьево", "Москва")
        repo.add_airport("LED", "Пулково", "Санкт-Петербург")
        repo.add_flight("SU100", "SVO", "LED", "2024-05-20 10:00", "2024-05-20 11:30")
        flights = repo.get_all_flights()
        assert len(flights) == 1
        flight = flights[0]
        assert isinstance(flight, Flight)
        assert flight.number == "SU100"
        assert flight.departure_airport_code == "SVO"
        assert flight.arrival_airport_code == "LED"
        assert isinstance(flight.departure_time, datetime)
        assert flight.departure_time.year == 2024
        assert flight.departure_time.month == 5
        assert flight.departure_time.day == 20
        assert flight.departure_time.hour == 10
        assert flight.departure_time.minute == 0
        assert isinstance(flight.arrival_time, datetime)
        assert flight.arrival_time.year == 2024
        assert flight.arrival_time.month == 5
        assert flight.arrival_time.day == 20
        assert flight.arrival_time.hour == 11
        assert flight.arrival_time.minute == 30

    def test_relationships_in_session(self, repo):
        with repo._get_session() as session:
            airport1 = Airport(code="SVO", name="Шереметьево", city="Москва")
            airport2 = Airport(code="LED", name="Пулково", city="Санкт-Петербург")
            session.add_all([airport1, airport2])
            session.commit()

            dep_time = datetime(2024, 5, 20, 10, 0)
            arr_time = datetime(2024, 5, 20, 11, 30)
            flight = Flight(
                number="SU100",
                departure_airport_code="SVO",
                arrival_airport_code="LED",
                departure_time=dep_time,
                arrival_time=arr_time,
            )
            session.add(flight)
            session.commit()

            assert flight.departure_airport is not None
            assert flight.arrival_airport is not None
            assert flight.departure_airport.code == "SVO"
            assert flight.arrival_airport.code == "LED"

    def test_get_flights_by_destination(self, repo):
        repo.add_airport("SVO", "Шереметьево", "Москва")
        repo.add_airport("LED", "Пулково", "Санкт-Петербург")
        repo.add_airport("DME", "Домодедово", "Москва")
        flights_data = [
            ("SU100", "SVO", "LED", "2024-05-20 10:00", "2024-05-20 11:30"),
            ("SU200", "LED", "DME", "2024-05-20 14:00", "2024-05-20 15:30"),
            ("SU300", "SVO", "DME", "2024-05-20 16:00", "2024-05-20 16:45"),
        ]
        for number, departure, arrival, dep_time, arr_time in flights_data:
            repo.add_flight(number, departure, arrival, dep_time, arr_time)
        moscow_flights = repo.get_flights_by_destination("DME")
        assert len(moscow_flights) == 2
        flight_numbers = {f.number for f in moscow_flights}
        assert flight_numbers == {"SU200", "SU300"}
        spb_flights = repo.get_flights_by_destination("LED")
        assert len(spb_flights) == 1
        assert spb_flights[0].number == "SU100"
        empty_flights = repo.get_flights_by_destination("XXX")
        assert len(empty_flights) == 0

    def test_empty_repository(self, repo):
        airports = repo.get_all_airports()
        flights = repo.get_all_flights()
        assert len(airports) == 0
        assert len(flights) == 0

    def test_duplicate_airport(self, repo):
        repo.add_airport("SVO", "Шереметьево", "Москва")
        try:
            repo.add_airport("SVO", "Другое название", "Другой город")
            pytest.fail("Expected exception for duplicate airport")
        except Exception:
            pass

    def test_invalid_time_format(self, repo):
        repo.add_airport("SVO", "Шереметьево", "Москва")
        repo.add_airport("LED", "Пулково", "Санкт-Петербург")
        try:
            repo.add_flight(
                "SU100", "SVO", "LED", "неправильный-формат", "2024-05-20 11:30"
            )
            pytest.fail("Expected ValueError for invalid time format")
        except ValueError:
            pass

    def test_airport_model(self):
        airport = Airport(code="TEST", name="Тест", city="Город")
        assert airport.code == "TEST"
        assert airport.name == "Тест"
        assert airport.city == "Город"

    def test_flight_model(self):
        dep_time = datetime(2024, 5, 20, 10, 0)
        arr_time = datetime(2024, 5, 20, 11, 30)
        flight = Flight(
            number="SU100",
            departure_airport_code="SVO",
            arrival_airport_code="LED",
            departure_time=dep_time,
            arrival_time=arr_time,
        )
        assert flight.number == "SU100"
        assert flight.departure_airport_code == "SVO"
        assert flight.arrival_airport_code == "LED"
        assert flight.departure_time == dep_time
        assert flight.arrival_time == arr_time


class TestDisplayFunctionsSQLAlchemy:
    def test_display_flights_empty(self, capsys):
        display_flights([])
        captured = capsys.readouterr()
        assert "Список рейсов пуст." in captured.out

    def test_display_flights_with_data(self, capsys):
        from datetime import datetime

        dep_time = datetime(2024, 5, 20, 10, 0)
        arr_time = datetime(2024, 5, 20, 11, 30)
        flights = [
            Flight(
                number="SU100",
                departure_airport_code="SVO",
                arrival_airport_code="LED",
                departure_time=dep_time,
                arrival_time=arr_time,
            )
        ]
        display_flights(flights)
        captured = capsys.readouterr()
        assert "SU100" in captured.out
        assert "SVO" in captured.out
        assert "LED" in captured.out
        assert "2024-05-20 10:00" in captured.out
        assert "2024-05-20 11:30" in captured.out

    def test_display_airports_empty(self, capsys):
        display_airports([])
        captured = capsys.readouterr()
        assert "Список аэропортов пуст." in captured.out

    def test_display_airports_with_data(self, capsys):
        airports = [Airport(code="SVO", name="Шереметьево", city="Москва")]
        display_airports(airports)
        captured = capsys.readouterr()
        assert "SVO" in captured.out
        assert "Шереметьево" in captured.out
        assert "Москва" in captured.out
