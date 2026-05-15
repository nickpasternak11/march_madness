import argparse
from collections import Counter

from src.march_madness_sim import MarchMadnessSim
from src.utils import load_json, save_tournament_report


def parse_args():
    parser = argparse.ArgumentParser(description="March Madness Simulation")
    parser.add_argument(
        "--year",
        type=int,
        default=2026,
        help="Year of the tournament to simulate (default: 2026)",
    )
    parser.add_argument(
        "--sd_3pr_scalar",
        type=float,
        default=1.0,
        help="Scalar to adjust the standard deviation of 3-point shooting (default: 1.0)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Start date for simulations in YYYYMMDD format (default: None, uses Jan 1 of the year)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End date for simulations in YYYYMMDD format (default: None, uses current date)",
    )
    parser.add_argument(
        "--n_sims",
        type=int,
        default=100000,
        help="Number of simulations to run (default: 100,000)",
    )
    parser.add_argument(
        "--final_four_settings",
        nargs=4,
        default=["East", "South", "Midwest", "West"],
        help="Regions for the Final Four (default: East South Midwest West)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    year = args.year
    final_four_settings = args.final_four_settings
    brackets = load_json("data/all_brackets.json")
    bracket = brackets.get(year)

    # Run the simulation
    sim = MarchMadnessSim(
        year=year,
        start=args.start,
        end=args.end,
        bracket=bracket,
        final_four_settings=final_four_settings,
        n_sims=args.n_sims,
        sd_3pr_scalar=args.sd_3pr_scalar,
    )
    res = sim.run()

    # Output analysis
    print(f"\n=== {year} MARCH MADNESS SIMULATION RESULTS ===")
    print(res.head(25))

    # Most likely Final Matchups
    final_games = [g for g in sim.all_sim_results if g["round"] == "F2"]

    # Normalize and count the pairs
    # We sort the team names so (A, B) and (B, A) are counted as the same matchup
    matchup_counts = Counter(
        tuple(sorted([g["team_a"], g["team_b"]])) for g in final_games
    )

    print("\n" + "=" * 40)
    print(f"{'MOST LIKELY FINAL MATCHUPS':^40}")
    print("=" * 40)
    for (t1, t2), count in matchup_counts.most_common(10):
        percentage = (count / sim.n_sims) * 100
        print(f"{t1:>18} vs {t2:<18} | {percentage:>6.2f}% ({count:,})")

    # Cinderella Index: A simple metric to identify potential upsets based on seed and advancement probability
    cinderellas = res[res["Seed"] >= 7].copy()
    cinderellas["Cinderella_Index"] = cinderellas["S16"] * cinderellas["Seed"]
    print("\n=== TOP POTENTIAL CINDERELLA TEAMS ===")
    print(
        cinderellas.sort_values("Cinderella_Index", ascending=False)[
            ["Seed", "S16", "E8", "F4", "Cinderella_Index"]
        ].head(10)
    )

    # Save the tournament report as a PDF with visualizations
    save_tournament_report(res, bracket)
