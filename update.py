import pandas as pd
from understatapi import UnderstatClient
import json
import os

CURRENT_SEASON = "2025"

def update_database():
    if not os.path.exists('data.json'):
        print("Error: data.json not found. Run setup_data.py first.")
        return
        
    with open('data.json', 'r') as f:
        existing_data = json.load(f)
        
    existing_dates = {match['date'] for match in existing_data}
    
    print("Checking Understat for new matches...")
    with UnderstatClient() as understat:
        try:
            matches = understat.team(team="Arsenal").get_match_data(season=CURRENT_SEASON)
        except Exception as e:
            print(f"Failed to connect to Understat: {e}")
            return
            
        new_matches_found = False
        
        for match in matches:
            if match.get('isResult'):
                date_str = match['datetime'].split(' ')[0]
                
                # Check if this match is missing from our database
                if date_str not in existing_dates:
                    is_home = match['h']['title'] == 'Arsenal'
                    opponent = match['a']['title'] if is_home else match['h']['title']
                    xg = float(match['xG']['h']) if is_home else float(match['xG']['a'])
                    xga = float(match['xG']['a']) if is_home else float(match['xG']['h'])
                    
                    print(f"New match found! Adding: {date_str} vs {opponent}")
                    existing_data.append({
                        "date": date_str,
                        "opponent": opponent,
                        "season": CURRENT_SEASON,
                        "xG": xg,
                        "xGA": xga
                    })
                    new_matches_found = True
                    
        if new_matches_found:
            print("Recalculating rolling averages with new data...")
            df = pd.DataFrame(existing_data)
            
            df['rolling_xG'] = df['xG'].rolling(window=10).mean().round(2)
            df['rolling_xGA'] = df['xGA'].rolling(window=10).mean().round(2)
            df['rolling_difference'] = (df['rolling_xG'] - df['rolling_xGA']).round(2)
            
            df.to_json('data.json', orient='records', indent=4)
            print("Success! Database has been updated.")
        else:
            print("No new matches found. Database is up to date.")

if __name__ == "__main__":
    update_database()