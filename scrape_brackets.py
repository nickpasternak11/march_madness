import csv
import json
from collections import defaultdict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.sports-reference.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}
REGIONAL_ROUND_NAMES = [
    "R64",
    "R32",
    "S6",
    "E8",
]
NATIONAL_ROUND_NAMES = ["F4", "F2"]
REGION_NAMES = ["east", "west", "south", "midwest"]


def get_tournament_links(years: list[int]):
    # Navigate to Sports-Reference
    url = "https://www.sports-reference.com/cbb/postseason/"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Locate the table of march madness tourney info
    table = soup.find("table", id="ncaa-tournament-history_NCAAM")
    tbody = table.find("tbody")

    tournament_links = []
    for row in tbody.find_all("tr"):
        # skip header rows accidentally embedded in tbody
        if row.get("class") == ["thead"]:
            continue

        cell = row.find("th", {"data-stat": "ncaa_tourney"})
        if not cell:
            continue

        a_tag = cell.find("a")
        if not a_tag:
            continue

        href = a_tag["href"]
        year = int(href.split("/")[-1].split("-")[0])
        if year not in years:
            continue

        tournament_links.append(urljoin(BASE_URL, href))

    return sorted(tournament_links)


def parse_first_four(region_div, year, region):
    games = []
    p_tag = region_div.find("p")
    if not p_tag:
        return games

    # Extract all text segments to avoid being tripped up by <strong> vs <a>
    raw_parts = [
        part.strip()
        for part in p_tag.get_text(separator="|").split("|")
        if part.strip()
    ]

    current_teams = []
    i = 0
    while i < len(raw_parts):
        # Anchor on the seed (must be numeric)
        if raw_parts[i].isdigit():
            seed = int(raw_parts[i])
            team_name = raw_parts[i + 1]
            score = None

            # Check if the segment after the team name is a score
            if i + 2 < len(raw_parts) and raw_parts[i + 2].isdigit():
                score = int(raw_parts[i + 2])
                i += 3  # Move past seed, name, and score
            else:
                i += 2  # Move past seed and name

            current_teams.append({"seed": seed, "team": team_name, "score": score})

            # Pair them up as soon as we have two teams
            if len(current_teams) == 2:
                t1, t2 = current_teams
                winner = None
                if t1["score"] is not None and t2["score"] is not None:
                    winner = t1["team"] if t1["score"] > t2["score"] else t2["team"]

                games.append(
                    {
                        "year": year,
                        "region": region.capitalize(),
                        "round": "First4",
                        "team_a": t1["team"],
                        "seed_a": t1["seed"],
                        "score_a": t1["score"],
                        "team_b": t2["team"],
                        "seed_b": t2["seed"],
                        "score_b": t2["score"],
                        "winner": winner,
                    }
                )
                current_teams = []
        else:
            i += 1

    return games


def parse_team(team_div):
    # ---- Seed ----
    seed_tag = team_div.find("span")
    seed = None
    if seed_tag:
        seed_text = seed_tag.text.strip()
        if seed_text.isdigit():
            seed = int(seed_text)

    # ---- Links (name + score) ----
    a_tags = team_div.find_all("a")
    if not a_tags:
        return None, None, None, False

    # Team name is always first link
    team = a_tags[0].text.strip()

    # ---- Score ----
    score = None
    if len(a_tags) > 1:
        score_text = a_tags[-1].text.strip()
        if score_text.isdigit():
            score = int(score_text)

    # ---- Winner flag ----
    is_winner = "winner" in team_div.get("class", [])

    return seed, team, score, is_winner


def scrape_bracket(link: str):
    bracket_data = defaultdict(lambda: {})
    games_data = []
    year = int(link.split("/")[-1].split("-")[0])

    resp = requests.get(link, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")

    brackets = soup.find("div", id="brackets")
    for region_div in brackets.find_all("div", recursive=False):
        region = region_div.get("id")
        if not region:
            continue

        # ---- FIRST FOUR ----
        first_four_games = parse_first_four(region_div, year, region)
        games_data.extend(first_four_games)
        for game in first_four_games:
            bracket_data[region.capitalize()][game["seed_a"]] = [
                game["team_a"],
                game["team_b"],
            ]

        # --- REGIONAL PLAY ----
        bracket_div = region_div.find("div", id="bracket")
        if not bracket_div:
            continue

        rounds = bracket_div.find_all("div", class_="round", recursive=False)
        for r_idx, round_div in enumerate(rounds):
            round_names = (
                NATIONAL_ROUND_NAMES if region == "national" else REGIONAL_ROUND_NAMES
            )
            if r_idx >= len(round_names):
                continue
            round_str = round_names[r_idx]

            # skip empty final placeholder round
            games = round_div.find_all("div", recursive=False)
            if not games:
                continue

            for game in games:
                teams = game.find_all("div", recursive=False)

                if len(teams) < 2:
                    continue  # skip incomplete

                seed_a, team_a, score_a, win_a = parse_team(teams[0])
                seed_b, team_b, score_b, _ = parse_team(teams[1])
                winner = team_a if win_a else team_b

                if round_str == "R64" and region in REGION_NAMES:
                    if bracket_data[region.capitalize()].get(seed_a) is None:
                        bracket_data[region.capitalize()][seed_a] = team_a
                    if bracket_data[region.capitalize()].get(seed_b) is None:
                        bracket_data[region.capitalize()][seed_b] = team_b

                games_data.append(
                    {
                        "year": year,
                        "region": region.capitalize(),
                        "round": round_str,
                        "team_a": team_a,
                        "seed_a": seed_a,
                        "score_a": score_a,
                        "team_b": team_b,
                        "seed_b": seed_b,
                        "score_b": score_b,
                        "winner": winner,
                    }
                )

    return {year: dict(bracket_data)}, games_data


def scrape_brackets(years: list[int]):
    all_brackets = {}
    all_toruney_games = []

    tournament_links = get_tournament_links(years)
    for link in tournament_links:
        print(f"Scraping {link}")

        bracket_data, games_data = scrape_bracket(link)
        all_brackets.update(bracket_data)
        all_toruney_games.extend(games_data)

    with open("all_brackets.json", "w", encoding="utf-8") as f:
        json.dump(all_brackets, f, indent=2)
    print("Saved all_brackets.json")

    fieldnames = all_toruney_games[0].keys()
    with open("all_tourney_games.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_toruney_games)
    print("Saved all_tourney_games.csv")


if __name__ == "__main__":
    scrape_brackets(years=list(range(2002, 2026)))
