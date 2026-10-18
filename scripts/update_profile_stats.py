#!/usr/bin/env python3
"""Refresh the profile README's public GitHub statistics card."""

from datetime import datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = "zhuhaoran666"
OUTPUT = Path("assets/profile-header.svg")


def github_json(url: str) -> object:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-stats-updater",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_stats() -> dict[str, int]:
    user = github_json(f"https://api.github.com/users/{OWNER}")
    repos = []
    page = 1
    while True:
        batch = github_json(
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&sort=updated&per_page=100&page={page}"
        )
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return {
        "stars": sum(repo["stargazers_count"] for repo in repos),
        "repositories": user["public_repos"],
        "followers": user["followers"],
        "forks": sum(repo["forks_count"] for repo in repos),
    }


def collect_contributions() -> dict[str, object]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { contributionCount date weekday }
            }
          }
        }
      }
    }
    """
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({
            "query": query,
            "variables": {
                "login": OWNER,
                "from": start.isoformat().replace("+00:00", "Z"),
                "to": end.isoformat().replace("+00:00", "Z"),
            },
        }).encode(),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-stats-updater",
            "Content-Type": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {result['errors']}")
    collection = result["data"]["user"]["contributionsCollection"]
    calendar = collection["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    return {
        "total": calendar["totalContributions"],
        "commits": collection["totalCommitContributions"],
        "pull_requests": collection["totalPullRequestContributions"],
        "issues": collection["totalIssueContributions"],
        "reviews": collection["totalPullRequestReviewContributions"],
        "days": days,
        "updated": end.strftime("%Y-%m-%d %H:%M UTC"),
    }


def render_contributions(data: dict[str, object]) -> str:
    days = data["days"]
    max_count = max((day["contributionCount"] for day in days), default=0)
    palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    rects = []
    for index, day in enumerate(days):
        x = 30 + (index // 7) * 12
        y = 66 + day["weekday"] * 12
        count = day["contributionCount"]
        level = 0 if count == 0 else min(4, max(1, (count * 4 + max_count - 1) // max_count))
        rects.append(
            f'<rect x="{x}" y="{y}" width="9" height="9" rx="2" '
            f'fill="{palette[level]}"><title>{escape(day["date"])}: {count} contributions</title></rect>'
        )

    categories = [
        ("COMMITS", data["commits"], "#58a6ff"),
        ("PULL REQUESTS", data["pull_requests"], "#63e6be"),
        ("ISSUES", data["issues"], "#f2cc60"),
        ("CODE REVIEWS", data["reviews"], "#d2a8ff"),
    ]
    total = max(sum(item[1] for item in categories), 1)
    rows = []
    for index, (label, count, color) in enumerate(categories):
        y = 80 + index * 39
        width = round(170 * count / total)
        rows.append(
            f'<text x="695" y="{y}" fill="#c9d1d9" font-size="12">{label}</text>'
            f'<text x="950" y="{y}" fill="#ffffff" font-size="13" text-anchor="end" font-weight="700">{count:,}</text>'
            f'<rect x="695" y="{y + 9}" width="170" height="5" rx="2.5" fill="#30363d"/>'
            f'<rect x="695" y="{y + 9}" width="{width}" height="5" rx="2.5" fill="{color}"/>'
        )
    weeks = (len(days) + 6) // 7
    month_labels = []
    seen_months = set()
    for index, day in enumerate(days):
        month = day["date"][:7]
        if month not in seen_months:
            month_labels.append(
                f'<text x="{30 + (index // 7) * 12}" y="54" fill="#8b949e" font-size="10">'
                f'{escape(datetime.strptime(day["date"], "%Y-%m-%d").strftime("%b"))}</text>'
            )
            seen_months.add(month)
    return f"""<svg x="0" y="280" width="1000" height="190" viewBox="0 0 1000 190" aria-labelledby="contribution-title contribution-desc">
  <title id="contribution-title">GitHub contributions in the last year</title>
  <desc id="contribution-desc">{data['total']} public contributions in the last year with a daily contribution graph and activity breakdown.</desc>
  <rect width="1000" height="190" rx="18" fill="#0d1117" stroke="#30363d"/>
  <text x="30" y="34" fill="#f0f6fc" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="16" font-weight="700">{data['total']:,} contributions in the last year</text>
  {''.join(month_labels)}
  {''.join(rects)}
  <text x="30" y="169" fill="#8b949e" font-size="10">Less</text>
  {''.join(f'<rect x="{63 + i * 14}" y="160" width="9" height="9" rx="2" fill="{palette[i]}"/>' for i in range(5))}
  <text x="141" y="169" fill="#8b949e" font-size="10">More</text>
  <line x1="665" y1="24" x2="665" y2="166" stroke="#30363d"/>
  <text x="695" y="42" fill="#8b949e" font-size="10" font-weight="700" letter-spacing="1">ACTIVITY OVERVIEW</text>
  {''.join(rows)}
  <text x="695" y="173" fill="#6e7681" font-size="9">PUBLIC CONTRIBUTIONS · UPDATED {escape(data['updated'])}</text>
</svg>
"""


def render(stats: dict[str, int], contributions: dict[str, object]) -> str:
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="480" viewBox="0 0 1000 480" role="img" aria-labelledby="title desc">
  <title id="title">Zhu Haoran — live GitHub statistics</title>
  <desc id="desc">Total stars {stats['stars']}, public repositories {stats['repositories']}, followers {stats['followers']}, and forks {stats['forks']}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07152d"/>
      <stop offset=".58" stop-color="#0b3266"/>
      <stop offset="1" stop-color="#0b7285"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#58a6ff"/>
      <stop offset="1" stop-color="#63e6be"/>
    </linearGradient>
  </defs>
  <rect width="1000" height="480" rx="24" fill="url(#bg)"/>
  <circle cx="940" cy="30" r="150" fill="#20c997" opacity=".08"/>
  <text x="54" y="48" fill="#b9d9ff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="14" font-weight="700" letter-spacing="2">ZHU HAORAN · OPEN-SOURCE SNAPSHOT</text>
  <rect x="806" y="27" width="142" height="28" rx="14" fill="#ffffff" opacity=".1"/>
  <circle cx="824" cy="41" r="4" fill="#63e6be"/>
  <text x="836" y="46" fill="#d7e8f8" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11" font-weight="600" letter-spacing=".6">REFRESHES HOURLY</text>

  <rect x="48" y="72" width="380" height="154" rx="18" fill="#ffffff" opacity=".1" stroke="#8ecbff" stroke-opacity=".28"/>
  <rect x="48" y="72" width="6" height="154" rx="3" fill="url(#accent)"/>
  <text x="78" y="107" fill="#b9d9ff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="13" font-weight="700" letter-spacing="1.7">TOTAL STARS</text>
  <path d="M372 91l5.4 11 12.1 1.8-8.8 8.6 2.1 12.1-10.8-5.7-10.8 5.7 2.1-12.1-8.8-8.6 12.1-1.8z" fill="#63e6be"/>
  <text x="77" y="174" fill="#ffffff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="55" font-weight="750">{stats['stars']:,}</text>
  <text x="80" y="203" fill="#d7e8f8" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="14">across public repositories</text>

  <g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
    <rect x="448" y="72" width="155" height="154" rx="18" fill="#ffffff" opacity=".09" stroke="#8ecbff" stroke-opacity=".18"/>
    <text x="468" y="107" fill="#b9d9ff" font-size="12" font-weight="700" letter-spacing=".7">PUBLIC REPOS</text>
    <text x="468" y="164" fill="#ffffff" font-size="36" font-weight="700">{stats['repositories']:,}</text>
    <path d="M469 191h112" stroke="url(#accent)" stroke-width="3" stroke-linecap="round" opacity=".8"/>

    <rect x="623" y="72" width="155" height="154" rx="18" fill="#ffffff" opacity=".09" stroke="#8ecbff" stroke-opacity=".18"/>
    <text x="643" y="107" fill="#b9d9ff" font-size="12" font-weight="700" letter-spacing=".7">FOLLOWERS</text>
    <text x="643" y="164" fill="#ffffff" font-size="36" font-weight="700">{stats['followers']:,}</text>
    <path d="M644 191h112" stroke="url(#accent)" stroke-width="3" stroke-linecap="round" opacity=".8"/>

    <rect x="798" y="72" width="155" height="154" rx="18" fill="#ffffff" opacity=".09" stroke="#8ecbff" stroke-opacity=".18"/>
    <text x="818" y="107" fill="#b9d9ff" font-size="12" font-weight="700" letter-spacing=".7">TOTAL FORKS</text>
    <text x="818" y="164" fill="#ffffff" font-size="36" font-weight="700">{stats['forks']:,}</text>
    <path d="M819 191h112" stroke="url(#accent)" stroke-width="3" stroke-linecap="round" opacity=".8"/>
  </g>
  <text x="54" y="255" fill="#a9c7e8" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11">PUBLIC ACTIVITY · LAST UPDATED {escape(updated)}</text>
  {render_contributions(contributions)}
</svg>
"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        render(collect_stats(), collect_contributions()), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
