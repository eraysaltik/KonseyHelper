import pandas as pd
from datetime import datetime, timedelta

def get_recent_match_statistics(player_id):
    """
    Get match statistics for the last 60 days
    """
    try:
        df = pd.read_csv('total_matches_new.csv')
        
        # Clean up the date string first (remove the period after p.m./a.m.)
        df['Match_Time'] = df['Match_Time'].str.replace('p.m.', 'PM').str.replace('a.m.', 'AM')
        
        # Convert Match_Time to datetime using a more flexible parser
        df['Match_Time'] = pd.to_datetime(df['Match_Time'], format='mixed')
        
        # Get most recent date and calculate cutoff
        most_recent_date = df['Match_Time'].max()
        cutoff_date = most_recent_date - timedelta(days=60)
        
        # Filter matches for player and last 60 days
        recent_matches = df[
            (df['MainPlayer_ID'] == player_id) & 
            (df['Match_Time'] >= cutoff_date)
        ].copy()
        
        if len(recent_matches) == 0:
            return {
                'total_matches': 0,
                'win_rate': 0,
                'recent_performance_multiplier': 1.0
            }
        
        total_matches = len(recent_matches)
        wins = len(recent_matches[recent_matches['MainPlayer_isWon'] == 1])
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        # Calculate performance multiplier
        performance_multiplier = calculate_recent_performance_multiplier(recent_matches)
        
        return {
            'total_matches': total_matches,
            'win_rate': win_rate,
            'recent_performance_multiplier': performance_multiplier
        }
        
    except Exception as e:
        print(f"Error processing match data for player {player_id}: {str(e)}")
        return None

def calculate_recent_performance_multiplier(recent_matches):
    """
    Calculate performance multiplier based on last 60 days matches
    Returns a multiplier between 0.8 and 1.2 (±20%)
    """
    try:
        if len(recent_matches) == 0:
            return 1.0
            
        # Sort matches by time for time-weighted win rate calculation
        recent_matches = recent_matches.sort_values('Match_Time')
        total_matches = len(recent_matches)
        
        # Calculate time-weighted wins
        most_recent_date = recent_matches['Match_Time'].max()
        weights = []
        
        for match_date in recent_matches['Match_Time']:
            days_ago = (most_recent_date - match_date).days
            # Weight decreases linearly from 1.0 to 0.5 over 60 days
            weight = 1.0 - (days_ago / 120)  # 60 days = 0.5 weight
            weights.append(weight)
            
        # Calculate weighted win rate
        wins = recent_matches['MainPlayer_isWon'] == 1
        weighted_wins = sum(w * v for w, v in zip(weights, wins))
        weighted_winrate = (weighted_wins / sum(weights)) * 100
        
        # Calculate activity score (0 to 1) based on number of matches
        # Assuming 30 matches in 60 days is maximum activity
        activity_score = min(total_matches / 30, 1.0)
        
        # Normalize win rate impact (-1 to 1)
        winrate_impact = (weighted_winrate - 50) / 50  # Center around 50%
        
        # Combine factors with weights
        performance_score = (
            0.3 * activity_score +  # 30% weight for activity
            0.7 * winrate_impact    # 70% weight for win rate
        )
        
        # Convert to multiplier range (0.9 to 1.1)
        multiplier = 1.0 + (performance_score * 0.1)
        
        return max(0.8, min(1.2, multiplier))
        
    except Exception as e:
        print(f"Error calculating recent performance multiplier: {str(e)}")
        return 1.0 