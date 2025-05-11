// Save prediction data
window.savePrediction = function(form) {
    const matchIndex = form.querySelector('input[name="match_index"]').value;
    const isWomen = form.querySelector('input[name="is_women"]').value === 'true';
    const winner = form.querySelector('input[name="winner"]:checked')?.value || '';
    const player1Score = form.querySelector('input[name="player1_score"]').value;
    const player2Score = form.querySelector('input[name="player2_score"]').value;
    const spread = form.querySelector('input[name="spread"]').value;
    const notes = form.querySelector('textarea[name="notes"]').value;
    
    console.log(`Saving prediction for match ${matchIndex}, isWomen: ${isWomen}`);
    console.log(`Winner: ${winner}, Scores: ${player1Score}-${player2Score}, Spread: ${spread}`);
    
    // Create data object to send to server
    const data = {
        match_index: parseInt(matchIndex),
        is_women: isWomen,
        winner: winner,
        player1_score: player1Score,
        player2_score: player2Score,
        spread: spread,
        notes: notes
    };
    
    // Send data to server
    fetch('/save_prediction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Prediction saved successfully');
            // Hide the form and reload the page to show updated prediction
            form.closest('.prediction-form').style.display = 'none';
            window.location.reload();
        } else {
            console.error('Error saving prediction:', data.error);
            alert(`Error saving prediction: ${data.error}`);
        }
    })
    .catch((error) => {
        console.error('Error saving prediction:', error);
        alert('Error saving prediction. Please try again.');
    });
    
    return false; // Prevent form submission
};

// Toggle prediction form visibility
window.togglePredictionForm = function(matchIndex, isWomen) {
    const gender = isWomen ? 'w' : 'm';
    const formId = `prediction-form-${matchIndex}-${gender}`;
    const existingPredictionId = `existing-prediction-${matchIndex}-${gender}`;
    
    const form = document.getElementById(formId);
    const existingPrediction = document.getElementById(existingPredictionId);
    
    console.log(`Toggling form ${formId}, exists: ${form !== null}`);
    
    if (form) {
        // Toggle form visibility
        if (form.style.display === 'none' || form.style.display === '') {
            form.style.display = 'block';
            // Hide existing prediction if it exists
            if (existingPrediction) {
                existingPrediction.style.display = 'none';
            }
        } else {
            form.style.display = 'none';
            // Show existing prediction if it exists
            if (existingPrediction) {
                existingPrediction.style.display = 'block';
            }
        }
    } else {
        console.error(`Form with ID ${formId} not found`);
    }
};

// Process all prediction displays on page load
document.addEventListener('DOMContentLoaded', function() {
    // Process all prediction containers
    const predictionContainers = document.querySelectorAll('.user-prediction');
    console.log(`Found ${predictionContainers.length} prediction containers`);
    
    predictionContainers.forEach(container => {
        // Get the match row associated with this prediction
        const matchRow = container.closest('.match-prediction-container').querySelector('.row');
        if (!matchRow) return;
        
        // Get player data
        const player1Data = matchRow.querySelector('.player1');
        const player2Data = matchRow.querySelector('.player2');
        
        if (!player1Data || !player2Data) return;
        
        // Get prediction data
        const predictionDataElements = container.querySelectorAll('.prediction-data');
        let predictionData = null;
        
        try {
            // First try to find prediction data in hidden divs
            for (const element of predictionDataElements) {
                const text = element.textContent;
                if (text.startsWith('prediction:')) {
                    predictionData = JSON.parse(text.substring(11));
                    break;
                }
            }
            
            // If not found, try to extract from the prediction text
            if (!predictionData) {
                const winnerLi = Array.from(container.querySelectorAll('li')).find(li => 
                    li.textContent.trim().startsWith('Winner:'));
                
                if (winnerLi) {
                    const winnerText = winnerLi.textContent.trim();
                    const player1Name = player1Data.children[0].textContent.trim();
                    const player2Name = player2Data.children[0].textContent.trim();
                    
                    // Determine if winner is player1 or player2
                    const predictedWinner = winnerText.includes(player1Name) ? 'player1' : 'player2';
                    
                    predictionData = { winner: predictedWinner };
                    console.log('Extracted prediction data:', predictionData);
                }
            }
        } catch (e) {
            console.error('Error parsing prediction data:', e);
        }
        
        if (!predictionData || !predictionData.winner) {
            console.log('No valid prediction data found');
            return;
        }
        
        // Count sets won by each player
        let player1Sets = 0;
        let player2Sets = 0;
        
        // Get all set scores (columns 3-7, which are divs 2-6 in each player container)
        // Note: The first div (index 0) is the player name, and index 1 is 'S'
        for (let i = 2; i <= 6; i++) {
            if (i >= player1Data.children.length || i >= player2Data.children.length) continue;
            
            const player1Score = player1Data.children[i].textContent.trim();
            const player2Score = player2Data.children[i].textContent.trim();
            
            console.log(`Set ${i-1}: ${player1Score} - ${player2Score}`);
            
            // If scores are numbers, compare them
            if (!isNaN(player1Score) && !isNaN(player2Score)) {
                if (parseInt(player1Score) > parseInt(player2Score)) {
                    player1Sets++;
                } else if (parseInt(player2Score) > parseInt(player1Score)) {
                    player2Sets++;
                }
            }
        }
        
        console.log(`Sets won: Player1=${player1Sets}, Player2=${player2Sets}`);
        
        // Determine actual winner
        let actualWinner = null;
        if (player1Sets > player2Sets) {
            actualWinner = 'player1';
        } else if (player2Sets > player1Sets) {
            actualWinner = 'player2';
        }
        
        // If we have both a prediction and an actual result, show success/failure
        if (actualWinner && predictionData.winner) {
            const resultBanner = container.querySelector('.prediction-result-banner');
            if (resultBanner) {
                if (actualWinner === predictionData.winner) {
                    resultBanner.classList.add('success');
                    resultBanner.classList.remove('failure');
                    resultBanner.innerHTML = '<span>Prediction Correct!</span>';
                } else {
                    resultBanner.classList.add('failure');
                    resultBanner.classList.remove('success');
                    resultBanner.innerHTML = '<span>Prediction Incorrect</span>';
                }
                resultBanner.style.display = 'block';
            }
        }
    });
});

