import pandas as pd
import numpy as np
import ast

# Load the dataset
df = pd.read_csv('Final_CCS_Measurement_with_Static_Analysis.csv')

# Clean and prepare the data for analysis
# Filter out rows where static analysis failed (e.g., 'Missing APK' or 'Analysis Error')
# In this specific file, Target_SDK might have string values like 'Missing APK'
valid_df = df[pd.to_numeric(df['Target_SDK'], errors='coerce').notnull()].copy()
valid_df['Target_SDK'] = valid_df['Target_SDK'].astype(int)
valid_df['Risk_Score_10'] = pd.to_numeric(valid_df['Risk_Score_10'], errors='coerce')
valid_df['Rating'] = pd.to_numeric(valid_df['Rating'], errors='coerce')

# Basic Stats
total_apps = len(df)
analyzed_apps = len(valid_df)

print(f"Total Apps: {total_apps}, Successfully Analyzed: {analyzed_apps}")

# 1. Target SDK Distribution
sdk_counts = valid_df['Target_SDK'].value_counts().sort_index(ascending=False)
print("\n--- Target SDK Distribution ---")
print(sdk_counts)

# 2. Risk Score Analysis
avg_risk = valid_df['Risk_Score_10'].mean()
high_risk = len(valid_df[valid_df['Risk_Score_10'] >= 7])
print(f"\n--- Risk Score Analysis ---")
print(f"Average Risk Score: {avg_risk:.2f}/10")
print(f"Apps with High Risk Score (>= 7): {high_risk} ({high_risk/analyzed_apps*100:.1f}%)")

# 3. Tracker Analysis
print("\n--- Embedded Trackers Analysis ---")
tracker_counts = {}
for trackers in valid_df['Embedded_Trackers'].dropna():
    if trackers != "None Detected":
        for t in [x.strip() for x in trackers.split(',')]:
            tracker_counts[t] = tracker_counts.get(t, 0) + 1

# Sort trackers by frequency
sorted_trackers = sorted(tracker_counts.items(), key=lambda item: item[1], reverse=True)
for k, v in sorted_trackers:
    print(f"{k}: {v} apps ({v/analyzed_apps*100:.1f}%)")

# 4. Permission Analysis
bg_loc_count = valid_df['Has_Background_Loc'].sum()
fine_loc_count = valid_df['Has_Fine_Loc'].sum()
print("\n--- Permission Analysis ---")
print(f"Has Background Location: {bg_loc_count} ({bg_loc_count/analyzed_apps*100:.1f}%)")
print(f"Has Fine Location: {fine_loc_count} ({fine_loc_count/analyzed_apps*100:.1f}%)")

# 5. Category Analysis (Top 5 Vulnerable Categories)
print("\n--- Top Categories ---")
print(valid_df['Category'].value_counts().head(5))

# 6. Installs Impact
# Convert "10,000,000+" to numbers for a rough estimate of total impacted users
def parse_installs(install_str):
    if pd.isna(install_str) or install_str in ['Unknown', 'Error', 'Delisted']:
        return 0
    clean_str = install_str.replace(',', '').replace('+', '')
    try:
        return int(clean_str)
    except:
        return 0

valid_df['Min_Installs_Numeric'] = valid_df['Installs'].apply(parse_installs)
total_impacted_users = valid_df['Min_Installs_Numeric'].sum()
print(f"\n--- Total Impacted Users (Min Estimate) ---")
print(f"{total_impacted_users:,}")