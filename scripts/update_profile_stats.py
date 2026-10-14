#!/usr/bin/env python3
"""Refresh the profile README's public GitHub statistics card."""

from datetime import datetime, timezone
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


def render(stats: dict[str, int]) -> str:
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="280" viewBox="0 0 1000 280" role="img" aria-labelledby="title desc">
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
  <rect width="1000" height="280" rx="24" fill="url(#bg)"/>
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
</svg>
"""


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(collect_stats()), encoding="utf-8")


if __name__ == "__main__":
    main()
