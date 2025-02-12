from flask import render_template, jsonify, request
from app import app
from app.team_comparison import (fetch_json, calculate_metrics, calculate_team_strength,
                               head_to_head_expected, find_best_team_combination,
                               calculate_series_probabilities)

PLAYERS = [
    {
        "name": "Saltik",
        "url": "https://www.aoe2insights.com/user/13028522/elo-history/3/"
    },
    {
        "name": "Eren",
        "url": "https://www.aoe2insights.com/user/2471692/elo-history/3/"
    },
    {
        "name": "Sencer",
        "url": "https://www.aoe2insights.com/user/3915596/elo-history/3/"
    },
    {
        "name": "Dinc",
        "url": "https://www.aoe2insights.com/user/4970559/elo-history/3/"
    },
    {
        "name": "Salim",
        "url": "https://www.aoe2insights.com/user/1444557/elo-history/3/"
    },
    {
        "name": "Emre",
        "url": "https://www.aoe2insights.com/user/2079039/elo-history/3/"
    },
    {
        "name": "Kaan",
        "url": "https://www.aoe2insights.com/user/12397390/elo-history/3/"
    },
    {
        "name": "Hakan",
        "url": "https://www.aoe2insights.com/user/1528769/elo-history/3/"
    },
    {
        "name": "JR",
        "url": "https://www.aoe2insights.com/user/2943236/elo-history/3/"
    },
    {
        "name": "Yahya",
        "url": "https://www.aoe2insights.com/user/3138965/elo-history/3/"
    },
    {
        "name": "Kursad",
        "url": "https://www.aoe2insights.com/user/3545515/elo-history/3/"
    },
    {
        "name": "Kuzen",
        "url": "https://www.aoe2insights.com/user/3778162/elo-history/3/"
    }
]

@app.route('/')
def index():
    return render_template('index.html', players=PLAYERS)

@app.route('/get_player_metrics', methods=['POST'])
def get_player_metrics():
    data = request.get_json()
    filter_type = data.get('filterType', 'all')
    
    players_metrics = []
    for player in PLAYERS:
        try:
            raw_data = fetch_json(player['url'])
            history = [{"date": date, "elo": elo} for date, elo in raw_data.items()]
            metrics = calculate_metrics(history, filter_type)
            if metrics:
                metrics['name'] = player['name']
                players_metrics.append(metrics)
        except Exception as e:
            return jsonify({'error': f"Error fetching data for {player['name']}: {str(e)}"}), 500
    
    return jsonify(players_metrics)

@app.route('/compare_teams', methods=['POST'])
def compare_teams():
    data = request.get_json()
    team_a = data.get('teamA', [])
    team_b = data.get('teamB', [])
    all_metrics = data.get('allMetrics', [])
    
    team_a_metrics = [m for m in all_metrics if m['name'] in team_a]
    team_b_metrics = [m for m in all_metrics if m['name'] in team_b]
    
    team_a_strength = calculate_team_strength(team_a_metrics)
    team_b_strength = calculate_team_strength(team_b_metrics)
    
    expected_a = head_to_head_expected(team_a_strength["weighted_average"],
                                     team_b_strength["weighted_average"])
    series_probs = calculate_series_probabilities(expected_a)
    
    return jsonify({
        'teamAStrength': team_a_strength,
        'teamBStrength': team_b_strength,
        'expectedA': expected_a,
        'seriesProbabilities': series_probs
    })

@app.route('/find_balanced_teams', methods=['POST'])
def find_balanced_teams():
    data = request.get_json()
    selected_players = data.get('selectedPlayers', [])
    all_metrics = data.get('allMetrics', [])
    
    selected_metrics = [m for m in all_metrics if m['name'] in selected_players]
    player_names = [m['name'] for m in selected_metrics]
    
    best_teams = find_best_team_combination(selected_metrics, player_names)
    
    return jsonify({
        'teamA': best_teams[0],
        'teamB': best_teams[1],
        'winProbability': best_teams[2]
    })
