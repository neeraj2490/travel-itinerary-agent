from __future__ import annotations

import json
import sys
from pathlib import Path

import groq
from dotenv import dotenv_values
from groq import APIConnectionError, APIError, RateLimitError
from pydantic import ValidationError

from schemas import TravelItinerary

MODEL = "openai/gpt-oss-20b"
ENV_PATH = Path(__file__).resolve().parent / ".env"


def _load_api_key_from_env_file() -> str | None:
    if not ENV_PATH.is_file():
        return None
    return dotenv_values(ENV_PATH).get("GROQ_API_KEY")


def split_trip_days(total_days: int, num_destinations: int) -> list[int]:
    """Split total trip days across destinations, giving extra days to earlier cities."""
    base, remainder = divmod(total_days, num_destinations)
    return [base + (1 if i < remainder else 0) for i in range(num_destinations)]


def _destination_schema(destination_days: int) -> dict:
    schema = TravelItinerary.model_json_schema()
    schema["properties"]["trip_duration_days"] = {
        "type": "integer",
        "const": destination_days,
        "description": "Days spent in this destination only",
    }
    schema["properties"]["daily_plan"]["minItems"] = destination_days
    schema["properties"]["daily_plan"]["maxItems"] = destination_days
    return schema


def _parse_itinerary(
    content: str, destination: str, destination_days: int
) -> TravelItinerary:
    data = json.loads(content)
    data["trip_duration_days"] = destination_days

    daily_plan = data.get("daily_plan")
    if isinstance(daily_plan, list) and len(daily_plan) == destination_days:
        for i, plan in enumerate(daily_plan):
            if isinstance(plan, dict):
                plan["day"] = i + 1

    return TravelItinerary.model_validate(data)


class TravelItineraryAgent:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or _load_api_key_from_env_file()
        if not key:
            print(
                "Error: GROQ_API_KEY is not set in .env. "
                "Copy .env.example to .env and add your key.",
                file=sys.stderr,
            )
            sys.exit(1)
        self.client = groq.Groq(api_key=key)

    def _build_messages(
        self,
        source_city: str,
        destination: str,
        destination_days: int,
        budget_category: str,
        total_trip_days: int,
        all_destinations: list[str],
    ) -> list[dict[str, str]]:
        if len(all_destinations) == 1:
            trip_context = (
                f"Plan a {total_trip_days}-day trip from {source_city} to {destination}."
            )
        else:
            route = " -> ".join(all_destinations)
            trip_context = (
                f"Plan the {destination} leg of a {total_trip_days}-day multi-city trip "
                f"from {source_city} visiting {route}. "
                f"Allocate exactly {destination_days} days to {destination}."
            )

        system_msg = {
            "role": "system",
            "content": (
                "You are an expert travel planner. Return JSON matching the provided schema. "
                f"trip_duration_days must be {destination_days} — the number of days in "
                f"{destination} only, not the full multi-city trip. "
                f"The daily_plan array must contain exactly {destination_days} entries, "
                f"numbered 1 through {destination_days}. "
                f"Activities should be realistic for a {budget_category} budget."
            ),
        }
        user_msg = {
            "role": "user",
            "content": (
                f"{trip_context}\n"
                f"Destination: {destination}\n"
                f"Days in this city: {destination_days}\n"
                f"Budget: {budget_category}\n"
                "Include top attractions and a day-by-day activity plan for this city only."
            ),
        }
        return [system_msg, user_msg]

    def generate_itinerary(
        self,
        source_city: str,
        destination: str,
        destination_days: int,
        budget_category: str,
        total_trip_days: int,
        all_destinations: list[str],
    ) -> TravelItinerary:
        messages = self._build_messages(
            source_city,
            destination,
            destination_days,
            budget_category,
            total_trip_days,
            all_destinations,
        )

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "travel_itinerary",
                        "schema": _destination_schema(destination_days),
                    },
                },
            )
        except RateLimitError as exc:
            print(f"Rate limit error for {destination}: {exc}", file=sys.stderr)
            sys.exit(1)
        except APIConnectionError as exc:
            print(f"Connection error for {destination}: {exc}", file=sys.stderr)
            sys.exit(1)
        except APIError as exc:
            print(f"API error for {destination}: {exc}", file=sys.stderr)
            sys.exit(1)

        content = response.choices[0].message.content
        if not content:
            raise ValueError(
                f"Empty response from {MODEL} for destination '{destination}'"
            )

        try:
            return _parse_itinerary(content, destination, destination_days)
        except json.JSONDecodeError as exc:
            snippet = content[:200]
            raise ValueError(
                f"Invalid JSON from {MODEL} for '{destination}': {exc}. "
                f"Raw snippet: {snippet!r}"
            ) from exc
        except ValidationError as exc:
            print(
                f"Validation failed for '{destination}':\n{exc}",
                file=sys.stderr,
            )
            sys.exit(1)

    def generate_all(
        self,
        source_city: str,
        destinations: list[str],
        trip_duration_days: int,
        budget_category: str,
    ) -> list[TravelItinerary]:
        if trip_duration_days < len(destinations):
            print(
                "Error: --days must be at least the number of destinations "
                f"({len(destinations)}), got {trip_duration_days}.",
                file=sys.stderr,
            )
            sys.exit(1)

        day_allocations = split_trip_days(trip_duration_days, len(destinations))
        return [
            self.generate_itinerary(
                source_city,
                dest,
                days,
                budget_category,
                trip_duration_days,
                destinations,
            )
            for dest, days in zip(destinations, day_allocations)
        ]
