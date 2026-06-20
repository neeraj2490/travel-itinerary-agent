from pydantic import BaseModel, model_validator


class DailyPlan(BaseModel):
    day: int
    activities: list[str]


class TravelItinerary(BaseModel):
    destination: str
    trip_duration_days: int
    budget_category: str
    top_attractions: list[str]
    daily_plan: list[DailyPlan]

    @model_validator(mode="after")
    def validate_daily_plan(self) -> "TravelItinerary":
        expected_days = self.trip_duration_days
        actual_days = len(self.daily_plan)

        if actual_days != expected_days:
            raise ValueError(
                f"daily_plan must have exactly {expected_days} entries, got {actual_days}"
            )

        day_numbers = [plan.day for plan in self.daily_plan]
        expected_range = set(range(1, expected_days + 1))
        actual_range = set(day_numbers)

        if actual_range != expected_range:
            raise ValueError(
                f"daily_plan days must be 1..{expected_days} with no duplicates, "
                f"got {sorted(day_numbers)}"
            )

        return self
