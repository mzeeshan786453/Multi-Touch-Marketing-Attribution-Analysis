# =============================================================
# main.py
# Run this first before launching the dashboard.
# It processes the data, runs all models, and saves outputs.
#
# Usage:
#   python main.py
# =============================================================

import os

def main():
    print("=" * 55)
    print("  TEYZIX CORE – Marketing Attribution System")
    print("  Task DA-2")
    print("=" * 55)

    # Make sure output folders exist
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # Step 1: Run data pipeline
    print("\nSTEP 1: Loading data and generating touchpoints...")
    from data_pipeline import run_pipeline
    cat_df, tp = run_pipeline()

    # Step 2: Run attribution models
    print("\nSTEP 2: Running attribution models...")
    from attribution_models import run_all_models
    results = run_all_models(tp)

    # Step 3: Generate report
    print("\nSTEP 3: Generating insights report...")
    from generate_report import save_report
    save_report(tp, results)

    # Done
    print("\n" + "=" * 55)
    print("  ALL DONE!")
    print("=" * 55)
    print("\nOutput files created:")
    print("  outputs/touchpoints.csv")
    print("  outputs/category_tree_enriched.csv")
    print("  outputs/attribution_results.csv")
    print("  reports/marketing_insights_report.txt")
    print("\nTo launch the dashboard, run:")
    print("  streamlit run dashboard.py")
    print("\nThen open: http://localhost:8501")


if __name__ == "__main__":
    main()
