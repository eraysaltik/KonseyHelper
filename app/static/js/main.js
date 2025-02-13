let playerMetrics = [];
let currentMode = null;

$(document).ready(function() {
    $('#loadData').click(loadPlayerData);
    $('#compareTeams').click(() => setMode('compare'));
    $('#findBalanced').click(() => setMode('balanced'));
    $('#calculateResults, #calculateBalancedResults').click(calculateResults);
    
    // Automatically load data when page loads
    loadPlayerData();
});

function loadPlayerData() {
    const filterValue = $('#dataFilter').val();
    
    // Show loading indicator
    $('#loadingIndicator').show();
    $('#loadData').prop('disabled', true);
    
    $.ajax({
        url: '/get_player_metrics',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ filterType: filterValue }),
        success: function(data) {
            playerMetrics = data;
            displayMetricsTable();
            $('#modeSelection').show();
            // Hide loading indicator
            $('#loadingIndicator').hide();
            $('#loadData').prop('disabled', false);
        },
        error: function(xhr) {
            alert('Error loading player data: ' + xhr.responseJSON.error);
            // Hide loading indicator
            $('#loadingIndicator').hide();
            $('#loadData').prop('disabled', false);
        }
    });
}

function displayMetricsTable() {
    if ($.fn.DataTable.isDataTable('#metricsTable')) {
        $('#metricsTable').DataTable().destroy();
    }
    
    // Clear existing table content
    $('#metricsTable tbody').empty();
    
    $('#metricsTable').DataTable({
        data: playerMetrics,
        columns: [
            { data: 'name' },
            { data: 'current_elo', render: formatNumber },
            { data: 'weighted_average', render: formatNumber },
            { data: 'max_elo', render: formatNumber },
            { data: 'avg_elo', render: formatNumber },
            { data: 'median_elo', render: formatNumber },
            { data: 'recent_matches', render: (data) => data || 'N/A' },
            { data: 'recent_winrate', render: (data) => data ? data.toFixed(1) + '%' : 'N/A' },
            { data: 'recent_performance_multiplier', render: (data) => data ? data.toFixed(3) : 'N/A' },
            { data: 'flank_multiplier', render: (data) => data ? data.toFixed(3) : 'N/A' },
            { data: 'flank_matches', render: (data) => data || 'N/A' },
            { data: 'flank_winrate', render: (data) => data ? data.toFixed(1) + '%' : 'N/A' },
            { data: 'pocket_multiplier', render: (data) => data ? data.toFixed(3) : 'N/A' },
            { data: 'pocket_matches', render: (data) => data || 'N/A' },
            { data: 'pocket_winrate', render: (data) => data ? data.toFixed(1) + '%' : 'N/A' }
        ],
        pageLength: 20,
        responsive: true,
        order: [[2, 'desc']], // Sort by weighted_average (column index 2) by default
        dom: 'Bfrtip'
    });
    
    $('#playerTable').show();
}

function setMode(mode) {
    currentMode = mode;
    
    // Hide all mode-specific divs first
    $('#teamSelection').hide();
    $('#balancedTeamsSelection').hide();
    
    // Clear and hide results
    $('#resultsContent').empty();
    $('#results').hide();
    
    if (mode === 'compare') {
        $('#teamSelection').show();
        setupTeamSelectors();
    } else if (mode === 'balanced') {
        $('#balancedTeamsSelection').show();
        setupBalancedTeamSelector();
    }
}

function setupTeamSelectors() {
    const playerOptions = playerMetrics.map(p => 
        `<option value="${p.name}">${p.name}</option>`
    ).join('');
    
    // Setup Team A
    const teamAContainer = $('#teamAContainer').empty();
    for (let i = 0; i < 4; i++) {
        const playerSelection = $(`
            <div class="player-selection mb-2">
                <select class="form-select player-select">${playerOptions}</select>
                <select class="form-select position-select mt-1" style="display: none">
                    <option value="flank">Flank</option>
                    <option value="pocket">Pocket</option>
                </select>
            </div>
        `);
        teamAContainer.append(playerSelection);
    }
    
    // Setup Team B (same structure)
    const teamBContainer = $('#teamBContainer').empty();
    for (let i = 0; i < 4; i++) {
        const playerSelection = $(`
            <div class="player-selection mb-2">
                <select class="form-select player-select">${playerOptions}</select>
                <select class="form-select position-select mt-1" style="display: none">
                    <option value="flank">Flank</option>
                    <option value="pocket">Pocket</option>
                </select>
            </div>
        `);
        teamBContainer.append(playerSelection);
    }

    // Handle position toggle
    $('#usePositions').change(function() {
        $('.position-select').toggle(this.checked);
    });
}

function setupBalancedTeamSelector() {
    const select = $('#balancedPlayersSelect');
    select.empty();
    
    // Add all players as options
    playerMetrics.forEach(player => {
        select.append($('<option>', {
            value: player.name,
            text: player.name
        }));
    });
    
    // Enable multiple selection
    select.attr('multiple', 'multiple');
}

function calculateResults() {
    if (currentMode === 'compare') {
        const usePositions = $('#usePositions').is(':checked');
        const useRecentPerformance = $('#useRecentPerformance').is(':checked');
        
        // Get teams data
        const teamA = $('#teamAContainer .player-selection').map(function() {
            const player = {
                name: $(this).find('.player-select').val()
            };
            if (usePositions) {
                player.position = $(this).find('.position-select').val();
            }
            return player;
        }).get();
        
        const teamB = $('#teamBContainer .player-selection').map(function() {
            const player = {
                name: $(this).find('.player-select').val()
            };
            if (usePositions) {
                player.position = $(this).find('.position-select').val();
            }
            return player;
        }).get();

        // Validate positions if checkbox is checked
        if (usePositions) {
            // Validate Team A positions
            const teamAPositions = teamA.map(p => p.position);
            const teamAFlankCount = teamAPositions.filter(p => p === 'flank').length;
            const teamAPocketCount = teamAPositions.filter(p => p === 'pocket').length;
            
            // Validate Team B positions
            const teamBPositions = teamB.map(p => p.position);
            const teamBFlankCount = teamBPositions.filter(p => p === 'flank').length;
            const teamBPocketCount = teamBPositions.filter(p => p === 'pocket').length;
            
            if (teamAFlankCount !== 2 || teamAPocketCount !== 2) {
                alert('Team A must have exactly 2 flanks and 2 pockets');
                return;
            }
            
            if (teamBFlankCount !== 2 || teamBPocketCount !== 2) {
                alert('Team B must have exactly 2 flanks and 2 pockets');
                return;
            }
        }
        
        // If validation passes, proceed with the AJAX call
        $.ajax({
            url: '/compare_teams',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                teamA,
                teamB,
                allMetrics: playerMetrics,
                usePositions: usePositions,
                useRecentPerformance: useRecentPerformance
            }),
            success: displayResults,
            error: function(xhr) {
                alert('Error comparing teams: ' + xhr.responseJSON.error);
            }
        });
    } else {
        const selectedPlayers = $('#balancedPlayersSelect').val();
        const usePositions = $('#usePositionsBalanced').is(':checked');
        const useRecentPerformance = $('#useRecentPerformanceBalanced').is(':checked');
        
        if (selectedPlayers.length !== 8) {
            alert('Please select exactly 8 players');
            return;
        }
        
        $.ajax({
            url: '/find_balanced_teams',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                selectedPlayers,
                allMetrics: playerMetrics,
                usePositions,
                useRecentPerformance
            }),
            success: displayBalancedResults,
            error: function(xhr) {
                alert('Error finding balanced teams: ' + xhr.responseJSON.error);
            }
        });
    }
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
    let teamAHtml = '<h4>Team A:</h4><ul>';
    data.teamA.forEach(player => {
        teamAHtml += `<li>${player.name}${player.position ? ` (${player.position})` : ''}</li>`;
    });
    teamAHtml += '</ul>';

    let teamBHtml = '<h4>Team B:</h4><ul>';
    data.teamB.forEach(player => {
        teamBHtml += `<li>${player.name}${player.position ? ` (${player.position})` : ''}</li>`;
    });
    teamBHtml += '</ul>';

    const html = `
        <div class="row">
            <div class="col-md-6">
                ${teamAHtml}
                <p>Team Strength: ${formatNumber(data.teamAStrength.weighted_average)}</p>
            </div>
            <div class="col-md-6">
                ${teamBHtml}
                <p>Team Strength: ${formatNumber(data.teamBStrength.weighted_average)}</p>
            </div>
        </div>
        <div class="mt-3">
            <h5>Match Probabilities:</h5>
            <p>Team A win probability: ${(data.expectedA * 100).toFixed(1)}%</p>
            <p>Team B win probability: ${((1 - data.expectedA) * 100).toFixed(1)}%</p>
            
            <h5>Best of 3 Series Probabilities:</h5>
            <ul>
                <li>Team A wins 2-0: ${(data.seriesProbabilities['3-0'] * 100).toFixed(1)}%</li>
                <li>Team A wins 2-1: ${(data.seriesProbabilities['2-1'] * 100).toFixed(1)}%</li>
                <li>Team B wins 2-0: ${(data.seriesProbabilities['0-3'] * 100).toFixed(1)}%</li>
                <li>Team B wins 2-1: ${(data.seriesProbabilities['1-2'] * 100).toFixed(1)}%</li>
            </ul>
        </div>
    `;
    
    $('#resultsContent').html(html);
    $('#results').show();
}

function formatNumber(num) {
    return num.toFixed(0);
}

function compareTeams() {
    const teamA = getSelectedTeam('teamA');
    const teamB = getSelectedTeam('teamB');
    const usePositions = $('#usePositions').is(':checked');
    const useRecentPerformance = $('#useRecentPerformance').is(':checked');
    
    $.ajax({
        url: '/compare_teams',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            teamA: teamA,
            teamB: teamB,
            allMetrics: playerMetrics,
            usePositions: usePositions,
            useRecentPerformance: useRecentPerformance
        }),
        success: function(response) {
            displayComparisonResults(response);
        },
        error: function(error) {
            console.error('Error:', error);
        }
    });
} 