"""GitHub contribution data for the live panels: the calendar of the last 12 months and what can be read from it."""
import calendar
import json
import os
import urllib.request
from collections import Counter

USER = "jlceaser"
QUERY = """{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions
  weeks{contributionDays{date weekday contributionCount contributionLevel}}}}}}"""
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch():
    """Calendar weeks of the last 12 months, oldest first; each day has date, weekday, count and level 0-4."""
    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": QUERY % USER}).encode(),
                                 {"Authorization": f"bearer {token}"})
    with urllib.request.urlopen(req) as r:
        weeks = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[dict(date=d["date"], weekday=d["weekday"], count=d["contributionCount"], level=LEVELS[d["contributionLevel"]])
             for d in w["contributionDays"]] for w in weeks]


def streaks(counts):
    """Current and best run of days with contributions; today may still be empty without breaking the run."""
    best = run = 0
    for n in counts:
        run = run + 1 if n else 0
        best = max(best, run)
    i, cur = len(counts) - 1, 0
    if counts and not counts[i]:
        i -= 1
    while i >= 0 and counts[i]:
        cur, i = cur + 1, i - 1
    return cur, best


def facts(weeks):
    days = [d for w in weeks for d in w]
    counts = [d["count"] for d in days]
    cur, best = streaks(counts)
    by_month = Counter()
    for d in days:
        by_month[d["date"][:7]] += d["count"]
    month, month_n = by_month.most_common(1)[0]
    top = max(days, key=lambda d: d["count"])
    return dict(total=sum(counts), active=sum(1 for n in counts if n), streak=cur, best=best,
                month=calendar.month_name[int(month[5:])], month_n=month_n, top_day=top["date"], top_n=top["count"])
