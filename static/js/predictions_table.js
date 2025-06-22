// Predictions Table JavaScript

// Store original values for cancel functionality
let originalValues = {};

// Show notification
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Show loading overlay
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// Edit row functionality
function editRow(rowId) {
    const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
    if (!row) return;
    
    // Store original values
    originalValues[rowId] = {};
    const editableCells = row.querySelectorAll('.editable');
    
    editableCells.forEach(cell => {
        const column = cell.getAttribute('data-column');
        const originalValue = cell.textContent.trim();
        originalValues[rowId][column] = originalValue;
        
        // Create input field
        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalValue;
        input.setAttribute('data-column', column);
        
        // Clear cell and add input
        cell.innerHTML = '';
        cell.appendChild(input);
        cell.classList.add('editing');
    });
    
    // Toggle buttons
    row.querySelector('.edit-btn').style.display = 'none';
    row.querySelector('.save-btn').style.display = 'inline-block';
    row.querySelector('.cancel-btn').style.display = 'inline-block';
    row.querySelector('.delete-btn').style.display = 'none';
    
    // Focus on first input
    const firstInput = row.querySelector('input');
    if (firstInput) {
        firstInput.focus();
        firstInput.select();
    }
}

// Save row functionality
function saveRow(rowId) {
    const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
    if (!row) return;
    
    // Collect updated data
    const updatedData = {};
    const inputs = row.querySelectorAll('.editable input');
    
    inputs.forEach(input => {
        const column = input.getAttribute('data-column');
        updatedData[column] = input.value.trim();
    });
    
    showLoading();
    
    // Send update request
    fetch('/edit_prediction_row', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            row_id: rowId,
            updated_data: updatedData
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Update cells with new values
            inputs.forEach(input => {
                const cell = input.parentNode;
                const column = input.getAttribute('data-column');
                const value = updatedData[column];
                
                cell.innerHTML = value;
                cell.classList.remove('editing');
            });
            
            // Toggle buttons back
            row.querySelector('.edit-btn').style.display = 'inline-block';
            row.querySelector('.save-btn').style.display = 'none';
            row.querySelector('.cancel-btn').style.display = 'none';
            row.querySelector('.delete-btn').style.display = 'inline-block';
            
            // Clean up stored values
            delete originalValues[rowId];
            
            showNotification('Row updated successfully!', 'success');
        } else {
            showNotification(`Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error saving row:', error);
        showNotification('Error saving row. Please try again.', 'error');
    });
}

// Cancel edit functionality
function cancelEdit(rowId) {
    const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
    if (!row) return;
    
    // Restore original values
    const editableCells = row.querySelectorAll('.editable');
    editableCells.forEach(cell => {
        const column = cell.getAttribute('data-column');
        const originalValue = originalValues[rowId][column] || '';
        
        cell.innerHTML = originalValue;
        cell.classList.remove('editing');
    });
    
    // Toggle buttons back
    row.querySelector('.edit-btn').style.display = 'inline-block';
    row.querySelector('.save-btn').style.display = 'none';
    row.querySelector('.cancel-btn').style.display = 'none';
    row.querySelector('.delete-btn').style.display = 'inline-block';
    
    // Clean up stored values
    delete originalValues[rowId];
}

// Delete row functionality
function deleteRow(rowId) {
    if (!confirm('Are you sure you want to delete this row? This action cannot be undone.')) {
        return;
    }
    
    showLoading();
    
    // Send delete request
    fetch('/delete_prediction_row', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            row_id: rowId
        }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Remove row from table
            const row = document.querySelector(`tr[data-row-id="${rowId}"]`);
            if (row) {
                row.remove();
            }
            
            showNotification('Row deleted successfully!', 'success');
        } else {
            showNotification(`Error: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error deleting row:', error);
        showNotification('Error deleting row. Please try again.', 'error');
    });
}

// Refresh table functionality
function refreshTable() {
    showLoading();
    window.location.reload();
}

// Handle Enter key in input fields
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter' && event.target.tagName === 'INPUT') {
        const row = event.target.closest('tr');
        if (row) {
            const rowId = row.getAttribute('data-row-id');
            saveRow(rowId);
        }
    }
    
    if (event.key === 'Escape' && event.target.tagName === 'INPUT') {
        const row = event.target.closest('tr');
        if (row) {
            const rowId = row.getAttribute('data-row-id');
            cancelEdit(rowId);
        }
    }
});

// Double-click to edit
document.addEventListener('dblclick', function(event) {
    if (event.target.classList.contains('editable') && !event.target.classList.contains('editing')) {
        const row = event.target.closest('tr');
        if (row) {
            const rowId = row.getAttribute('data-row-id');
            editRow(rowId);
        }
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('Predictions table loaded');
    
    // Add tooltips or help text
    const editableCells = document.querySelectorAll('.editable');
    editableCells.forEach(cell => {
        cell.title = 'Double-click to edit, or use the Edit button';
    });
});
