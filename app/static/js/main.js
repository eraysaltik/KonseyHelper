let playerMetrics = [];
let currentMode = null;

$(document).ready(function() {
    $('#loadData').click(loadPlayerData);
    $('#compareTeams').click(() => setMode('compare'));
    $('#findBalanced').click(() => setMode('balanced'));
    $('#calculateResults').click(calculateResults);
});

function loadPlayerData() {
    const filterValue = $('#dataFilter').val();
    
    $.ajax({
        url: '/get_player_metrics',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ filterType: filterValue }),
        success: function(data) {
            playerMetrics = data;
            displayMetricsTable();
            $('#modeSelection').show();
        },
        error: function(xhr) {
            alert('Error loading player data: ' + xhr.responseJSON.error);
        }
    });
}

function displayMetricsTable() {
    const table = $('#metricsTable').DataTable({
        destroy: true,
        pageLength: 20,
        data: playerMetrics,
        columns: [
            { data: 'name' },
            { data: 'current_elo', render: formatNumber },
            { data: 'weighted_average', render: formatNumber },
            { data: 'max_elo', render: formatNumber },
            { data: 'min_elo', render: formatNumber },
            { data: 'avg_elo', render: formatNumber },
            { data: 'median_elo', render: formatNumber },
            { data: 'trend', render: formatNumber }
        ]
    });
    
    $('#playerTable').show();
}

function setMode(mode) {
    currentMode = mode;
    $('#manualSelection, #balancedSelection').hide();
    
    if (mode === 'compare') {
        populateTeamSelects();
        $('#manualSelection').show();
    } else {
        populateBalancedSelect();
        $('#balancedSelection').show();
    }
    
    $('#teamSelection').show();
}

function populateTeamSelects() {
    const options = playerMetrics.map(p => 
        `<option value="${p.name}">${p.name} (${p.weighted_average.toFixed(0)})</option>`
    ).join('');
    
    $('#teamASelect, #teamBSelect').html(options);
}

function populateBalancedSelect() {
    const options = playerMetrics.map(p => 
        `<option value="${p.name}">${p.name} (${p.weighted_average.toFixed(0)})</option>`
    ).join('');
    
    $('#balancedPlayersSelect').html(options);
}

function calculateResults() {
    if (currentMode === 'compare') {
        const teamA = $('#teamASelect').val();
        const teamB = $('#teamBSelect').val();
        
        if (teamA.length !== 4 || teamB.length !== 4) {
            alert('Please select exactly 4 players for each team');
            return;
        }
        
        compareTeams(teamA, teamB);
    } else {
        const selectedPlayers = $('#balancedPlayersSelect').val();
        
        if (selectedPlayers.length !== 8) {
            alert('Please select exactly 8 players');
            return;
        }
        
        findBalancedTeams(selectedPlayers);
    }
}

function compareTeams(teamA, teamB) {
    $.ajax({
        url: '/compare_teams',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            teamA,
            teamB,
            allMetrics: playerMetrics
        }),
        success: displayResults,
        error: function(xhr) {
            alert('Error calculating results: ' + xhr.responseJSON.error);
        }
    });
}

function findBalancedTeams(selectedPlayers) {
    $.ajax({
        url: '/find_balanced_teams',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            selectedPlayers,
            allMetrics: playerMetrics
        }),
        success: displayBalancedResults,
        error: function(xhr) {
            alert('Error finding balanced teams: ' + xhr.responseJSON.error);
        }
    });
}

function displayResults(data) {
    const html = `
        <h4>Team Strengths</h4>
        <p>Team A: ${data.teamAStrength.weighted_average.toFixed(0)}</p>
        <p>Team B: ${data.teamBStrength.weighted_average.toFixed(0)}</p>
        
        <h4>Single Match Win Probabilities</h4>
        <p>Team A: ${(data.expectedA * 100).toFixed(1)}%</p>
        <p>Team B: ${((1 - data.expectedA) * 100).toFixed(1)}%</p>
        
        <h4>Best of 3 Series Probabilities</h4>
        <p>Team A 3-0: ${(data.seriesProbabilities['3-0'] * 100).toFixed(1)}%</p>
        <p>Team A 2-1: ${(data.seriesProbabilities['2-1'] * 100).toFixed(1)}%</p>
        <p>Team B 2-1: ${(data.seriesProbabilities['1-2'] * 100).toFixed(1)}%</p>
        <p>Team B 3-0: ${(data.seriesProbabilities['0-3'] * 100).toFixed(1)}%</p>

        <h4>Overall Series Win Probability</h4>
        <p>Team A: ${((data.seriesProbabilities['3-0'] + data.seriesProbabilities['2-1']) * 100).toFixed(1)}%</p>
        <p>Team B: ${((data.seriesProbabilities['0-3'] + data.seriesProbabilities['1-2']) * 100).toFixed(1)}%</p>
    `;
    
    $('#resultsContent').html(html);
    $('#results').show();
}

function displayBalancedResults(data) {
    const html = `
        <h4>Most Balanced Teams</h4>
        <p>Team A: ${data.teamA.join(', ')}</p>
        <p>Team B: ${data.teamB.join(', ')}</p>
        <p>Win Probability: ${(data.winProbability * 100).toFixed(1)}% vs ${((1 - data.winProbability) * 100).toFixed(1)}%</p>
    `;
    
    $('#resultsContent').html(html);
    $('#results').show();
}

function formatNumber(num) {
    return num.toFixed(0);
} 