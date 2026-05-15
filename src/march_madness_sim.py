import os
import time
from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

team_stats_columns = [
    "team",
    "adjoe",
    "adjde",
    "Barthag",
    "Record",
    "Wins",
    "Games",
    "eFG%",
    "eFG% D",
    "FT Rate",
    "FT Rate D",
    "TOV%",
    "TOV% D",
    "O Reb%",
    "Op OReb%",
    "Raw T",
    "2P %",
    "2P % D",
    "3P %",
    "3P % D",
    "Blk %",
    "Blked %",
    "Ast %",
    "Op Ast %",
    "3P Rate",
    "3P Rate D",
    "adjt",
    "Avg Hgt",
    "Eff Hgt",
    "Exp",
    "Year",
    "PAKE",
    "PASE",
    "Talent",
    "",
    "FT%",
    "Op FT%",
    "PPP Off",
    "PPP Def",
    "Elite SOS",
]


class MarchMadnessSim:
    def __init__(
        self,
        year: int,
        bracket: Dict[str, dict],
        final_four_settings: List[str],
        start: int = None,
        end: int = None,
        n_sims: int = 10000,
        sd_3pr_scalar: float = 0.20,
    ):
        self.n_sims = n_sims
        self.sd_3pr_scalar = sd_3pr_scalar
        self.bracket: Dict[str, dict] = bracket
        self.final_four_settings = final_four_settings
        self.team_stats_df: pd.DataFrame = self.scrape_team_data(year, start, end)
        self.seed_mapping = self.get_seed_mapping()

        # Pre-calculate league averages once
        self.avg_adjoe = self.team_stats_df["adjoe"].mean()
        self.avg_adjde = self.team_stats_df["adjde"].mean()
        self.avg_adjt = self.team_stats_df["adjt"].mean()
        self.avg_3pr = self.team_stats_df["3P Rate"].mean()

        self.all_sim_results = []

    @staticmethod
    def scrape_team_data(
        year: int, start: Optional[int] = None, end: Optional[int] = None
    ) -> pd.DataFrame:
        print("Scraping barttorvik data..")

        file_name = "trank_team_table_data.csv"
        if os.path.exists(file_name):
            os.remove(file_name)

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        download_dir = os.path.abspath(".")

        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,  # Disable safebrowsing to allow CSVs
            },
        )

        driver = webdriver.Chrome(options=chrome_options)

        # Allow downloads in headless mode
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": download_dir},
        )

        try:
            url = f"https://barttorvik.com/team-tables_each.php?year={year}"
            if start:
                url += f"&begin={start}"
            if end:
                url += f"&end={end}"
            url += "&csv=1"

            print(f"Navigating to: {url}")
            driver.get(url)

            # Wait for the JS verification form to auto-submit and trigger the download
            print("Waiting for browser verification and download...")
            time.sleep(5)

            # Wait for file to appear on disk
            timeout = 20
            elapsed = 0
            while not os.path.exists(file_name) and elapsed < timeout:
                temp_files = [f for f in os.listdir(".") if f.endswith(".crdownload")]
                if temp_files:
                    print(f"Download started... (found {temp_files[0]})")

                time.sleep(1)
                elapsed += 1

            if not os.path.exists(file_name):
                raise RuntimeError("CSV download failed within timeout")

        finally:
            driver.quit()

        print("Web scraping complete!")
        df = pd.read_csv(file_name, header=None)
        df.columns = team_stats_columns
        return df.set_index("team")

    def get_seed_mapping(self):
        seed_map = {}
        for region in self.bracket.values():
            for seed, team in region.items():
                if isinstance(team, list):
                    # For play-ins, we'll just map both to that seed for now
                    for t in team:
                        seed_map[t] = int(seed)
                else:
                    seed_map[team] = int(seed)
        return seed_map

    def _update_metrics(
        self, team_a, team_b, score_a, score_b, total_poss, current_data, alpha=0.05
    ):
        tA, tB = current_data[team_a], current_data[team_b]
        league_avg_eff = self.avg_adjoe

        # Observed game efficiencies (Self-correcting for OT because of 'total_poss')
        game_adjoe_A = (
            (score_a / total_poss) / (tB["adjde"] / league_avg_eff) * league_avg_eff
        )
        game_adjde_A = (
            (score_b / total_poss) / (tB["adjoe"] / league_avg_eff) * league_avg_eff
        )
        game_adjoe_B = (
            (score_b / total_poss) / (tA["adjde"] / league_avg_eff) * league_avg_eff
        )
        game_adjde_B = (
            (score_a / total_poss) / (tA["adjoe"] / league_avg_eff) * league_avg_eff
        )

        # Update ratings
        for team, oe, de in [
            (team_a, game_adjoe_A, game_adjde_A),
            (team_b, game_adjoe_B, game_adjde_B),
        ]:
            current_data[team]["adjoe"] = (1 - alpha) * current_data[team][
                "adjoe"
            ] + alpha * oe
            current_data[team]["adjde"] = (1 - alpha) * current_data[team][
                "adjde"
            ] + alpha * de
            # We use the total_poss for tempo, but the smoothing alpha mitigates OT inflation
            current_data[team]["adjt"] = (1 - alpha) * current_data[team][
                "adjt"
            ] + alpha * total_poss

    def simulate_game(
        self,
        team_a: str,
        team_b: str,
        current_data: dict,
        round_str: str,
        region: str,
        is_ot: bool = False,
        acc_a: float = 0,
        acc_b: float = 0,
        acc_poss: float = 0,
    ):
        stats_a, stats_b = current_data[team_a], current_data[team_b]
        dt = 0.125 if is_ot else 1.0
        base_scoring_sd = 7.5

        # Scale scoring SD by adjusted 3pt Rate
        vol_a = 1 + self.sd_3pr_scalar * (
            (
                ((stats_a["3P Rate"] * stats_b["3P Rate D"]) / self.avg_3pr)
                / self.avg_3pr
            )
            - 1
        )
        vol_b = 1 + self.sd_3pr_scalar * (
            (
                ((stats_b["3P Rate"] * stats_a["3P Rate D"]) / self.avg_3pr)
                / self.avg_3pr
            )
            - 1
        )

        sd_a = base_scoring_sd * vol_a * np.sqrt(dt)
        sd_b = base_scoring_sd * vol_b * np.sqrt(dt)

        # Posessions
        exp_poss = ((stats_a["adjt"] * stats_b["adjt"]) / self.avg_adjt) * dt
        actual_poss = np.random.normal(exp_poss, 3.5 * np.sqrt(dt))

        # Efficiency
        eff_a = (stats_a["adjoe"] * stats_b["adjde"]) / self.avg_adjoe
        eff_b = (stats_b["adjoe"] * stats_a["adjde"]) / self.avg_adjoe

        # Scoring
        exp_score_a = (eff_a / 100) * actual_poss
        exp_score_b = (eff_b / 100) * actual_poss

        actual_score_a = np.random.normal(exp_score_a, sd_a)
        actual_score_b = np.random.normal(exp_score_b, sd_b)

        # Final numbers
        total_a = acc_a + actual_score_a
        total_b = acc_b + actual_score_b
        total_poss = acc_poss + actual_poss

        # Overtime
        if round(total_a) == round(total_b):
            return self.simulate_game(
                team_a,
                team_b,
                current_data,
                round_str,
                region,
                True,
                total_a,
                total_b,
                total_poss,
            )

        # Finalize and Update
        self._update_metrics(team_a, team_b, total_a, total_b, total_poss, current_data)

        winner = team_a if total_a > total_b else team_b

        self.all_sim_results.append(
            {
                "round": round_str,
                "region": region,
                "seed_a": self.seed_mapping[team_a],
                "team_a": team_a,
                "sd_a": sd_a,
                "score_a": total_a,
                "seed_b": self.seed_mapping[team_b],
                "team_b": team_b,
                "sd_b": sd_b,
                "score_b": total_b,
                "is_ot": acc_a > 0,
                "winner": winner,
            }
        )

        return team_a if total_a > total_b else team_b

    def simulate_tournament(self, current_data: dict):
        results = defaultdict(list)
        final_four_teams = []

        # Regional play
        for region in self.final_four_settings:
            seeds = {}

            # Handle play-ins
            for seed, team in self.bracket[region].items():
                seeds[seed] = (
                    self.simulate_game(
                        team[0],
                        team[1],
                        current_data,
                        round_str="FIRST4",
                        region=region,
                    )
                    if isinstance(team, list)
                    else team
                )

            # R64
            r64_m = [
                (1, 16),
                (8, 9),
                (5, 12),
                (4, 13),
                (6, 11),
                (3, 14),
                (7, 10),
                (2, 15),
            ]
            r32_w = [
                self.simulate_game(
                    seeds[a], seeds[b], current_data, round_str="R64", region=region
                )
                for a, b in r64_m
            ]
            results["R32"].extend(r32_w)

            # R32
            s16_w = [
                self.simulate_game(
                    r32_w[i], r32_w[i + 1], current_data, round_str="R32", region=region
                )
                for i in range(0, 8, 2)
            ]
            results["S16"].extend(s16_w)

            # R16
            e8_w = [
                self.simulate_game(
                    s16_w[i], s16_w[i + 1], current_data, round_str="S16", region=region
                )
                for i in range(0, 4, 2)
            ]
            results["E8"].extend(e8_w)

            # E8
            regional_champ = self.simulate_game(
                e8_w[0], e8_w[1], current_data, round_str="E8", region=region
            )
            results["F4"].append(regional_champ)
            final_four_teams.append(regional_champ)

        # Final four
        f2_1 = self.simulate_game(
            final_four_teams[0],
            final_four_teams[1],
            current_data,
            round_str="F4",
            region="F4",
        )
        f2_2 = self.simulate_game(
            final_four_teams[2],
            final_four_teams[3],
            current_data,
            round_str="F4",
            region="F4",
        )
        results["F2"].extend([f2_1, f2_2])

        # Championship
        results["CHAMP"].append(
            self.simulate_game(f2_1, f2_2, current_data, round_str="F2", region="F2")
        )

        return results

    def run(self) -> pd.DataFrame:
        rounds = ["R32", "S16", "E8", "F4", "F2", "CHAMP"]
        counts = {r: defaultdict(int) for r in rounds}
        base_stats = self.team_stats_df.to_dict(orient="index")

        for _ in tqdm(range(self.n_sims), desc="Simulating.."):
            current_data = {t: s.copy() for t, s in base_stats.items()}
            tourney = self.simulate_tournament(current_data)
            for r in rounds:
                for team in tourney[r]:
                    counts[r][team] += 1

        final_df = pd.DataFrame(index=self.team_stats_df.index, columns=rounds).fillna(
            0
        )
        for r in rounds:
            for team, count in counts[r].items():
                final_df.at[team, r] = count / self.n_sims

        final_df["Seed"] = final_df.index.map(self.seed_mapping)

        return final_df.sort_values("CHAMP", ascending=False)
