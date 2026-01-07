from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, Iterable, Optional, Tuple

def iso_date(d: date) -> str:
    return d.isoformat()

def week_start(d: date) -> date:
    # Monday-start week
    return d.fromordinal(d.toordinal() - (d.weekday()))

def month_start(d: date) -> date:
    return date(d.year, d.month, 1)

def year_start(d: date) -> date:
    return date(d.year, 1, 1)

@dataclass
class Agg:
    run_count: int = 0
    total_meters: float = 0.0
    total_seconds: float = 0.0
    elev_gain: float = 0.0
    hr_time_sum: float = 0.0
    hr_weight_sum: float = 0.0

    def add(self, meters: float, seconds: float, elev: float, avg_hr: Optional[float]):
        self.run_count += 1
        self.total_meters += meters
        self.total_seconds += seconds
        self.elev_gain += elev
        if avg_hr is not None and seconds > 0:
            self.hr_time_sum += avg_hr * seconds
            self.hr_weight_sum += seconds

    def avg_hr_time_weighted(self) -> Optional[float]:
        if self.hr_weight_sum <= 0:
            return None
        return self.hr_time_sum / self.hr_weight_sum

def parse_activity_date(act: Dict[str, Any]) -> date:
    dt = datetime.fromisoformat(act["start_date"].replace("Z", "+00:00"))
    return dt.date()

def is_run(act: Dict[str, Any]) -> bool:
    t = (act.get("sport_type") or act.get("type") or "").lower()
    return "run" == t

def build_period_aggregates(activities: Iterable[Dict[str, Any]]) -> Tuple[dict, dict, dict]:
    weekly: Dict[str, Agg] = {}
    monthly: Dict[str, Agg] = {}
    yearly: Dict[str, Agg] = {}

    for act in activities:
        if not is_run(act):
            continue

        d = parse_activity_date(act)

        w = iso_date(week_start(d))
        m = iso_date(month_start(d))
        y = iso_date(year_start(d))

        meters = float(act.get("distance") or 0.0)
        seconds = float(act.get("moving_time") or 0.0)
        elev = float(act.get("total_elevation_gain") or 0.0)
        avg_hr = act.get("average_heartrate")
        avg_hr = float(avg_hr) if avg_hr is not None else None

        weekly.setdefault(w, Agg()).add(meters, seconds, elev, avg_hr)
        monthly.setdefault(m, Agg()).add(meters, seconds, elev, avg_hr)
        yearly.setdefault(y, Agg()).add(meters, seconds, elev, avg_hr)

    return weekly, monthly, yearly
