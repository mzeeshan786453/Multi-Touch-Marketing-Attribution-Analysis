# =============================================================
# data_pipeline.py
# Step 1: Load the dataset, build category tree, and generate
#         synthetic marketing touchpoint data from it.
# =============================================================

import pandas as pd
import numpy as np
import os

# Fix random seed so results are the same every run
np.random.seed(42)

# Get the directory where this file lives
# This makes all paths work on both local machine and Streamlit Cloud
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------
# Marketing channels mapped from category tree depth levels
# ------------------------------------------------------------------
DEPTH_TO_CHANNEL = {
    0: "Organic Search",
    1: "Paid Social",
    2: "Email Marketing",
    3: "Display Ads",
    4: "Direct / Referral",
    5: "Direct / Referral",
}

CHANNELS = [
    "Organic Search",
    "Paid Social",
    "Email Marketing",
    "Display Ads",
    "Direct / Referral",
]

CHANNEL_BUDGET = {
    "Organic Search":    45000,
    "Paid Social":       30000,
    "Email Marketing":   20000,
    "Display Ads":       25000,
    "Direct / Referral": 15000,
}


# ==================================================================
# PART 1 — Load and process the real category_tree.csv dataset
# ==================================================================

def load_dataset(path=None):
    """Load the provided category_tree.csv file."""
    if path is None:
        path = os.path.join(BASE_DIR, "data", "category_tree.csv")

    df = pd.read_csv(path)
    df["parentid"] = pd.to_numeric(df["parentid"], errors="coerce")
    print(f"[OK] Loaded dataset: {len(df)} categories | {df['parentid'].isna().sum()} root nodes")
    return df


def calculate_depth(df):
    """Calculate how deep each category is in the tree."""
    parent_map  = dict(zip(df["categoryid"], df["parentid"]))
    depth_cache = {}

    def get_depth(cid, visited=None):
        if visited is None:
            visited = set()
        if cid in depth_cache:
            return depth_cache[cid]
        if cid in visited:
            depth_cache[cid] = 0
            return 0
        visited.add(cid)
        pid = parent_map.get(cid)
        if pd.isna(pid):
            depth_cache[cid] = 0
        else:
            depth_cache[cid] = 1 + get_depth(int(pid), visited)
        return depth_cache[cid]

    for cid in df["categoryid"]:
        get_depth(cid)

    df = df.copy()
    df["depth"]   = df["categoryid"].map(depth_cache)
    df["channel"] = df["depth"].map(DEPTH_TO_CHANNEL)
    return df


# ==================================================================
# PART 2 — Generate synthetic touchpoint data
# NOTE: data_source = "SYNTHETIC" is set on every row
# ==================================================================

def generate_touchpoints(category_df, n_journeys=1500):
    """Generate synthetic customer journey touchpoint records."""

    # Channel weights from real category tree depth distribution
    depth_counts = category_df["depth"].value_counts().sort_index()
    raw_weights  = []
    for ch_depth in range(5):
        count = depth_counts.get(ch_depth, 0) + depth_counts.get(ch_depth + 1, 0)
        raw_weights.append(max(count, 1))

    total           = sum(raw_weights)
    channel_weights = [w / total for w in raw_weights]

    print(f"[OK] Channel weights: {dict(zip(CHANNELS, [round(w,3) for w in channel_weights]))}")

    records = []
    for journey_id in range(1, n_journeys + 1):
        n_touches          = np.random.randint(1, 7)
        channels_in_journey = np.random.choice(CHANNELS, size=n_touches, p=channel_weights).tolist()
        did_convert        = np.random.random() < 0.35
        revenue            = round(np.random.uniform(50, 500), 2) if did_convert else 0.0
        start_day          = np.random.randint(0, 345)

        for i, channel in enumerate(channels_in_journey):
            day     = start_day + i
            month   = min(day // 30 + 1, 12)
            quarter = (month - 1) // 3 + 1
            records.append({
                "journey_id":    journey_id,
                "touch_order":   i + 1,
                "total_touches": n_touches,
                "channel":       channel,
                "month":         f"2025-{month:02d}",
                "quarter":       f"2025-Q{quarter}",
                "converted":     did_convert,
                "revenue":       revenue,
                "is_first":      (i == 0),
                "is_last":       (i == n_touches - 1),
                "data_source":   "SYNTHETIC",
            })

    df              = pd.DataFrame(records)
    converted_count = df.groupby("journey_id")["converted"].first().sum()
    print(f"[OK] Generated {len(df)} touchpoints | {n_journeys} journeys | {converted_count} conversions")
    return df


# ==================================================================
# PART 3 — Run the full pipeline
# ==================================================================

def run_pipeline(csv_path=None):
    """
    Run the complete data pipeline.
    Uses BASE_DIR-relative paths so it works locally AND on Streamlit Cloud.
    Returns: (category_df, touchpoints_df)
    """
    print("\n" + "="*55)
    print("  DATA PIPELINE")
    print("="*55)

    # Always use absolute paths based on where this file is located
    if csv_path is None:
        csv_path = os.path.join(BASE_DIR, "data", "category_tree.csv")

    out_dir = os.path.join(BASE_DIR, "outputs")
    rep_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(rep_dir, exist_ok=True)

    # Step 1: Load real dataset
    cat_df = load_dataset(csv_path)

    # Step 2: Calculate tree depth and assign channels
    cat_df = calculate_depth(cat_df)

    # Step 3: Generate synthetic touchpoints
    touchpoints = generate_touchpoints(cat_df, n_journeys=1500)

    # Step 4: Save outputs
    touchpoints.to_csv(os.path.join(out_dir, "touchpoints.csv"), index=False)
    cat_df.to_csv(os.path.join(out_dir, "category_tree_enriched.csv"), index=False)

    print("[OK] Saved outputs/touchpoints.csv")
    print("[OK] Saved outputs/category_tree_enriched.csv")

    return cat_df, touchpoints


# Run directly to test
if __name__ == "__main__":
    cat_df, tp = run_pipeline()
    print("\nCategory tree sample:")
    print(cat_df.head(5).to_string(index=False))
    print("\nTouchpoints sample:")
    print(tp.head(10).to_string(index=False))
