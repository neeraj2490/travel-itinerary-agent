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
        trip_duration_days: int,
        budget_category: str,
    ) -> list[dict[str, str]]:
        system_msg = {
            "role": "system",
            "content": (
                "You are an expert travel planner. Return JSON matching the provided schema. "
                f"The daily_plan array must contain exactly {trip_duration_days} entries, "
                f"one per day numbered 1 through {trip_duration_days}. "
                f"Activities should be realistic for a {budget_category} budget."
            ),
        }
        user_msg = {
            "role": "user",
            "content": (
                f"Plan a {trip_duration_days}-day trip from {source_city} to {destination}.\n"
                f"Destination: {destination}\n"
                f"Duration: {trip_duration_days} days\n"
                f"Budget: {budget_category}\n"
                "Include top attractions and a day-by-day activity plan."
            ),
        }
        return [system_msg, user_msg]

    def generate_itinerary(
        self,
        source_city: str,
        destination: str,
        trip_duration_days: int,
        budget_category: str,
    ) -> TravelItinerary:
        messages = self._build_messages(
            source_city, destination, trip_duration_days, budget_category
        )

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "travel_itinerary",
                        "schema": TravelItinerary.model_json_schema(),
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
            return TravelItinerary.model_validate_json(content)
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
        return [
            self.generate_itinerary(
                source_city, dest, trip_duration_days, budget_category
            )
            for dest in destinations
        ]
