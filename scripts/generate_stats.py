#!/usr/bin/env python3
"""Generate self-hosted GitHub profile statistics SVG cards."""
import html
import json
import os
import time
import urllib.error
import urllib.request

USERNAME = "BiancaAbbamonte"
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "github-profile-stats-generator",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

BG = "#15121C"
PURPLE = "#A855F7"
RED = "#E11D48"
TEXT = "#E5E7EB"
MUTED = "#A1A1AA"
BORDER = "#30283A"
LANG_COLORS = {
    "Python": "#3572A5", "Java": "#B07219", "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6", "C#": "#178600", "C++": "#F34B7D",
    "C": "#555555", "HTML": "#E34C26", "CSS": "#563D7C",
    "Go": "#00ADD8", "Kotlin": "#A97BFF", "Shell": "#89E051",
    "Jupyter Notebook": "#DA5B0B", "Dart": "#00B4AB", "Ruby": "#701516",
    "PHP": "#4F5D95", "Rust": "#DEA584", "Swift": "#F05138",
}

def api_get(path):
    request = urllib.request.Request(API + path, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if attempt == 2 or error.code not in (403, 429, 500, 502, 503, 504):
                raise
            time.sleep(min(2 ** attempt, 8))
    raise RuntimeError("GitHub API request failed")

def esc(value):
    return html.escape(str(value), quote=True)

def svg_start(title):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="495" height="165" viewBox="0 0 495 165" role="img">',
        f'<title>{esc(title)}</title>',
        f'<rect x="0.5" y="0.5" width="494" height="164" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        '<g font-family="Segoe UI, Ubuntu, sans-serif">',
    ]

def svg_end(parts):
    parts.extend(['</g>', '</svg>'])
    return "\n".join(parts) + "\n"

def stats_svg(stats):
    p = svg_start("Bianca's GitHub statistics")
    p.append(f'<text x="25" y="32" fill="{PURPLE}" font-size="18" font-weight="600">GitHub Stats</text>')
    positions = [(25, 76), (265, 76), (25, 126), (265, 126)]
    for (label, value), (x, y) in zip(stats, positions):
        p.append(f'<text x="{x}" y="{y}" fill="{RED}" font-size="19" font-weight="600">{esc(value)}</text>')
        p.append(f'<text x="{x}" y="{y + 18}" fill="{TEXT}" font-size="11">{esc(label)}</text>')
    return svg_end(p)

def languages_svg(languages):
    p = svg_start("Most used programming languages")
    p.append(f'<text x="25" y="32" fill="{PURPLE}" font-size="18" font-weight="600">Top Languages</text>')
    if not languages:
        p.append(f'<text x="25" y="82" fill="{TEXT}" font-size="12">No public language data available yet.</text>')
        return svg_end(p)
    total = sum(size for _, size in languages)
    x = 25
    bar_y = 52
    bar_width = 445
    p.append(f'<clipPath id="barClip"><rect x="{x}" y="{bar_y}" width="{bar_width}" height="9" rx="4.5"/></clipPath>')
    p.append('<g clip-path="url(#barClip)">')
    cursor = x
    for language, size in languages:
        width = bar_width * size / total
        color = LANG_COLORS.get(language, PURPLE)
        p.append(f'<rect x="{cursor:.2f}" y="{bar_y}" width="{width + 0.5:.2f}" height="9" fill="{color}"/>')
        cursor += width
    p.append('</g>')
    for index, (language, size) in enumerate(languages[:5]):
        col = index % 2
        row = index // 2
        lx = 25 + col * 235
        ly = 85 + row * 25
        color = LANG_COLORS.get(language, PURPLE)
        percent = size / total * 100
        p.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4" fill="{color}"/>')
        p.append(f'<text x="{lx + 16}" y="{ly}" fill="{TEXT}" font-size="11">{esc(language)}</text>')
        p.append(f'<text x="{lx + 205}" y="{ly}" fill="{MUTED}" font-size="11" text-anchor="end">{percent:.1f}%</text>')
    return svg_end(p)

def main():
    user = api_get(f"/users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = api_get(f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}&sort=updated")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    forks = sum(repo.get("forks_count", 0) for repo in repos)
    stats = [
        ("Public Repositories", len(repos)),
        ("Followers", user.get("followers", 0)),
        ("Total Stars", stars),
        ("Total Forks", forks),
    ]

    language_totals = {}
    for repo in repos:
        if repo.get("fork") or not repo.get("language"):
            continue
        repo_languages = api_get(f"/repos/{USERNAME}/{repo['name']}/languages")
        for language, size in repo_languages.items():
            language_totals[language] = language_totals.get(language, 0) + size
    top_languages = sorted(language_totals.items(), key=lambda item: item[1], reverse=True)[:5]

    os.makedirs("assets", exist_ok=True)
    with open("assets/github-stats.svg", "w", encoding="utf-8") as file:
        file.write(stats_svg(stats))
    with open("assets/top-languages.svg", "w", encoding="utf-8") as file:
        file.write(languages_svg(top_languages))
    print(f"Generated stats for {USERNAME}: {len(repos)} repositories, {len(top_languages)} languages.")

if __name__ == "__main__":
    main()
