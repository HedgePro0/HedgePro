// Save prediction data with loading indicator
const savePrediction = (form) => {
    const matchIndex = form.match_index.value;
    const isWomen = form.is_women.value === 'true';
    const isNextDay = form.is_next_day ? form.is_next_day.value === 'true' : false;
    const isProfile = form.is_profile ? form.is_profile.value === 'true' : false;
    const winner = form.winner.value;
    const player1Score = form.player1_score.value;
    const player2Score = form.player2_score.value;
    const spread = form.spread ? form.spread.value : '';
    const notes = form.notes ? form.notes.value : '';
    
    // Validate required fields
    if (!winner) {
        alert('Please select a winner');
        return false;
    }
    
    console.log(`Saving prediction for match ${matchIndex}, isWomen: ${isWomen}, isNextDay: ${isNextDay}, isProfile: ${isProfile}`);
    console.log(`Winner: ${winner}, Scores: ${player1Score}-${player2Score}, Spread: ${spread}`);
    
    // Show loading indicator
    const saveButton = form.querySelector('.save-btn');
    const originalText = saveButton.textContent;
    saveButton.disabled = true;
    saveButton.textContent = 'Saving...';
    
    // Add a loading overlay to the form
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = '<div class="spinner"></div><div class="loading-text">Saving prediction...</div>';
    form.appendChild(loadingOverlay);
    
    // Create data object to send to server
    const data = {
        match_index: parseInt(matchIndex),
        is_women: isWomen,
        is_next_day: isNextDay,
        is_profile: isProfile,
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
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // Remove loading overlay
        if (loadingOverlay.parentNode) {
            loadingOverlay.parentNode.removeChild(loadingOverlay);
        }
        
        // Reset button
        saveButton.disabled = false;
        saveButton.textContent = originalText;
        
        if (data.success) {
            console.log('Prediction saved successfully');
            
            // Show success notification
            showNotification('Prediction saved successfully!', 'success');
            
            // Hide the form
            const formContainer = form.closest('.prediction-form');
            if (formContainer) {
                formContainer.style.display = 'none';
            }
            
            // Only reload if the server indicates it's needed
            if (data.reload_needed) {
                console.log('Reloading page to show updated prediction');
                showNotification('Reloading page to show your prediction...', 'info');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // Show a success message without reloading
                showNotification('Prediction saved! Refresh the page when done to see all predictions.', 'success');
            }
        } else {
            console.error('Error saving prediction:', data.error);
            showNotification(`Error: ${data.error}`, 'error');
        }
    })
    .catch((error) => {
        // Remove loading overlay
        if (loadingOverlay.parentNode) {
            loadingOverlay.parentNode.removeChild(loadingOverlay);
        }
        
        // Reset button
        saveButton.disabled = false;
        saveButton.textContent = originalText;
        
        console.error('Error saving prediction:', error);
        showNotification('Error saving prediction. Please try again.', 'error');
    });
    
    return false; // Prevent form submission
};

// Function to show notifications
function showNotification(message, type = 'info') {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Show notification with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Make sure the function is available globally
window.savePrediction = savePrediction;
window.showNotification = showNotification;

// Toggle prediction form visibility
window.togglePredictionForm = function(matchIndex, isWomen, isNextDay, context) {
    let formId, existingPredictionId;

    if (context === 'profile') {
        // Player profile context
        formId = `prediction-form-${matchIndex}-profile`;
        existingPredictionId = `existing-prediction-${matchIndex}-profile`;
    } else {
        // Today's matches context
        const gender = isWomen ? 'w' : 'm';
        const dayType = isNextDay ? '-next' : '';
        formId = `prediction-form-${matchIndex}-${gender}${dayType}`;
        existingPredictionId = `existing-prediction-${matchIndex}-${gender}${dayType}`;
    }

    const form = document.getElementById(formId);
    const existingPrediction = document.getElementById(existingPredictionId);

    console.log(`Toggling form ${formId}, exists: ${form !== null}, context: ${context || 'today'}, isNextDay: ${isNextDay}`);
    
    if (form) {
        // Toggle form visibility
        if (form.style.display === 'none' || form.style.display === '') {
            form.style.display = 'block';

            // Populate form with existing prediction data if available
            populatePredictionForm(form, context);

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
        showNotification(`Error: Form not found (ID: ${formId})`, 'error');
    }
};

// Function to populate prediction form with existing data
function populatePredictionForm(form, context) {
    try {
        // Find the match container that contains this form
        const matchContainer = form.closest('.match-prediction-container');
        if (!matchContainer) return;

        // Look for prediction data in the container
        let predictionData = null;

        if (context === 'profile') {
            // For profile context, look for hidden prediction data div
            const predictionDataDiv = matchContainer.querySelector('.prediction-data');
            if (predictionDataDiv) {
                const text = predictionDataDiv.textContent;
                if (text.startsWith('prediction:')) {
                    predictionData = JSON.parse(text.substring(11));
                    console.log('Found prediction data for form population:', predictionData);
                }
            }
        } else {
            // For today's matches context, use existing logic
            const predictionDataElements = matchContainer.querySelectorAll('.prediction-data');
            for (const element of predictionDataElements) {
                const text = element.textContent;
                if (text.startsWith('prediction:')) {
                    predictionData = JSON.parse(text.substring(11));
                    break;
                }
            }
        }

        if (!predictionData) {
            console.log('No prediction data found for form population');
            return;
        }

        // Populate form fields
        if (predictionData.winner) {
            const winnerRadio = form.querySelector(`input[name="winner"][value="${predictionData.winner}"]`);
            if (winnerRadio) {
                winnerRadio.checked = true;
            }
        }

        if (predictionData.player1_score) {
            const player1ScoreInput = form.querySelector('input[name="player1_score"]');
            if (player1ScoreInput) {
                player1ScoreInput.value = predictionData.player1_score;
            }
        }

        if (predictionData.player2_score) {
            const player2ScoreInput = form.querySelector('input[name="player2_score"]');
            if (player2ScoreInput) {
                player2ScoreInput.value = predictionData.player2_score;
            }
        }

        if (predictionData.spread) {
            const spreadInput = form.querySelector('input[name="spread"]');
            if (spreadInput) {
                spreadInput.value = predictionData.spread;
            }
        }

        if (predictionData.notes) {
            const notesTextarea = form.querySelector('textarea[name="notes"]');
            if (notesTextarea) {
                notesTextarea.value = predictionData.notes;
            }
        }

        console.log('Successfully populated form with existing prediction data');
    } catch (e) {
        console.error('Error populating prediction form:', e);
    }
}

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






