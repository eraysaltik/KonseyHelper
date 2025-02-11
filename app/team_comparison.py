import requests
from datetime import datetime
from itertools import combinations

def fetch_json(url):
    """
    Fetch JSON data from a URL.
    """
    response = requests.get(url)
    response.raise_for_status()
    # Add debug print to see raw response
    #print(f"Response from {url}:")
    #print(response.text[:500])  # Print first 500 chars to avoid overwhelming output
    return response.json()

def calculate_metrics(history, use_filtered_data):
    """
    Given a list of history records (each with keys 'date' and 'elo'),
    sort them chronologically and calculate:
      - Arithmetic mean
      - Weighted average (weights = 1,2,...,n)
      - Maximum Elo reached
      - Current Elo (latest value)
      - Trend (current minus earliest Elo)
    """
    if use_filtered_data:
        # Filter history to include only entries from 2024 and 2025
        history = [entry for entry in history if entry["date"].startswith("2024") or entry["date"].startswith("2025")]
    
    if not history:
        return None
    
    # Sort history by date (assumes date in ISO format)
    sorted_history = sorted(history, key=lambda x: x["date"])
    
    # Extract Elo values as floats
    elos = [float(entry["elo"]) for entry in sorted_history]
    n = len(elos)
    
    arithmetic_mean = sum(elos) / n
    
    # Weighted average: weight=1 for oldest, weight=n for newest
    weighted_sum = sum((i+1) * elo for i, elo in enumerate(elos))
    total_weight = sum(range(1, n+1))
    weighted_average = weighted_sum / total_weight
    
    max_elo = max(elos)
    current_elo = elos[-1]
    trend = elos[-1] - elos[0]
    
    return {
        "arithmetic_mean": arithmetic_mean,
        "weighted_average": weighted_average,
        "max_elo": max_elo,
        "current_elo": current_elo,
        "trend": trend,
        "min_elo": min(elos),
        "avg_elo": sum(elos) / n,
        "median_elo": sorted(elos)[n // 2],
        "elos": elos  # include the full list if needed later
    }

def head_to_head_expected(elo_A, elo_B):
    """
    Compute the expected win probability for Player A over Player B
    using the standard Elo formula.
    
    E_A = 1 / (1 + 10^((elo_B - elo_A)/400))
    """
    expected_A = 1 / (1 + 10 ** ((elo_B - elo_A) / 400))
    return expected_A

def calculate_team_strength(metrics_list):
    """
    Calculate team strength based on multiple players' metrics.
    Returns average values for the team's metrics.
    """
    if not metrics_list:
        return None
    
    # Calculate weighted average of players' weighted averages
    total_weighted_elo = sum(m["weighted_average"] * m["weighted_average"] for m in metrics_list)
    total_weight = sum(m["weighted_average"] for m in metrics_list)
    team_weighted_average = total_weighted_elo / total_weight if total_weight != 0 else 0
    
    team_metrics = {
        "arithmetic_mean": sum(m["arithmetic_mean"] for m in metrics_list) / len(metrics_list),
        "weighted_average": team_weighted_average,
        "max_elo": max(m["max_elo"] for m in metrics_list),
        "current_elo": sum(m["current_elo"] for m in metrics_list) / len(metrics_list),
        "trend": sum(m["trend"] for m in metrics_list) / len(metrics_list),
        "min_elo": min(m["min_elo"] for m in metrics_list),
        "avg_elo": sum(m["avg_elo"] for m in metrics_list) / len(metrics_list),
        "median_elo": sorted(m["elos"] for m in metrics_list)[len(metrics_list) // 2]
    }
    return team_metrics

def find_best_team_combination(players_metrics, player_names):
    """
    Find the most balanced team combination from 8 players.
    Returns the best combination with closest to 50% win probability.
    """
    best_diff = float('inf')
    best_teams = None
    
    # Get all possible combinations of 4 players for team A
    for team_a_indices in combinations(range(8), 4):
        team_b_indices = tuple(i for i in range(8) if i not in team_a_indices)
        
        # Get metrics for both teams
        team_a_metrics = [players_metrics[i] for i in team_a_indices]
        team_b_metrics = [players_metrics[i] for i in team_b_indices]
        
        # Calculate team strengths
        team_a_strength = calculate_team_strength(team_a_metrics)
        team_b_strength = calculate_team_strength(team_b_metrics)
        
        # Calculate win probability
        expected_a = head_to_head_expected(team_a_strength["weighted_average"], 
                                         team_b_strength["weighted_average"])
        
        # Check how close it is to 50%
        diff = abs(0.5 - expected_a)
        if diff < best_diff:
            best_diff = diff
            best_teams = (
                [player_names[i] for i in team_a_indices],
                [player_names[i] for i in team_b_indices],
                expected_a
            )
    
    return best_teams

def calculate_series_probabilities(p_win):
    """
    Calculate probabilities for different series outcomes where all 3 matches are played.
    p_win: probability of winning a single game
    Returns: dict of probabilities for each possible series score (1-2, 2-1, 3-0, 0-3)
    """
    # Probability of losing a single game
    p_lose = 1 - p_win
    
    # Calculate probabilities for each possible series outcome
    p_3_0 = p_win * p_win * p_win           # Win-Win-Win
    p_2_1 = 3 * p_win * p_win * p_lose      # Three ways to get 2 wins, 1 loss
    p_1_2 = 3 * p_win * p_lose * p_lose     # Three ways to get 1 win, 2 losses
    p_0_3 = p_lose * p_lose * p_lose        # Loss-Loss-Loss
    
    return {
        "3-0": p_3_0,
        "2-1": p_2_1,
        "1-2": p_1_2,
        "0-3": p_0_3
    }

def main():
    # Player names and URLs for the eight players' Elo histories
    players = [
        ("Saltik", "https://www.aoe2insights.com/user/2739525/elo-history/3/"),
        ("Eren", "https://www.aoe2insights.com/user/2471692/elo-history/3/"),
        ("Sencer", "https://www.aoe2insights.com/user/3915596/elo-history/3/"),
        ("Dinc", "https://www.aoe2insights.com/user/4970559/elo-history/3/"),
        ("Salim", "https://www.aoe2insights.com/user/1444557/elo-history/3/"),
        ("Emre", "https://www.aoe2insights.com/user/2079039/elo-history/3/"),
        ("Kaan", "https://www.aoe2insights.com/user/12397390/elo-history/3/"),
        ("Hakan", "https://www.aoe2insights.com/user/1528769/elo-history/3/"),
        ("JR", "https://www.aoe2insights.com/user/2943236/elo-history/3/"),
        ("Yahya", "https://www.aoe2insights.com/user/3138965/elo-history/3/"),
        ("Kursad", "https://www.aoe2insights.com/user/3545515/elo-history/3/"),
        ("Kuzen", "https://www.aoe2insights.com/user/3778162/elo-history/3/"),
        ("Mustafa", "https://www.aoe2insights.com/user/5094125/elo-history/3/"),
        ("Berkay", "https://www.aoe2insights.com/user/1491145/elo-history/3/")
    ]
    
    # Ask user if they want to use filtered data
    use_filtered_data = input("Do you want to use only 2024 and 2025 data? (yes/no): ").strip().lower() == 'yes'
    
    # Ask user which mode they want to use
    mode = input("\nDo you want to:\n1. Compare two specific teams\n2. Find the most balanced teams\nEnter 1 or 2: ").strip()
    
    # Show all available players
    print("\nAvailable players:")
    for i, (name, _) in enumerate(players):
        print(f"{i}: {name}")
    
    if mode == "2":
        # Select 8 players for balanced teams
        print("\nSelect 8 players for balanced team matching (enter 8 indices separated by commas):")
        selected_indices = list(map(int, input("Selected players: ").split(',')))
        
        if len(selected_indices) != 8:
            print("Error: Please select exactly 8 players")
            return
        
        # Filter players list to only include selected players
        selected_players = [players[i] for i in selected_indices]
    else:
        selected_players = players
    
    all_metrics = []
    player_names = []
    
    # Fetch data and calculate metrics for selected players
    for i, (name, url) in enumerate(selected_players):
        try:
            data = fetch_json(url)
            history = [{"date": date, "elo": elo} for date, elo in data.items()]
            metrics = calculate_metrics(history, use_filtered_data)
            if metrics:
                all_metrics.append(metrics)
                player_names.append(name)
                #print(f"\n{name} history entries: {len(history)}")
            else:
                print(f"\nWarning: No data for {name}")
                return
        except Exception as e:
            print(f"Error fetching data for {name}: {str(e)}")
            return

    if mode == "1":
        # Manual team selection
        print("\nSelect players for Team A (enter indices separated by commas):")
        for i, name in enumerate(player_names):
            print(f"{i}: {name}")
        team_a_indices = list(map(int, input("Team A: ").split(',')))
        
        print("\nSelect players for Team B (enter indices separated by commas):")
        for i, name in enumerate(player_names):
            print(f"{i}: {name}")
        team_b_indices = list(map(int, input("Team B: ").split(',')))
        
        team_a_metrics = [all_metrics[i] for i in team_a_indices]
        team_b_metrics = [all_metrics[i] for i in team_b_indices]
        team_a_names = [player_names[i] for i in team_a_indices]
        team_b_names = [player_names[i] for i in team_b_indices]
    
    else:
        # Find most balanced teams from selected players
        print("\nFinding the most balanced team combination from selected players...")
        best_teams = find_best_team_combination(all_metrics, player_names)
        team_a_names, team_b_names = best_teams[0], best_teams[1]
        
        # Get metrics for the balanced teams
        team_a_indices = [player_names.index(name) for name in team_a_names]
        team_b_indices = [player_names.index(name) for name in team_b_names]
        team_a_metrics = [all_metrics[i] for i in team_a_indices]
        team_b_metrics = [all_metrics[i] for i in team_b_indices]
        
        print("\nMost balanced team combination found:")
        print("Team A:", ", ".join(team_a_names))
        print("Team B:", ", ".join(team_b_names))
        print(f"Expected win probability: {best_teams[2]*100:.1f}% vs {(1-best_teams[2])*100:.1f}%")

    # Print individual player metrics
    print("\nTeam A Players:")
    for name, metrics in zip(team_a_names, team_a_metrics):
        print(f"\n{name}:")
        print(f"  Current Elo: {metrics['current_elo']:.2f}")
        print(f"  Weighted Average: {metrics['weighted_average']:.2f}")
        print(f"  Maximum Elo: {metrics['max_elo']:.2f}")
        print(f"  Trend: {metrics['trend']:.2f}")
        print(f"  Number of Entries: {len(metrics['elos'])}")

    print("\nTeam B Players:")
    for name, metrics in zip(team_b_names, team_b_metrics):
        print(f"\n{name}:")
        print(f"  Current Elo: {metrics['current_elo']:.2f}")
        print(f"  Weighted Average: {metrics['weighted_average']:.2f}")
        print(f"  Maximum Elo: {metrics['max_elo']:.2f}")
        print(f"  Trend: {metrics['trend']:.2f}")
        print(f"  Number of Entries: {len(metrics['elos'])}")
    
    # Calculate team strengths using weighted averages
    team_a_strength = calculate_team_strength(team_a_metrics)
    team_b_strength = calculate_team_strength(team_b_metrics)
    
    print("\nTeam Comparisons (based on weighted averages):")
    print(f"\nTeam A Average Weighted Elo: {team_a_strength['weighted_average']:.2f}")
    print(f"Team B Average Weighted Elo: {team_b_strength['weighted_average']:.2f}")
    
    # Head-to-head expected outcome using weighted averages
    expected_a = head_to_head_expected(team_a_strength["weighted_average"], 
                                     team_b_strength["weighted_average"])
    expected_b = 1 - expected_a
    
    print("\nTeam Head-to-Head Expected Outcome (using weighted averages):")
    print(f"  Team A expected win probability: {expected_a * 100:.1f}%")
    print(f"  Team B expected win probability: {expected_b * 100:.1f}%")

    # Calculate and display series probabilities
    print("\nThree-Match Series Probabilities (all matches played):")
    series_probs = calculate_series_probabilities(expected_a)
    
    print(f"\nTeam A winning 3-0: {series_probs['3-0']*100:.1f}%")
    print(f"Team A winning 2-1: {series_probs['2-1']*100:.1f}%")
    print(f"Team B winning 2-1: {series_probs['1-2']*100:.1f}%")
    print(f"Team B winning 3-0: {series_probs['0-3']*100:.1f}%")
    
    # Summary of winning the series
    team_a_series_win = series_probs['3-0'] + series_probs['2-1']
    team_b_series_win = series_probs['0-3'] + series_probs['1-2']
    print(f"\nOverall series win probability:")
    print(f"Team A: {team_a_series_win*100:.1f}%")
    print(f"Team B: {team_b_series_win*100:.1f}%")

if __name__ == "__main__":
    main()
