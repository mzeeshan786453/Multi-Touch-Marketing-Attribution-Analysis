# TEYZIX CORE – Multi-Touch Marketing Attribution Analysis
## Task DA-2 | Domain: Data Analytics | Difficulty: Advanced

---

## What This Project Does

This project builds a complete **Multi-Touch Marketing Attribution System**.
It analyzes which marketing channels (like Email, Paid Ads, Organic Search)
deserve credit for converting customers — using 5 different attribution models.

---

## Project Files

```
DA2_project/
│
├── data/
│   └── category_tree.csv          ← PROVIDED DATASET (put it here)
│
├── outputs/                        ← Created automatically when you run main.py
│   ├── touchpoints.csv
│   ├── category_tree_enriched.csv
│   └── attribution_results.csv
│
├── reports/                        ← Created automatically
│   └── marketing_insights_report.txt
│
├── data_pipeline.py               ← Loads dataset + generates touchpoints
├── attribution_models.py          ← All 5 attribution models
├── dashboard.py                   ← Streamlit dashboard
├── generate_report.py             ← Creates the insights report
├── main.py                        ← Run this first
├── requirements.txt               ← Python packages needed
└── README.md                      ← This file
```

---

## How to Run (Step by Step)

### Step 1 – Install Python packages
Open terminal / command prompt in the project folder and run:
```
pip install -r requirements.txt
```

### Step 2 – Make sure the dataset is in place
```
data/category_tree.csv   ← should already be there
```

### Step 3 – Run the main script
```
python main.py
```
This will:
- Load and process the dataset
- Generate 1,500 synthetic customer journeys
- Run all 5 attribution models
- Save results to `outputs/` folder
- Save the insights report to `reports/` folder

### Step 4 – Launch the dashboard
```
streamlit run dashboard.py
```
Then open your browser at: **http://localhost:8501**

---

## Attribution Models

| Model | How it works | Best for |
|-------|-------------|---------|
| First-Touch | 100% credit to the FIRST channel | Measuring awareness |
| Last-Touch | 100% credit to the LAST channel | Measuring conversions |
| Linear | Equal credit to ALL channels | Balanced view |
| Time-Decay | More credit to RECENT channels | Short sales cycles |
| Markov Chain | Statistical removal effect | Strategic decisions |

---

## Dashboard Pages

| Page | What you see |
|------|-------------|
| Overview | KPIs, dataset info, category tree chart |
| Attribution Models | Bar charts, heatmap, model comparison |
| Budget Analysis | ROI scores, budget recommendations |
| Markov Chain | Removal effects, Markov vs Linear comparison |
| Journey Analysis | Funnel, trends, journey length |
| Data | All raw tables with download buttons |

---

## About the Dataset

The provided `category_tree.csv` contains 1,669 product categories in a
hierarchical tree structure. Each category has a `categoryid` and `parentid`.

**How the dataset is used:**
- We calculate the depth of each category in the tree
- Categories at different depths are mapped to marketing channels
- These channel weights are used to generate realistic synthetic touchpoints

**Synthetic data is clearly labeled** with `data_source = "SYNTHETIC"` in all
output files, as required by the task.

---

## Tech Stack

- **Python 3.10+**
- **Pandas** – data processing
- **NumPy** – calculations
- **Plotly** – interactive charts
- **Streamlit** – web dashboard

---

## Troubleshooting

**`streamlit` not found:**
```
pip install streamlit
```

**`ModuleNotFoundError`:**
Make sure you ran `pip install -r requirements.txt`

**Wrong folder error:**
Make sure you are inside the `DA2_project` folder when running commands:
```
cd DA2_project
python main.py
```

**Port already in use:**
```
streamlit run dashboard.py --server.port 8502
```

---

*TEYZIX CORE Internship | Task DA-2 | Multi-Touch Marketing Attribution*
