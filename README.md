# March Madness Tournament Simulator

A sophisticated Monte Carlo simulation engine for predicting March Madness tournament outcomes using advanced analytics from Barttorvik college basketball ratings.

## Overview

This project leverages comprehensive college basketball statistics to simulate thousands of tournament scenarios, calculating realistic win probabilities for each team across every round of March Madness. The simulator uses web scraping to fetch current Barttorvik team metrics and employs Bayesian smoothing to dynamically update team ratings throughout simulated tournament play.

## Key Features

- **Advanced Team Metrics**: Utilizes Barttorvik adjusted offensive efficiency (adjoe), adjusted defensive efficiency (adjde), and adjusted tempo (adjt)
- **Monte Carlo Simulation**: Runs 10,000+ independent tournament simulations for statistical robustness
- **Realistic Game Modeling**: Incorporates scoring variance based on team three-point shooting rates and accounts for overtime scenarios
- **Dynamic Rating Updates**: Team ratings evolve based on simulated game results using Bayesian smoothing
- **Comprehensive Analysis**: Generates championship probabilities, Final Four predictions, and Cinderella team identification
- **Visual Reporting**: Produces professional PDF reports with advancement probabilities across all tournament rounds
- **Flexible Input**: Command-line interface for customizing simulation parameters

## Getting Started

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nickpasternak11/march_madness.git
cd march_madness
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure you have ChromeDriver installed for web scraping (Selenium will manage this automatically)

### Basic Usage

Run the simulator with default parameters:
```bash
python main.py
```

### Command-Line Arguments

Customize simulations with the following arguments:

```bash
python main.py \
  --year 2026 \
  --n_sims 100000 \
  --sd_3pr_scalar 1.0 \
  --start 20260101 \
  --end 20260315 \
  --final_four_settings East South Midwest West
```

#### Available Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--year` | `int` | 2026 | Tournament year (used to fetch Barttorvik data) |
| `--n_sims` | `int` | 100,000 | Number of tournament simulations to run |
| `--sd_3pr_scalar` | `float` | 1.0 | Scoring volatility coefficient based on three-point shooting (range: 0.0-1.0) |
| `--start` | `int` | None | Start date filter for Barttorvik data (format: YYYYMMDD) |
| `--end` | `int` | None | End date filter for Barttorvik data (format: YYYYMMDD) |
| `--final_four_settings` | `str` (4 args) | East South Midwest West | Regions in tournament order |

**Parameter Notes:**
- `--n_sims`: Higher values provide more statistical accuracy but increase computation time
- `--sd_3pr_scalar`: Controls how much three-point shooting rates influence game-to-game scoring variance. A value of 1.0 means full weight is given to three-point shooting volatility
- `--start/--end`: Allows filtering team performance to specific date ranges (useful for mid-season or tournament-mode analysis)

## Output

The simulator produces:
1. **Console Output**: Championship probabilities, championship-game matchups, and Cinderella index
2. **PDF Report**: `MM_Simulation_Report.pdf` with:
   - Overall tournament probability heatmaps
   - Regional deep-dives with team advancement odds
   - Advanced round projections

## Data Source

Tournament simulations powered by [Barttorvik College Basketball Rankings](https://barttorvik.com). Team data is automatically scraped on initialization, including adjusted offensive efficiency, adjusted defensive efficiency, and game tempo.

## Project Structure

```
march_madness/
├── main.py                    # Entry point and CLI argument handling
├── requirements.txt           # Python package dependencies
├── bracket.py                 # Tournament bracket definitions (2026 format)
├── scripts/
│   └── scrape_brackets.py     # Historical bracket scraper utility
├── data/
│   └── all_brackets.json      # Bracket data for historical tournaments
├── src/
│   ├── march_madness_sim.py   # Core simulator class and tournament logic
│   └── utils.py               # Utility functions (data loading, report generation)
└── README.md                  # This file
```

## How It Works

### 1. **Data Collection**
- Fetches current team statistics from Barttorvik using Selenium web scraping
- Calculates league averages for key metrics (adjoe, adjde, adjt, 3P rate)

### 2. **Simulation Loop**
For each of the `n_sims` simulations:
- Plays out all tournament games using probability-based outcomes
- Game scores incorporate three-point shooting variance
- Updates team ratings based on results (Bayesian smoothing)

### 3. **Analysis**
- Aggregates results across all simulations
- Calculates advancement probabilities for each team in each round
- Identifies likely Final Four matchups and Cinderella candidates

### 4. **Reporting**
- Generates probability tables ranked by championship odds
- Creates visualization heatmaps of tournament advancement by region
- Produces PDF report with key insights

## Notes

- Simulations use [Barthag](https://barttorvik.com/about.php) ratings as the foundation for team strength
- Overtime scenarios are accounted for in game modeling via possession count normalization
- The simulator is stochastic—results vary between runs; use `--n_sims` to control variance
- PDF reports are generated in the working directory as `MM_Simulation_Report.pdf`
