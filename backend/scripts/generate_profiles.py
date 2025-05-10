import pandas as pd

INPUT_CSV = "D:/rag-2.0/data/customers.csv"
OUTPUT_TXT = "D:/rag-2.0/data/customer_profiles.txt"

def safe_round(value, decimals):
    """Safe rounding that handles NaN values"""
    return round(value, decimals) if pd.notna(value) else "N/A"

def generate_profiles():
    try:
        # Read with explicit encoding and error handling
        df = pd.read_csv(INPUT_CSV, encoding='utf-8')
        
        # Validate input structure
        required_columns = ['Email', 'Address', 'Avatar', 'Time on App', 
                          'Time on Website', 'Length of Membership', 'Yearly Amount Spent']
        if not all(col in df.columns for col in required_columns):
            missing = [col for col in required_columns if col not in df.columns]
            raise ValueError(f"Missing required columns: {missing}")

        profiles = []
        total_rows = len(df)

        for idx, row in df.iterrows():
            try:
                username = row['Email'].split('@')[0].capitalize()
                profile = f"""
--- METADATA ---
Email: {row['Email']}
--- CONTENT ---
Customer Profile:
- Email: {row['Email']}
- Address: {row['Address']}
- Avatar: {row['Avatar']}
- Time Spent on App: {safe_round(row['Time on App'], 2)} minutes
- Time Spent on Website: {safe_round(row['Time on Website'], 2)} minutes
- Membership Duration: {safe_round(row['Length of Membership'], 1)} years
- Yearly Spending: ${safe_round(row['Yearly Amount Spent'], 2)}

Summary:
{username} ({row['Email']}) has been a member for {safe_round(row['Length of Membership'], 1)} years. They spend {safe_round(row['Time on App'], 2)} minutes in the app and {safe_round(row['Time on Website'], 2)} minutes on the website annually, with a total yearly expenditure of ${safe_round(row['Yearly Amount Spent'], 2)}.
""".strip()
                profiles.append(profile)

                # Progress feedback
                if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                    print(f"🔄 Processed {idx + 1}/{total_rows} records...")

            except Exception as row_error:
                print(f"⚠️ Error processing row {idx + 1}: {str(row_error)}")
                continue

        # Write output with error handling
        with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
            f.write("\n\n".join(profiles))

        print(f"✅ Successfully generated {len(profiles)} profiles in {OUTPUT_TXT}")
        print(f"📊 Stats: {total_rows} input rows, {len(profiles)} output profiles")

    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        raise

if __name__ == "__main__":
    generate_profiles()