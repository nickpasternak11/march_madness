import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages


def transform_to_ints(data):
    """
    Recursively converts string digits to integers for both keys and values.
    """
    if isinstance(data, dict):
        # Create a new dict: convert key if it's a digit, then recurse on value
        return {
            (int(k) if k.isdigit() else k): transform_to_ints(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        # Recurse on every item in the list (e.g., the First Four team lists)
        return [transform_to_ints(item) for item in data]
    elif isinstance(data, str) and data.isdigit():
        # Convert the value itself if it's a digit string
        return int(data)
    else:
        return data


def load_json(file_path: str | Path):
    with open(file_path, "r") as f:
        raw_data = json.load(f)
    return transform_to_ints(raw_data)


def save_tournament_report(
    df: pd.DataFrame,
    bracket_dict: dict,
    filename: str = "MM_Simulation_Report.pdf",
):
    with PdfPages(f"data/reports/{filename}") as pdf:
        # PAGE 1: Top Overall Contenders
        plt.figure(figsize=(12, 12))
        top_df = df.sort_values("CHAMP", ascending=False).head(20)
        sns.heatmap(
            top_df[["R32", "S16", "E8", "F4", "F2", "CHAMP"]],
            annot=True,
            fmt=".1%",
            cmap="YlGnBu",
            cbar=False,
        )
        plt.title("Tournament Overview: Probability Leaders", fontsize=16)
        pdf.savefig(bbox_inches="tight")
        plt.close()

        # PAGES 2-5: Regional Deep-Dives
        for region in ["East", "West", "South", "Midwest"]:
            # Extract specific teams in the region
            region_teams = []
            for val in bracket_dict[region].values():
                if isinstance(val, list):
                    region_teams.extend(val)
                else:
                    region_teams.append(val)

            reg_df = df.loc[df.index.isin(region_teams)].sort_values("Seed")

            plt.figure(figsize=(12, 10))
            sns.heatmap(
                reg_df[["R32", "S16", "E8", "F4"]],
                annot=True,
                fmt=".1%",
                cmap="YlGnBu",
                cbar=False,
            )
            plt.title(f"{region} Region: Advancement Probabilities", fontsize=16)
            pdf.savefig(bbox_inches="tight")
            plt.close()

    print(f"Tournament report saved successfully as {filename}")
