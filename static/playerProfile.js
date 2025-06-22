var finalResult = document.querySelectorAll('.finalResult')
var surface = document.querySelectorAll(".surfaceType") 

var odds_container = document.querySelectorAll(".odds")
var scores_container_player1 = document.querySelectorAll(".player1_scores")
var scores_container_player2 = document.querySelectorAll(".player2_scores")

var breakpoints = document.querySelectorAll(".breakPoints")

var summaryTable = document.querySelector(".summaryTable")

var matches_list = document.querySelector(".table")
let length = matches_list.children.length 
for (var i = 1; i < length - 1; i++) {
    var prev = matches_list.children[i - 1]
    var current = matches_list.children[i]


    if (prev.className === "header" && current.className === "header") {
        prev.style.display = "none"
    }

    console.log(current)
    try {
        var nxt = matches_list.children[i+1]

        if (current.className === "header" && nxt.className === "header") {
            nxt.style.display = "none"
        }
    } catch (err) {
        console.log(err)
    } 
}

finalResult.forEach(element => {
    if (element.textContent === "L") {
        element.style.background = "red"
    } else if (element.textContent === "W"){
        element.style.background = "green"
    }
});

surface.forEach(element => {
    surfaceType = element.textContent
    if (surfaceType === "hard") {
        element.style.background = "blue"
    } else if (surfaceType === "clay") {
        element.style.background = "#a65c03"
    } else if (surfaceType === "grass") {
        element.style.background = "green"
    } else {
        element.style.display = "none"
    }
})

for (var i = 0; i < odds_container.length; i++) 
{
    var odds1 = Number(odds_container[i].children[0].textContent)
    var odds2 = Number(odds_container[i].children[2].textContent)

    if (odds1 < odds2) {
        for (var j = 0; j < 5; j++) {     
            var score1 = scores_container_player1[i].children[j]
            var score2 = scores_container_player2[i].children[j]
            
            var score1_num = scores_container_player1[i].children[j].textContent.split("^")
            var score2_num = scores_container_player2[i].children[j].textContent.split("^")

            if (score1_num.length > 1) {
                if (Number(score1_num[0]) > Number(score2_num[0]))
                {
                    score1.style.color = "green"
                } else {
                    score2.style.color = "red"
                }
            }
        }
    } else {
        for (var j = 0; j < 5; j++) {
            var score1 = scores_container_player2[i].children[j]
            var score2 = scores_container_player1[i].children[j]
            
            var score1_num = scores_container_player2[i].children[j].textContent.split("^")
            var score2_num = scores_container_player1[i].children[j].textContent.split("^")

            if (score1_num.length > 1) {
                if (Number(score1_num[0]) > Number(score2_num[0]))
                    {
                    score1.style.color = "green"
                } else {
                    score2.style.color = "red"
                }
            }
        }
    }
}

// FORMATTING THE BREAKPOINTS
for (var i = 0; i < breakpoints.length; i++) {
    var sets_player1 = breakpoints[i].children[1]
    for (var j = 0; j < sets_player1.children.length; j++) {
        var set = sets_player1.children[j].children[1]

        for (var k = 0; k < set.children.length; k++) {
            var point = set.children[k]
            if (k % 2 === 1) {
                point.style.display = "none"
            }
        }
    }
}

// DEATH RIDING LOGIC
for (var i = 0; i < breakpoints.length; i++) {
    var sets_player1 = breakpoints[i].children[1]
    var sets_player2 = breakpoints[i].children[2]
    for (var j = 0; j < 5; j++) {
        var set_player1  = sets_player1.children[j].children[1]
        var set_player2 = sets_player2.children[j].children[1]


        for (var k = 0; k < set_player1.children.length-1; k++) {
            if (k % 2 === 0) {
                try {
                    var nxt = Number(set_player2.children[k+1].textContent.trim())
                    var crt = Number(set_player2.children[k].textContent.trim())
                    
                    if (nxt === crt) {
                        set_player1.children[k].style.color = "red"
                        set_player1.children[k].style.fontWeight = "bold"
                        continue
                    }
                    if (crt === nxt - 1) {
                        set_player1.children[k].style.color = "red"
                        set_player1.children[k].style.fontWeight = "bold"
                        continue
                    } 
                } catch {
                    continue
                } 
            }
        }


        for (var k = 0; k < set_player1.children.length-1; k++) {
            if (k % 2 === 0) {
                var nxt = Number(set_player1.children[k+1].textContent.trim())
                var crt = Number(set_player1.children[k].textContent.trim())
        
                if (nxt === crt) {
                    set_player1.children[k].style.color = "green"
                    set_player1.children[k].style.fontWeight = "bold"
                    continue
                }
                
                if ( crt === nxt - 1 ) {
                    set_player1.children[k].style.color = "green"
                    set_player1.children[k].style.fontWeight = "bold"
                    continue   
                }
            }
        }

    }
}

// MOVING THE SUMMARY ROW TO THE BOTTOM

let row = document.createElement("div")
row.className = "row"

let rows = summaryTable.children
row = rows[2]

console.log(row)

summaryTable.removeChild(rows[2])
summaryTable.append(row)

// TAB FUNCTIONALITY
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // Tab switching functionality
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            this.classList.add('active');
            document.getElementById(targetTab + '-tab').classList.add('active');

            // Load predictions if predictions tab is clicked
            if (targetTab === 'predictions') {
                loadPlayerPredictions();
            }
        });
    });
});

// Function to load player predictions
function loadPlayerPredictions() {
    const playerName = window.playerName;
    if (!playerName) {
        showNoPredictionsMessage();
        return;
    }

    const loadingMessage = document.querySelector('.loading-message');
    const noPredictionsMessage = document.querySelector('.no-predictions-message');
    const predictionsContent = document.querySelector('.predictions-content');

    // Show loading message
    loadingMessage.style.display = 'block';
    noPredictionsMessage.style.display = 'none';
    predictionsContent.innerHTML = '';

    // Fetch predictions from API
    fetch(`/api/player-predictions/${encodeURIComponent(playerName)}`)
        .then(response => response.json())
        .then(data => {
            loadingMessage.style.display = 'none';

            if (data.success && data.predictions && data.predictions.length > 0) {
                renderPredictions(data.predictions);
            } else {
                showNoPredictionsMessage();
            }
        })
        .catch(error => {
            console.error('Error loading predictions:', error);
            loadingMessage.style.display = 'none';
            showNoPredictionsMessage();
        });
}

function showNoPredictionsMessage() {
    const noPredictionsMessage = document.querySelector('.no-predictions-message');
    noPredictionsMessage.style.display = 'block';
}

function renderPredictions(predictions) {
    const predictionsContent = document.querySelector('.predictions-content');
    predictionsContent.innerHTML = '';

    // Match counter for unique IDs
    let matchCounter = 0;

    predictions.forEach((item, index) => {
        if (Array.isArray(item) && item.length === 3 && item[2] === 'header') {
            // This is a header row - use today's matches format with exactly 11 columns
            const headerDiv = document.createElement('div');
            headerDiv.className = 'header';
            let headerHTML = '';

            // Standard header columns for tennis matches
            const headerColumns = ['Time', 'Name', 'S', '1', '2', '3', '4', '5', 'H2H', 'H', 'A'];

            for (let i = 0; i < 11; i++) {
                let content = '';
                if (i < item.length) {
                    content = item[i] || '';
                } else {
                    // Use standard header labels if item doesn't have enough data
                    content = headerColumns[i] || '';
                }
                headerHTML += `<div class="col">${content}</div>`;
            }
            headerDiv.innerHTML = headerHTML;
            predictionsContent.appendChild(headerDiv);
        } else if (Array.isArray(item) && item.length === 2) {
            // This is a match with two players - use same structure as today's matches
            const matchContainer = document.createElement('div');
            matchContainer.className = 'match-prediction-container';

            // Use a match counter for unique IDs
            const matchIndex = matchCounter++;
            matchContainer.innerHTML = renderMatchContent(item, matchIndex);

            predictionsContent.appendChild(matchContainer);
        }
    });
}

function renderMatchContent(match, matchIndex) {
    const player1 = match[0];
    const player2 = match[1];

    // Get the actual match index from the API data (13th element, index 12)
    const actualMatchIndex = player1.length > 12 ? player1[12] : matchIndex;

    // Get h and a values (second to last and last values from player1 array, excluding Header and match index)
    const hValue = player1.length > 10 ? player1[9] : '-';  // H column
    const aValue = player1.length > 11 ? player1[10] : '-'; // A column

    // Check if this match has a prediction by looking at the Header column (last element)
    let hasPrediction = false;
    let predictionData = null;

    // Check both player1 and player2 for prediction data in Header column
    // Header column is at index 11 (12th element), actual match index is at index 12 (13th element)
    const player1Header = player1[11]; // Header column
    const player2Header = player2[11]; // Header column

    console.log('Player1 Header:', player1Header);
    console.log('Player2 Header:', player2Header);
    console.log('Player1 full array:', player1);
    console.log('Player2 full array:', player2);
    console.log('Player1 array length:', player1.length);
    console.log('Player2 array length:', player2.length);

    // Parse prediction data from Header column
    if (player1Header && typeof player1Header === 'string' && player1Header.startsWith('prediction:')) {
        try {
            const jsonStr = player1Header.substring(11); // Remove "prediction:" prefix
            const compactData = JSON.parse(jsonStr);

            // Convert compact format back to full format
            predictionData = {
                winner: compactData.w || '',
                player1_score: compactData.p1 || '',
                player2_score: compactData.p2 || '',
                spread: compactData.s || '',
                notes: compactData.n || ''
            };
            hasPrediction = true;
            console.log('Parsed prediction data:', predictionData);
        } catch (e) {
            console.error('Error parsing prediction data:', e);
        }
    } else if (player2Header && typeof player2Header === 'string' && player2Header.startsWith('prediction:')) {
        try {
            const jsonStr = player2Header.substring(11); // Remove "prediction:" prefix
            const compactData = JSON.parse(jsonStr);

            // Convert compact format back to full format
            predictionData = {
                winner: compactData.w || '',
                player1_score: compactData.p1 || '',
                player2_score: compactData.p2 || '',
                spread: compactData.s || '',
                notes: compactData.n || ''
            };
            hasPrediction = true;
            console.log('Parsed prediction data from player2:', predictionData);
        } catch (e) {
            console.error('Error parsing prediction data from player2:', e);
        }
    }

    return `
        <div class="match-prediction-container">
            <div class="row">
                <div class="time">${player1[0]}</div>
                <div class="players">
                    <div class="player1">
                        <div>${player1[1] || ''}</div>
                        <div>${player1[2] || ''}</div>
                        <div>${player1[3] || ''}</div>
                        <div>${player1[4] || ''}</div>
                        <div>${player1[5] || ''}</div>
                        <div>${player1[6] || ''}</div>
                        <div>${player1[7] || ''}</div>
                        <div>${player1[8] || ''}</div>
                    </div>
                    <div class="player2">
                        <div>${player2[1] || ''}</div>
                        <div>${player2[2] || ''}</div>
                        <div>${player2[3] || ''}</div>
                        <div>${player2[4] || ''}</div>
                        <div>${player2[5] || ''}</div>
                        <div>${player2[6] || ''}</div>
                        <div>${player2[7] || ''}</div>
                        <div>${player2[8] || ''}</div>
                    </div>
                </div>
                <div class="h">${hValue}</div>
                <div class="a">${aValue}</div>
            </div>

        <!-- Prediction bar -->
        <div class="prediction-bar-container">
            <div class="prediction-bar" onclick="window.togglePredictionForm(${matchIndex}, false, false, 'profile')">
                <span>${hasPrediction ? 'Edit Prediction' : 'Make Prediction'}</span>
            </div>
        </div>

        <!-- Prediction form -->
        <div class="prediction-form" id="prediction-form-${matchIndex}-profile" style="display: none;">
            <form class="predict-form">
                <input type="hidden" name="match_index" value="${actualMatchIndex}">
                <input type="hidden" name="is_women" value="false">
                <input type="hidden" name="is_profile" value="true">

                <div style="font-size: 10px; color: #999; margin-bottom: 10px;">Match Index: ${actualMatchIndex} (Local: ${matchIndex})</div>

                <div class="form-group">
                    <label>Winner:</label>
                    <div class="radio-group">
                        <div class="radio-option">
                            <input type="radio" name="winner" value="player1" ${predictionData && predictionData.winner === 'player1' ? 'checked' : ''}>
                            <label>${player1[1]}</label>
                        </div>
                        <div class="radio-option">
                            <input type="radio" name="winner" value="player2" ${predictionData && predictionData.winner === 'player2' ? 'checked' : ''}>
                            <label>${player2[1]}</label>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label>Predicted Score:</label>
                    <div class="score-inputs">
                        <div class="score-input">
                            <label>${player1[1]} Score:</label>
                            <input type="text" name="player1_score" value="${predictionData ? predictionData.player1_score || '' : ''}" placeholder="e.g., 6-4, 6-2">
                        </div>
                        <div class="score-input">
                            <label>${player2[1]} Score:</label>
                            <input type="text" name="player2_score" value="${predictionData ? predictionData.player2_score || '' : ''}" placeholder="e.g., 4-6, 2-6">
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label>Spread (optional):</label>
                    <input type="text" name="spread" value="${predictionData ? predictionData.spread || '' : ''}" placeholder="e.g., +1.5, -2.5">
                </div>

                <div class="form-group">
                    <label>Notes (optional):</label>
                    <textarea name="notes" placeholder="Any additional notes about your prediction...">${predictionData ? predictionData.notes || '' : ''}</textarea>
                </div>

                <div class="form-actions">
                    <button type="button" class="cancel-btn" onclick="window.togglePredictionForm(${matchIndex}, false, false, 'profile')">Cancel</button>
                    <button type="button" class="save-btn" onclick="window.savePrediction(this.form)">Save Prediction</button>
                </div>
            </form>
        </div>

        <!-- Hidden prediction data for form access -->
        ${hasPrediction ? `
        <div class="prediction-data" style="display: none;">prediction:${JSON.stringify(predictionData)}</div>
        ` : ''}

        <!-- Display existing prediction -->
        ${hasPrediction ? `
        <div class="user-prediction" id="existing-prediction-${matchIndex}-profile">
            <h5>Your Prediction:</h5>
            <ul>
                ${predictionData.winner ? `<li><strong>Winner:</strong> ${predictionData.winner === 'player1' ? player1[1] : player2[1]}</li>` : ''}
                ${predictionData.player1_score ? `<li><strong>${player1[1]} Score:</strong> ${predictionData.player1_score}</li>` : ''}
                ${predictionData.player2_score ? `<li><strong>${player2[1]} Score:</strong> ${predictionData.player2_score}</li>` : ''}
                ${predictionData.spread ? `<li><strong>Spread:</strong> ${predictionData.spread}</li>` : ''}
                ${predictionData.notes ? `<li><strong>Notes:</strong> ${predictionData.notes}</li>` : ''}
            </ul>
        </div>
        ` : ''}
        </div>
    `;
}

