# March Madness Tournament Simulator

A sophisticated Monte Carlo simulation engine for predicting March Madness tournament outcomes using advanced analytics from Barttorvik college basketball ratings.

## Overview

This project leverages comprehensive college basketball statistics to simulate thousands of tournament scenarios, calculating realistic win probabilities for each team across every round of March Madness. The simulator accounts for team efficiency metrics, three-point shooting rates, tempo, and in-game variance to generate statistically sound predictions.

## Key Features

- **Advanced Team Metrics**: Utilizes Barttorvik adjusted offensive efficiency (adjoe), adjusted defensive efficiency (adjde), and adjusted tempo (adjt)
- **Monte Carlo Simulation**: Runs 10,000+ independent tournament simulations for statistical robustness
- **Realistic Game Modeling**: Incorporates scoring variance based on team three-point shooting rates and accounts for overtime scenarios
- **Dynamic Rating Updates**: Team ratings evolve based on simulated game results using Bayesian smoothing
- **Comprehensive Analysis**: Generates tournament-wide probability heatmaps, regional breakdowns, and Cinderella team identification
- **Visual Reporting**: Produces professional PDF reports with advancement probabilities across all tournament rounds

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nickpasternak11/march_madness.git
cd march_madness
```

2. Install dependencies:
```bash
pip install pandas numpy matplotlib seaborn selenium tqdm
```

3. Ensure you have ChromeDriver installed for web scraping (automatically downloaded by Selenium)

### Basic Usage

```python
from march_madness import MarchMadnessSim
from bracket import bracket as bracket_2026

# Initialize the simulator
sim = MarchMadnessSim(
    year=2026,
    bracket=bracket_2026,
    final_four_settings=["East", "South", "Midwest", "West"],
    n_sims=10000,
    sd_3pr_scalar=0.50,
)

# Run the simulation
results = sim.run()
print(results.head(25))
```

### Simulator Parameters

**`MarchMadnessSim` Constructor:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `year` | `int` | Tournament year (used to fetch Barttorvik data) |
| `bracket` | `Dict[str, dict]` | Tournament bracket structure mapping regions to seeded teams |
| `final_four_settings` | `List[str]` | List of four regions in tournament order (e.g., ["East", "South", "Midwest", "West"]) |
| `start` | `int` | Optional—Begin date filter for Barttorvik data (format: YYYYMMDD) |
| `end` | `int` | Optional—End date filter for Barttorvik data (format: YYYYMMDD) |
| `n_sims` | `int` | Number of tournament simulations to run (default: 10,000) |
| `sd_3pr_scalar` | `float` | Scoring volatility coefficient based on three-point shooting (default: 0.20; range: 0.0-1.0) |

**Parameter Notes:**
- `n_sims`: Higher values provide more statistical accuracy but increase computation time
- `sd_3pr_scalar`: Controls how much three-point shooting rates influence game-to-game scoring variance. A value of 0.50 means 50% of scoring variance is attributed to three-point shooting volatility
- `start/end`: Allows filtering team performance to specific date ranges (useful for mid-season or tournament-mode analysis)

## Data Source

Tournament simulations powered by [Barttorvik College Basketball Rankings](https://barttorvik.com). Team data is automatically scraped on initialization, including adjusted offensive efficiency, adjusted defensive efficiency, adjusted tempo, and three-point shooting metrics.

## Project Structure

```
march_madness/
├── march_madness.py          # Main simulator class and game logic
├── bracket.py                # Tournament bracket definitions
├── README.md                 # This file
└── all_brackets.json         # Historical bracket configurations
```