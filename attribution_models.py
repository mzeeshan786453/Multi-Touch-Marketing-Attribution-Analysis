# =============================================================
# attribution_models.py
# Step 2: All attribution models
#   1. First-Touch
#   2. Last-Touch
#   3. Linear
#   4. Time-Decay
#   5. Markov Chain (Bonus)
# =============================================================

import pandas as pd
import numpy as np


# ------------------------------------------------------------------
# Helper: get only touchpoints from journeys that converted
# ------------------------------------------------------------------
def get_converted_journeys(df):
    converted_ids = df[df["converted"] == True]["journey_id"].unique()
    return df[df["journey_id"].isin(converted_ids)].copy()


# ==================================================================
# MODEL 1 — First-Touch Attribution
# Logic: The FIRST channel in the journey gets 100% of the credit
# Good for: measuring which channels drive initial awareness
# ==================================================================
def first_touch_attribution(df):
    converted = get_converted_journeys(df)

    # Keep only the first touchpoint of each journey
    first_touches = converted[converted["is_first"] == True]

    # Count conversions and sum revenue per channel
    result = first_touches.groupby("channel").agg(
        conversions = ("journey_id", "count"),
        revenue     = ("revenue", "sum")
    ).reset_index()

    # Credit = share of total conversions
    result["credit"] = result["conversions"] / result["conversions"].sum()
    result["model"]  = "First-Touch"

    return result.sort_values("credit", ascending=False).reset_index(drop=True)


# ==================================================================
# MODEL 2 — Last-Touch Attribution
# Logic: The LAST channel before conversion gets 100% of the credit
# Good for: measuring which channels close / convert leads
# ==================================================================
def last_touch_attribution(df):
    converted = get_converted_journeys(df)

    # Keep only the last touchpoint of each journey
    last_touches = converted[converted["is_last"] == True]

    result = last_touches.groupby("channel").agg(
        conversions = ("journey_id", "count"),
        revenue     = ("revenue", "sum")
    ).reset_index()

    result["credit"] = result["conversions"] / result["conversions"].sum()
    result["model"]  = "Last-Touch"

    return result.sort_values("credit", ascending=False).reset_index(drop=True)


# ==================================================================
# MODEL 3 — Linear Attribution
# Logic: Credit is split EQUALLY across all touchpoints in a journey
# Good for: giving fair credit to every channel that helped
# ==================================================================
def linear_attribution(df):
    converted = get_converted_journeys(df).copy()

    # Each touch gets equal share: 1 / total_touches
    converted["touch_credit"] = 1.0 / converted["total_touches"]
    converted["rev_credit"]   = converted["revenue"] / converted["total_touches"]

    result = converted.groupby("channel").agg(
        conversions = ("touch_credit", "sum"),
        revenue     = ("rev_credit", "sum")
    ).reset_index()

    result["credit"] = result["conversions"] / result["conversions"].sum()
    result["model"]  = "Linear"

    return result.sort_values("credit", ascending=False).reset_index(drop=True)


# ==================================================================
# MODEL 4 — Time-Decay Attribution
# Logic: More credit goes to channels that appeared LATER (closer
#        to the conversion). Earlier touches get less credit.
# Good for: short sales cycles where recency matters more
# ==================================================================
def time_decay_attribution(df):
    converted = get_converted_journeys(df).copy()

    # Weight = touch_order / sum of all touch orders in that journey
    # Example: journey [ch1, ch2, ch3] → weights [1/6, 2/6, 3/6]
    order_sum = converted.groupby("journey_id")["touch_order"].transform("sum")
    converted["weight"]    = converted["touch_order"] / order_sum
    converted["rev_credit"] = converted["revenue"] * converted["weight"]

    result = converted.groupby("channel").agg(
        conversions = ("weight", "sum"),
        revenue     = ("rev_credit", "sum")
    ).reset_index()

    result["credit"] = result["conversions"] / result["conversions"].sum()
    result["model"]  = "Time-Decay"

    return result.sort_values("credit", ascending=False).reset_index(drop=True)


# ==================================================================
# MODEL 5 — Markov Chain Attribution (Bonus)
# Logic: Build a probability graph of channel transitions.
#        Remove each channel one by one and measure how much the
#        conversion rate drops. Bigger drop = more important channel.
#        This is called the "Removal Effect".
# ==================================================================
def markov_chain_attribution(df, n_simulations=4000):
    channels = df["channel"].unique().tolist()

    # ── Step 1: Build transition counts ──────────────────────
    # We track: what channel comes after each channel?
    # Special states: "(start)" = beginning, "(conv)" = converted, "(null)" = did not convert
    transition_counts = {}

    for journey_id, group in df.groupby("journey_id"):
        seq       = group.sort_values("touch_order")["channel"].tolist()
        converted = group["converted"].iloc[0]

        # (start) → first channel
        prev = "(start)"
        for channel in seq:
            if prev not in transition_counts:
                transition_counts[prev] = {}
            transition_counts[prev][channel] = transition_counts[prev].get(channel, 0) + 1
            prev = channel

        # last channel → outcome
        outcome = "(conv)" if converted else "(null)"
        if prev not in transition_counts:
            transition_counts[prev] = {}
        transition_counts[prev][outcome] = transition_counts[prev].get(outcome, 0) + 1

    # ── Step 2: Convert counts to probabilities ───────────────
    transition_probs = {}
    for state, targets in transition_counts.items():
        total = sum(targets.values())
        transition_probs[state] = {t: v / total for t, v in targets.items()}

    # ── Step 3: Simulate random walks to get conversion rate ──
    def simulate(probs, n=n_simulations):
        rng = np.random.default_rng(42)
        conversions = 0
        for _ in range(n):
            state = "(start)"
            for _ in range(30):   # max steps per journey
                if state not in probs or not probs[state]:
                    break
                next_states = list(probs[state].keys())
                next_probs  = list(probs[state].values())
                state = rng.choice(next_states, p=next_probs)
                if state == "(conv)":
                    conversions += 1
                    break
                elif state == "(null)":
                    break
        return conversions / n

    # ── Step 4: Baseline conversion rate ─────────────────────
    baseline_cr = simulate(transition_probs)

    # ── Step 5: Removal effect for each channel ───────────────
    removal_effects = {}
    for channel in channels:
        # Build modified transition matrix with this channel removed
        modified = {}
        for state, targets in transition_probs.items():
            if state == channel:
                # This channel now goes straight to null (removed)
                modified[state] = {"(null)": 1.0}
            else:
                # Remove this channel from all target options
                new_targets = {t: v for t, v in targets.items() if t != channel}
                total = sum(new_targets.values())
                if total > 0:
                    modified[state] = {t: v / total for t, v in new_targets.items()}
                else:
                    modified[state] = {"(null)": 1.0}

        cr_without = simulate(modified)
        removal_effects[channel] = max(baseline_cr - cr_without, 0)

    # ── Step 6: Normalise into attribution credits ────────────
    total_effect = sum(removal_effects.values())
    if total_effect == 0:
        total_effect = 1  # avoid division by zero

    # Get total conversions and revenue for scaling
    conv_df       = get_converted_journeys(df)
    total_conv    = conv_df["journey_id"].nunique()
    total_revenue = conv_df.groupby("journey_id")["revenue"].first().sum()

    rows = []
    for channel, effect in removal_effects.items():
        credit = effect / total_effect
        rows.append({
            "channel":         channel,
            "conversions":     round(credit * total_conv, 2),
            "revenue":         round(credit * total_revenue, 2),
            "credit":          credit,
            "removal_effect":  round(effect, 5),
            "model":           "Markov Chain",
        })

    result = pd.DataFrame(rows).sort_values("credit", ascending=False).reset_index(drop=True)
    return result


# ==================================================================
# Run all models together
# ==================================================================
def run_all_models(df):
    """Run all 5 attribution models and return combined results."""

    print("\n" + "="*55)
    print("  RUNNING ATTRIBUTION MODELS")
    print("="*55)

    print("  Running First-Touch...")
    r1 = first_touch_attribution(df)

    print("  Running Last-Touch...")
    r2 = last_touch_attribution(df)

    print("  Running Linear...")
    r3 = linear_attribution(df)

    print("  Running Time-Decay...")
    r4 = time_decay_attribution(df)

    print("  Running Markov Chain (bonus)...")
    r5 = markov_chain_attribution(df)

    combined = pd.concat([r1, r2, r3, r4, r5], ignore_index=True)
    combined.to_csv("outputs/attribution_results.csv", index=False)

    print("[OK] All models done! Saved outputs/attribution_results.csv")
    return combined


# Run directly to test
if __name__ == "__main__":
    from data_pipeline import run_pipeline
    _, tp = run_pipeline()
    results = run_all_models(tp)
    print("\nResults sample:")
    print(results[results["model"] == "Linear"].to_string(index=False))
