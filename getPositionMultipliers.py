import requests
from bs4 import BeautifulSoup
import pandas as pd

def extract_card_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    position_heading = soup.find('h4', string='Win rate by position')
    if position_heading:
        parent_div = position_heading.find_parent('div', class_='mb-4')
        if parent_div:
            card_bodies = parent_div.find_all('div', class_='card-body text-end')
            
            if len(card_bodies) >= 2:
                flank_stats = []
                pocket_stats = []
                
                for i, card_body in enumerate([card_bodies[0], card_bodies[1]]):
                    # Extract win rate (remove the % symbol and convert to float)
                    win_rate = float(card_body.find('span', class_='h3').text.strip().replace('%', ''))
                    
                    # Extract matches and wins from the spans with font-size: 1.2em
                    numbers = [int(span.text.strip()) for span in card_body.find_all('span', style='font-size: 1.2em')]
                    total_matches, total_wins = numbers
                    
                    if i == 0:
                        flank_stats = [win_rate, total_matches, total_wins]
                    else:
                        pocket_stats = [win_rate, total_matches, total_wins]
                
                return flank_stats, pocket_stats
    return None

def calculate_position_multipliers(flank_stats, pocket_stats):
    # Unpack stats
    flank_winrate, flank_matches, flank_wins = flank_stats
    pocket_winrate, pocket_matches, pocket_wins = pocket_stats
    
    # Calculate position preference factor (0 to 1)
    total_matches = flank_matches + pocket_matches
    if total_matches == 0:
        return {
            'flank_multiplier': 1.0,
            'pocket_multiplier': 1.0,
            'flank_winrate': 0,
            'pocket_winrate': 0,
            'flank_matches': 0,
            'pocket_matches': 0,
            'flank_wins': 0,
            'pocket_wins': 0
        }
    
    flank_preference = flank_matches / total_matches
    pocket_preference = pocket_matches / total_matches
    
    # Enhanced position preference impact based on thresholds
    preference_multiplier = 1.0
    if max(flank_preference, pocket_preference) > 0.75:
        preference_multiplier = 1.5
    elif max(flank_preference, pocket_preference) > 0.65:
        preference_multiplier = 1.2
    
    # Calculate performance factor (-1 to 1)
    winrate_difference = (flank_winrate - pocket_winrate) / 100
    
    # Enhanced winrate impact based on thresholds
    winrate_multiplier = 1.0
    if abs(winrate_difference) > 0.15:
        winrate_multiplier = 2
    elif abs(winrate_difference) > 0.10:
        winrate_multiplier = 1.8
    elif abs(winrate_difference) > 0.06:
        winrate_multiplier = 1.5
    
    # Revised experience weight calculation for 60-game maximum
    # Now using a more aggressive curve:
    # 10 games = 0.4
    # 20 games = 0.7
    # 30 games = 0.85
    # 40 games = 0.95
    # 50+ games = 1.0
    experience_weight = min(total_matches / 50, 1.0)  # Linear up to 50 games
    if total_matches < 40:
        experience_weight = 0.4 + (total_matches / 40) * 0.55  # More aggressive curve for fewer games
    
    base_adjustment = 0.15 * experience_weight
    
    # Combine preference and performance factors with their multipliers
    flank_multiplier = 1.0 + base_adjustment * (
        0.6 * (flank_preference - 0.5) * preference_multiplier +
        0.4 * winrate_difference * winrate_multiplier
    )
    
    pocket_multiplier = 1.0 + base_adjustment * (
        0.6 * (pocket_preference - 0.5) * preference_multiplier +
        -0.4 * winrate_difference * winrate_multiplier
    )
    
    return {
        'flank_multiplier': flank_multiplier,
        'pocket_multiplier': pocket_multiplier,
        'flank_winrate': flank_winrate,
        'pocket_winrate': pocket_winrate,
        'flank_matches': flank_matches,
        'pocket_matches': pocket_matches,
        'flank_wins': flank_wins,
        'pocket_wins': pocket_wins
    }

def get_position_metrics(aoe2insights_id, base_elo):
    """
    Main function to get all position-related metrics for a player
    
    Args:
        aoe2insights_id (int): Player's AOE2Insights ID
        base_elo (int): Player's base ELO rating
    
    Returns:
        dict: Dictionary containing all position metrics and multipliers
        None: If data couldn't be retrieved
    """
    url = f'https://www.aoe2insights.com/user/{aoe2insights_id}/stats/0/'
    result = extract_card_data(url)
    
    if result:
        flank_stats, pocket_stats = result
        return calculate_position_multipliers(flank_stats, pocket_stats)
    return None

def get_position_metrics_from_csv(player_id):
    """
    Get position metrics from CSV data instead of web scraping
    Uses last 60 matches or all matches if less than 60
    """
    try:
        df = pd.read_csv('total_matches_new.csv')
        # Sort by match time to get the most recent matches first
        df['Match_Time'] = pd.to_datetime(df['Match_Time'], 
                                        format="%b. %d, %Y, %I:%M %p",
                                        errors='coerce')
        df = df.sort_values('Match_Time', ascending=False)
        
        # Get player matches
        player_matches = df[df['MainPlayer_ID'] == player_id]
        
        if len(player_matches) == 0:
            return None
            
        # Take only last 60 matches (or all if less than 60)
        player_matches = player_matches.head(60)
            
        # Calculate flank stats
        flank_matches = player_matches[player_matches['MainPlayer_Position'] == 'Flank']
        flank_total = len(flank_matches)
        flank_wins = len(flank_matches[flank_matches['MainPlayer_isWon'] == 1])
        flank_winrate = (flank_wins / flank_total * 100) if flank_total > 0 else 0
        
        # Calculate pocket stats
        pocket_matches = player_matches[player_matches['MainPlayer_Position'] == 'Pocket']
        pocket_total = len(pocket_matches)
        pocket_wins = len(pocket_matches[pocket_matches['MainPlayer_isWon'] == 1])
        pocket_winrate = (pocket_wins / pocket_total * 100) if pocket_total > 0 else 0
        
        # Calculate multipliers using existing function
        multipliers = calculate_position_multipliers(
            [flank_winrate, flank_total, flank_wins],
            [pocket_winrate, pocket_total, pocket_wins]
        )
        
        # Return complete position data
        return {
            'flank_multiplier': multipliers['flank_multiplier'],
            'pocket_multiplier': multipliers['pocket_multiplier'],
            'flank_matches': flank_total,
            'pocket_matches': pocket_total,
            'flank_winrate': flank_winrate,
            'pocket_winrate': pocket_winrate
        }
        
    except Exception as e:
        print(f"Error processing CSV data for player {player_id}: {str(e)}")
        return None

# # Example usage
# url = 'https://www.aoe2insights.com/user/1444557/stats/0/'
# result = extract_card_data(url)
# if result:
#     flank_stats, pocket_stats = result
#     base_elo = 1200
#     position_metrics = calculate_position_multipliers(flank_stats, pocket_stats, base_elo)
    
#     print(f"Base Elo: {base_elo}")
#     print(f"\nFlank Stats:")
#     print(f"Win Rate: {flank_stats[0]}%")
#     print(f"Total Matches: {flank_stats[1]}")
#     print(f"Position Multiplier: {position_metrics['flank_multiplier']:.3f}")
#     print(f"Position-Adjusted Elo: {int(base_elo * position_metrics['flank_multiplier'])}")
    
#     print(f"\nPocket Stats:")
#     print(f"Win Rate: {pocket_stats[0]}%")
#     print(f"Total Matches: {pocket_stats[1]}")
#     print(f"Position Multiplier: {position_metrics['pocket_multiplier']:.3f}")
#     print(f"Position-Adjusted Elo: {int(base_elo * position_metrics['pocket_multiplier'])}")
# else:
#     print("Element not found in the HTML source.")