import argparse
import sys

from agent import TravelItineraryAgent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate travel itineraries using Groq structured outputs."
    )
    parser.add_argument("--source", required=True, help="Departure city")
    parser.add_argument(
        "--dest",
        action="append",
        required=True,
        dest="destinations",
        help="Destination city (repeatable)",
    )
    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="Trip duration in days (must be > 0)",
    )
    parser.add_argument(
        "--budget",
        required=True,
        choices=["budget", "moderate", "luxury"],
        help="Budget category",
    )
    args = parser.parse_args()

    if args.days <= 0:
        print("Error: --days must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    return args


def main() -> None:
    args = parse_args()
    agent = TravelItineraryAgent()
    itineraries = agent.generate_all(
        source_city=args.source,
        destinations=args.destinations,
        trip_duration_days=args.days,
        budget_category=args.budget,
    )

    for i, itinerary in enumerate(itineraries):
        if i > 0:
            print()
        print(itinerary.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
