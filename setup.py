import pandas as pd
from understatapi import UnderstatClient
import os

SEASONS = ["2023", "2024", "2025"]

def bootstrap_database():
    all_matches = []
    
    # The UnderstatClient automatically handles security headers and data parsing
    with UnderstatClient() as understat:
        for season in SEASONS:
            print(f"Fetching {season} season history...")
            try:
                matches = understat.team(team="Arsenal").get_match_data(season=season)
                
                for match in matches:
                    # 'isResult' is True if the game has actually been played
                    if match.get('isResult'):
                        is_home = match['h']['title'] == 'Arsenal'
                        opponent = match['a']['title'] if is_home else match['h']['title']
                        
                        xg = float(match['xG']['h']) if is_home else float(match['xG']['a'])
                        xga = float(match['xG']['a']) if is_home else float(match['xG']['h'])
                        date_str = match['datetime'].split(' ')[0]
                        
                        all_matches.append({
                            "date": date_str,
                            "opponent": opponent,
                            "season": season,
                            "xG": xg,
                            "xGA": xga
                        })
            except Exception as e:
                print(f"Error fetching {season}: {e}")
                
    print("Calculating historical rolling averages...")
    df = pd.DataFrame(all_matches)
    
    if not df.empty:
        df['rolling_xG'] = df['xG'].rolling(window=10).mean().round(2)
        df['rolling_xGA'] = df['xGA'].rolling(window=10).mean().round(2)
        df['rolling_difference'] = (df['rolling_xG'] - df['rolling_xGA']).round(2)
        
        df.to_json('data.json', orient='records', indent=4)
        print("Success! Historical database created as data.json")
    else:
        print("Error: No data fetched.")

if __name__ == "__main__":
    bootstrap_database()