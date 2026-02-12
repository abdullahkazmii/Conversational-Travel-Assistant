import json
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from dateutil import parser as date_parser  # type: ignore[import-untyped]

from src.models.schemas import Flight, FlightCriteria
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FlightSearchTool:
    def __init__(self, flights_path: str = "data/flights.json") -> None:
        self.flights_path = Path(flights_path)
        self.flights: List[Flight] = []
        self._load_flights()

    def _load_flights(self) -> None:
        try:
            with open(self.flights_path, encoding="utf-8") as f:
                data = json.load(f)
            for row in data:
                if "overnight_layover" not in row and row.get("layovers"):
                    row["overnight_layover"] = len(row["layovers"]) > 1
            self.flights = [Flight(**row) for row in data]
            logger.info("Loaded %d flights from %s", len(self.flights), self.flights_path)
        except Exception as e:
            logger.error("Error loading flights: %s", e)
            raise

    def _parse_date_or_range(self, value: Optional[str]) -> Optional[Tuple[date, date]]:
        if not value or not isinstance(value, str):
            return None
        value = value.strip()
        if value.lower() in ("flexible", "null", ""):
            return None
        if " to " in value:
            parts = value.split(" to ", 1)
            try:
                start = date_parser.parse(parts[0].strip()).date()
                end = date_parser.parse(parts[1].strip()).date()
                return (start, end)
            except (ValueError, TypeError):
                return None
        try:
            d = date_parser.parse(value).date()
            return (d, d)
        except (ValueError, TypeError):
            return None

    def _filter_departure_dates(
        self, flights: List[Flight], criteria_value: Optional[str]
    ) -> List[Flight]:
        parsed = self._parse_date_or_range(criteria_value)
        if not parsed:
            return flights
        start, end = parsed
        result = []
        for f in flights:
            try:
                d = date_parser.parse(f.departure_date).date()
                if start <= d <= end:
                    result.append(f)
            except (ValueError, TypeError):
                continue
        return result

    def _filter_return_dates(
        self, flights: List[Flight], criteria_value: Optional[str]
    ) -> List[Flight]:
        parsed = self._parse_date_or_range(criteria_value)
        if not parsed:
            return flights
        start, end = parsed
        result = []
        for f in flights:
            if not f.return_date:
                continue
            try:
                d = date_parser.parse(f.return_date).date()
                if start <= d <= end:
                    result.append(f)
            except (ValueError, TypeError):
                continue
        return result

    def search(self, criteria: FlightCriteria) -> List[Flight]:
        if not criteria.destination or not criteria.destination.strip():
            return []

        results: List[Flight] = list(self.flights)

        results = self._filter_destination(results, criteria.destination)

        if criteria.departure_date and criteria.departure_date.strip().lower() not in (
            "flexible",
            "null",
        ):
            results = self._filter_departure_dates(results, criteria.departure_date)
        if criteria.return_date and criteria.return_date.strip().lower() not in (
            "flexible",
            "null",
        ):
            results = self._filter_return_dates(results, criteria.return_date)

        if criteria.origin:
            results = self._filter_origin(results, criteria.origin)
        if criteria.alliance:
            results = self._filter_alliance(results, criteria.alliance.value)
        if criteria.preferred_airlines:
            results = self._filter_airlines(results, criteria.preferred_airlines)
        if criteria.avoid_overnight_layover:
            results = self._filter_overnight(results)
        if criteria.max_layovers is not None:
            results = self._filter_max_layovers(results, criteria.max_layovers)
        if criteria.max_price_usd is not None:
            results = self._filter_price(results, criteria.max_price_usd)
        if criteria.refundable_only:
            results = self._filter_refundable(results)

        results = self._rank_flights(results, criteria)
        logger.info("Found %d flights matching criteria", len(results))
        return results

    def _filter_destination(self, flights: List[Flight], destination: str) -> List[Flight]:
        dest = destination.strip().lower()
        return [f for f in flights if f.destination.lower() == dest]

    def _filter_origin(self, flights: List[Flight], origin: str) -> List[Flight]:
        o = origin.strip().lower()
        return [f for f in flights if f.origin.lower() == o]

    def _filter_alliance(self, flights: List[Flight], alliance: str) -> List[Flight]:
        return [f for f in flights if f.alliance and f.alliance == alliance]

    def _filter_airlines(
        self, flights: List[Flight], airlines: List[str]
    ) -> List[Flight]:
        airlines_lower = [a.lower() for a in airlines]
        return [f for f in flights if f.airline.lower() in airlines_lower]

    def _filter_overnight(self, flights: List[Flight]) -> List[Flight]:
        return [f for f in flights if not f.overnight_layover]

    def _filter_max_layovers(
        self, flights: List[Flight], max_layovers: int
    ) -> List[Flight]:
        return [f for f in flights if len(f.layovers) <= max_layovers]

    def _filter_price(self, flights: List[Flight], max_price: float) -> List[Flight]:
        return [f for f in flights if f.price_usd <= max_price]

    def _filter_refundable(self, flights: List[Flight]) -> List[Flight]:
        return [f for f in flights if f.refundable]

    def _rank_flights(
        self, flights: List[Flight], criteria: FlightCriteria
    ) -> List[Flight]:
        if not flights:
            return []
        max_price = max(f.price_usd for f in flights)
        for flight in flights:
            score = 0.0
            layover_count = len(flight.layovers)
            score += (3 - min(layover_count, 3)) * 10
            if layover_count == 0:
                score += 15
            price_score = ((max_price - flight.price_usd) / max_price) * 20
            score += max(0, price_score)
            if flight.refundable:
                score += 5
            if criteria.alliance and flight.alliance == criteria.alliance.value:
                score += 8
            flight.match_score = round(score, 2)
        return sorted(flights, key=lambda x: x.match_score, reverse=True)


flight_search_tool = FlightSearchTool()
