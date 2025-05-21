from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify
import csv
import os
from datetime import timedelta
from functools import wraps 
import json
from os import listdir
from os.path import isfile, join

app = Flask(__name__)
app.secret_key = '$4$4$4$6'  # Use a secure key for sessions
app.permanent_session_lifetime = timedelta(days=7)  # Session will last 7 days

# Add a custom filter to parse JSON strings
@app.template_filter('fromjson')
def from_json(value):
    try:
        return json.loads(value)
    except:
        return None

# Simple credentials for your private use
USERNAME = 'Hedgepro44'
PASSWORD = '$4$4$4$6'
app.permanent_session_lifetime = timedelta(days=30)  # Session will last 7 days

# Login Required Decorator
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' in session:
            return func(*args, **kwargs)
        else:
            flash("Please log in first.")
            return redirect(url_for('login'))
    return wrapper

# Data Loading (Unchanged)
names = []
prevCounter = 0 
prevMatchesData = []
prevMatchesData_w = []

todayMatchesData = []
todayMatchesData_w = []

nextMatchesData = []
nextMatchesData_w = []

menRankedPlayers = []
femaleRankedPlayers = []

# Load Data (Unchanged)
with open("previousMatchesCounter", encoding="utf-8") as file:
    prevCounter = int(file.read())
# print(prevCounter)
    
if prevCounter > 0:
    # Load men's previous matches with consistent parsing
    with open(f"./Previous_Matches/{prevCounter}.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                prevMatchesData.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                prevMatchesData.append(match_data)
                i += 2
            else:
                i += 1
                
    # Load women's previous matches with the same improved logic
    with open(f"./Previous_Matches/{prevCounter}_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                prevMatchesData_w.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                prevMatchesData_w.append(match_data)
                i += 2
            else:
                i += 1
        
# Load other files (Unchanged)
# with open('./playerLinks.csv') as file:
#     csvreader = csv.reader(file)
#     for row in csvreader:
#         names.append(row[0].lower())

names = [f for f in listdir("./FlashScore_database/") if not isfile(join("./FlashScore_database/", f))]

with open("./tmp/todaysMatches.csv", encoding="utf-8") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < (len(temp) - 1):
        if temp[i][-1] == "header":
            todayMatchesData.append(temp[i])
            i += 1
        else:
            todayMatchesData.append([ temp[i], temp[i+1] ])
            i += 2

with open("./tmp/todaysMatches_w.csv", encoding="utf-8") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < (len(temp) - 1):
        if temp[i][-1] == "header":
            todayMatchesData_w.append(temp[i])
            i += 1
        else:
            todayMatchesData_w.append([ temp[i], temp[i+1] ])
            i += 2

with open("./tmp/nextMatches.csv", encoding="utf-8") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < (len(temp) - 1):
        if temp[i][-1] == "header":
            nextMatchesData.append(temp[i])
            i += 1
        else:
            nextMatchesData.append([ temp[i], temp[i+1] ])
            i += 2

with open("./tmp/nextMatches_w.csv", encoding="utf-8") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < (len(temp) - 1):
        if temp[i][-1] == "header":
            nextMatchesData_w.append(temp[i])
            i += 1
        else:
            nextMatchesData_w.append([ temp[i], temp[i+1] ])
            i += 2
    
with open("men_ranking.csv", encoding="utf-8") as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        menRankedPlayers.append(row)
        
with open("women_ranking.csv", encoding="utf-8") as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        femaleRankedPlayers.append(row)
    

def getData(name):
    # GETTING THE MATCH DATA FOR A PARTICULAR PERSON
    rows = []
    name = name.replace("%20", " ")
    with open(f'./FlashScore_database/{name}/match_details.csv', encoding="utf-8") as file:
        csvreader = csv.reader(file)
        nextMatch = False
        length = 0
        temp_rows = []
        for row in csvreader:
            temp_rows.append(row)
        for i in range(len(temp_rows)):
            if not len(temp_rows[i]):
                continue

            if nextMatch:
                nextMatch = False 
                continue
            if temp_rows[i][-1] == 'header':
                rows.append(temp_rows[i])
            else:
                match_data = [temp_rows[i], temp_rows[i+1]]
                rows.append(match_data)
                nextMatch = True
    matches_info = rows[1::]

    # GETTING THE PROFILE DATA
    profileData = []
    with open(f'./FlashScore_database/{name}/personal_details.csv', encoding="utf-8") as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            profileData.append(row)
        
    # GETTING THE SUMMARY TABLE FOR THE REQUIRED PLAYER
    summary = []
    with open(f'./FlashScore_database/{name}/career_details.csv', encoding="utf-8") as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            summary.append(row)
    
    return matches_info, profileData, summary

# Login Required Decorator
def login_required(func):
    @wraps(func)  # This preserves the original function name and metadata
    def wrapper(*args, **kwargs):
        if 'user' in session:
            return func(*args, **kwargs)
        else:
            flash("Please log in first.")
            return redirect(url_for('login'))
    return wrapper

# LOGIN ROUTE
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == USERNAME and password == PASSWORD:
            session.permanent = True  # Session will persist across browser restarts
            session['user'] = username  # Store username in session
            flash("Login successful!", "info")
            return redirect(url_for('searchPlayer'))
        else:
            flash("Incorrect username or password.", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')

# LOGOUT ROUTE
@app.route("/logout")
def logout():
    session.pop('user', None)  # Remove user from session
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# PLAYER PROFILE PAGE (Login Required)
@app.route('/<name>')
@login_required
def player_profile_page(name):
    matches_info, profileData, summary = getData(name)
    # for row in matches_info:
        # print(row[0])
        # print(row[1])
        # print()
    return render_template('playerProfile.html', matches_info=matches_info, profileData=profileData, summary=summary)

# PLAYER SEARCH PAGE (Login Required)
@app.route("/", methods=['GET', 'POST'])
@login_required
def searchPlayer():
    # Declare globals at the beginning of the function
    global todayMatchesData, todayMatchesData_w
    global nextMatchesData, nextMatchesData_w
    global prevMatchesData, prevMatchesData_w
    
    # Reload previous matches data
    prevMatchesData = []
    prevMatchesData_w = []
    
    with open("previousMatchesCounter", encoding="utf-8") as file:
        prevCounter = int(file.read())
    
    if prevCounter > 0:
        # Reload men's previous matches
        with open(f"./Previous_Matches/{prevCounter}.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < len(temp):
                if not temp[i] or len(temp[i]) == 0:
                    i += 1
                    continue
                    
                if temp[i][-1] == "header":
                    prevMatchesData.append(temp[i])
                    i += 1
                elif i+1 < len(temp):
                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None
                    
                    for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                prediction_data = json.loads(prediction_json)
                            except:
                                pass
                    
                    match_data = [temp[i], temp[i+1]]
                    
                    # Add prediction data if found
                    if has_prediction and prediction_data:
                        match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                    
                    prevMatchesData.append(match_data)
                    i += 2
                else:
                    i += 1
        
        # Reload women's previous matches with the same improved logic
        with open(f"./Previous_Matches/{prevCounter}_w.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < len(temp):
                if not temp[i] or len(temp[i]) == 0:
                    i += 1
                    continue
                    
                if temp[i][-1] == "header":
                    prevMatchesData_w.append(temp[i])
                    i += 1
                elif i+1 < len(temp):
                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None
                    
                    for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                prediction_data = json.loads(prediction_json)
                            except:
                                pass
                    
                    match_data = [temp[i], temp[i+1]]
                    
                    # Add prediction data if found
                    if has_prediction and prediction_data:
                        match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                    
                    prevMatchesData_w.append(match_data)
                    i += 2
                else:
                    i += 1
    
    # Reload today's men's matches with the same improved logic
    todayMatchesData = []
    with open("./tmp/todaysMatches.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                todayMatchesData.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                todayMatchesData.append(match_data)
                i += 2
            else:
                i += 1
    
    # Reload today's women's matches with the same improved logic
    todayMatchesData_w = []
    with open("./tmp/todaysMatches_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                todayMatchesData_w.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                todayMatchesData_w.append(match_data)
                i += 2
            else:
                i += 1
    
    # Reload next matches (men) with the same improved logic
    nextMatchesData = []
    with open("./tmp/nextMatches.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                nextMatchesData.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                nextMatchesData.append(match_data)
                i += 2
            else:
                i += 1
    
    # Reload next matches (women) with the same improved logic
    nextMatchesData_w = []
    with open("./tmp/nextMatches_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                nextMatchesData_w.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                nextMatchesData_w.append(match_data)
                i += 2
            else:
                i += 1
    
    # Handle form submission
    if request.method == "POST":
        player_name = request.form.get("player_name")
        if player_name != "":
            return redirect(url_for('player_profile_page', name=player_name.lower()))
    
    # Pass the data to the template
    return render_template('home.html', 
                          today_rows=todayMatchesData, 
                          next_rows=nextMatchesData, 
                          prev_rows=prevMatchesData, 
                          today_rows_w=todayMatchesData_w, 
                          next_rows_w=nextMatchesData_w, 
                          prev_rows_w=prevMatchesData_w)

# RANKED PLAYERS PAGE (Login Required)
@app.route("/ranked-players")
@login_required
def rankedPlayers():
    return render_template("ranked_players.html", men_data=menRankedPlayers, female_data=femaleRankedPlayers)

# Add this route to handle saving predictions
@app.route("/save_prediction", methods=['POST'])
@login_required
def save_prediction():
    try:
        # Declare globals at the beginning of the function
        global todayMatchesData, todayMatchesData_w
        global nextMatchesData, nextMatchesData_w
        
        data = request.json
        match_index = int(data.get('match_index'))
        is_women = data.get('is_women') == True
        is_next_day = data.get('is_next_day') == True
        winner = data.get('winner', '')
        player1_score = data.get('player1_score', '')
        player2_score = data.get('player2_score', '')
        spread = data.get('spread', '')
        notes = data.get('notes', '')
        
        # Print debug information
        print(f"Saving prediction: match_index={match_index}, is_women={is_women}, is_next_day={is_next_day}, winner={winner}")
        print(f"Scores: player1={player1_score}, player2={player2_score}, spread={spread}")
        
        # Get the correct in-memory data and file path based on gender and day
        if is_next_day:
            if is_women:
                matches_data = nextMatchesData_w
                file_path = "./tmp/nextMatches_w.csv"
            else:
                matches_data = nextMatchesData
                file_path = "./tmp/nextMatches.csv"
        else:
            if is_women:
                matches_data = todayMatchesData_w
                file_path = "./tmp/todaysMatches_w.csv"
            else:
                matches_data = todayMatchesData
                file_path = "./tmp/todaysMatches.csv"
        
        # Read the file to get the raw data
        raw_data = []
        with open(file_path, 'r', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            raw_data = list(csvreader)
        
        # Count actual matches (non-header rows) to find the correct one
        actual_match_count = 0
        target_raw_indices = None
        i = 0
        
        while i < len(raw_data):
            # Skip empty rows
            if not raw_data[i] or len(raw_data[i]) == 0:
                i += 1
                continue
                
            # Skip header rows
            if raw_data[i][-1] == "header":
                i += 1
                continue
            
            # Check if this is a player1 row (followed by a player2 row)
            if (i+1 < len(raw_data) and 
                len(raw_data[i]) > 0 and 
                len(raw_data[i+1]) > 0):
                
                # This is a match (player1 + player2)
                if actual_match_count == match_index:
                    # This is the match we want to update
                    target_raw_indices = (i, i+1)
                    break
                
                actual_match_count += 1
                i += 2  # Skip both player rows
            else:
                i += 1
        
        if not target_raw_indices:
            return jsonify({"success": False, "error": f"Match with index {match_index} not found"})
        
        # Get the row indices for the selected match
        row1_index, row2_index = target_raw_indices
        
        # Get player names for verification
        raw_player1 = raw_data[row1_index][1] if len(raw_data[row1_index]) > 1 else "Unknown"
        raw_player2 = raw_data[row2_index][1] if len(raw_data[row2_index]) > 1 else "Unknown"
        
        print(f"Raw data match: {raw_player1} vs {raw_player2}")
        print(f"Row indices: player1={row1_index}, player2={row2_index}")
        
        # Remove any existing prediction from both player rows
        raw_data[row1_index] = [item for item in raw_data[row1_index] 
                               if not (isinstance(item, str) and item.startswith('prediction:'))]
        raw_data[row2_index] = [item for item in raw_data[row2_index] 
                               if not (isinstance(item, str) and item.startswith('prediction:'))]
        
        # Format prediction data as a JSON string
        prediction_data = {
            "winner": winner,
            "player1_score": player1_score,
            "player2_score": player2_score,
            "spread": spread,
            "notes": notes
        }
        
        # Convert to string format: "prediction:JSON_DATA"
        prediction_string = f"prediction:{json.dumps(prediction_data)}"
        
        # Add the new prediction to both player rows
        raw_data[row1_index].append(prediction_string)
        raw_data[row2_index].append(prediction_string)
        
        print(f"Updated row 1: {raw_data[row1_index]}")
        print(f"Updated row 2: {raw_data[row2_index]}")
        
        # Write back to the file
        with open(file_path, 'w', newline='', encoding="utf-8") as file:
            csvwriter = csv.writer(file)
            csvwriter.writerows(raw_data)
        
        # Also update the in-memory data
        # Find the corresponding match in the in-memory data
        actual_match_count = 0
        target_memory_index = None
        
        for i, item in enumerate(matches_data):
            if isinstance(item, list) and len(item) == 1 and item[0][-1] == "header":
                continue
            
            if actual_match_count == match_index:
                target_memory_index = i
                break
            
            actual_match_count += 1
        
        if target_memory_index is not None:
            # Update the in-memory data
            if len(matches_data[target_memory_index]) > 2:
                # Update existing prediction
                matches_data[target_memory_index][2] = {
                    "has_prediction": True,
                    "prediction_data": prediction_data
                }
            else:
                # Add new prediction
                matches_data[target_memory_index].append({
                    "has_prediction": True,
                    "prediction_data": prediction_data
                })
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error saving prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route("/reload_data")
@login_required
def reload_data():
    """Force reload of match data from CSV files"""
    global todayMatchesData, nextMatchesData, prevMatchesData
    global todayMatchesData_w, nextMatchesData_w, prevMatchesData_w
    
    # Reload previous matches data
    prevMatchesData = []
    prevMatchesData_w = []
    
    with open("previousMatchesCounter", encoding="utf-8") as file:
        prevCounter = int(file.read())
    
    if prevCounter > 0:
        # Reload men's previous matches with consistent parsing logic
        with open(f"./Previous_Matches/{prevCounter}.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < len(temp):
                if not temp[i] or len(temp[i]) == 0:
                    i += 1
                    continue
                    
                if temp[i][-1] == "header":
                    prevMatchesData.append(temp[i])
                    i += 1
                elif i+1 < len(temp):
                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None
                    
                    for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                prediction_data = json.loads(prediction_json)
                            except:
                                pass
                    
                    match_data = [temp[i], temp[i+1]]
                    
                    # Add prediction data if found
                    if has_prediction and prediction_data:
                        match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                    
                    prevMatchesData.append(match_data)
                    i += 2
                else:
                    i += 1
        
        # Reload women's previous matches with the same improved logic
        with open(f"./Previous_Matches/{prevCounter}_w.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < len(temp):
                if not temp[i] or len(temp[i]) == 0:
                    i += 1
                    continue
                    
                if temp[i][-1] == "header":
                    prevMatchesData_w.append(temp[i])
                    i += 1
                elif i+1 < len(temp):
                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None
                    
                    for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                prediction_data = json.loads(prediction_json)
                            except:
                                pass
                    
                    match_data = [temp[i], temp[i+1]]
                    
                    # Add prediction data if found
                    if has_prediction and prediction_data:
                        match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                    
                    prevMatchesData_w.append(match_data)
                    i += 2
                else:
                    i += 1
    
    # Reload today's men's matches with the same improved logic
    todayMatchesData = []
    with open("./tmp/todaysMatches.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                todayMatchesData.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                todayMatchesData.append(match_data)
                i += 2
            else:
                i += 1

    # Reload women's today matches
    todayMatchesData_w = []
    with open("./tmp/todaysMatches_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                todayMatchesData_w.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                todayMatchesData_w.append(match_data)
                i += 2

    # Reload next matches (men)
    nextMatchesData = []
    with open("./tmp/nextMatches.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < (len(temp) - 1):
            if temp[i][-1] == "header":
                nextMatchesData.append(temp[i])
                i += 1
            else:
                nextMatchesData.append([ temp[i], temp[i+1] ])
                i += 2

    # Reload next matches (women)
    nextMatchesData_w = []
    with open("./tmp/nextMatches_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < (len(temp) - 1):
            if temp[i][-1] == "header":
                nextMatchesData_w.append(temp[i])
                i += 1
            else:
                nextMatchesData_w.append([ temp[i], temp[i+1] ])
                i += 2

    # Reload previous matches if counter > 0
    prevMatchesData = []
    prevMatchesData_w = []
    with open("previousMatchesCounter", encoding="utf-8") as file:
        prevCounter = int(file.read())
    
    if prevCounter > 0:
        with open(f"./Previous_Matches/{prevCounter}.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < (len(temp) - 1):
                if temp[i][-1] == "header":
                    prevMatchesData.append(temp[i])
                    i += 1
                else:
                    prevMatchesData.append([ temp[i], temp[i+1] ])
                    i += 2
                    
        with open(f"./Previous_Matches/{prevCounter}_w.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < (len(temp) - 1):
                if temp[i][-1] == "header":
                    prevMatchesData_w.append(temp[i])
                    i += 1
                else:
                    prevMatchesData_w.append([ temp[i], temp[i+1] ])
                    i += 2

    flash("Data refreshed successfully!", "success")
    return redirect(url_for('searchPlayer'))

# Add this route to force reload data from files
@app.route("/refresh_data")
@login_required
def refresh_data():
    """Force reload of all match data from CSV files"""
    global todayMatchesData, nextMatchesData, prevMatchesData
    global todayMatchesData_w, nextMatchesData_w, prevMatchesData_w
    global menRankedPlayers, femaleRankedPlayers
    
    # Reload today's matches (men)
    todayMatchesData = []
    with open("./tmp/todaysMatches.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                todayMatchesData.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                todayMatchesData.append(match_data)
                i += 2
            else:
                i += 1

    # Reload women's today matches
    todayMatchesData_w = []
    with open("./tmp/todaysMatches_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < len(temp):
            if not temp[i] or len(temp[i]) == 0:
                i += 1
                continue
                
            if temp[i][-1] == "header":
                todayMatchesData_w.append(temp[i])
                i += 1
            elif i+1 < len(temp):
                # Check for prediction data in either row
                has_prediction = False
                prediction_data = None
                
                for item in temp[i] + (temp[i+1] if i+1 < len(temp) else []):
                    if isinstance(item, str) and item.startswith('prediction:'):
                        has_prediction = True
                        try:
                            prediction_json = item.replace('prediction:', '', 1)
                            prediction_data = json.loads(prediction_json)
                        except:
                            pass
                
                match_data = [temp[i], temp[i+1]]
                
                # Add prediction data if found
                if has_prediction and prediction_data:
                    match_data.append({"has_prediction": True, "prediction_data": prediction_data})
                
                todayMatchesData_w.append(match_data)
                i += 2

    # Reload next matches (men)
    nextMatchesData = []
    with open("./tmp/nextMatches.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < (len(temp) - 1):
            if temp[i][-1] == "header":
                nextMatchesData.append(temp[i])
                i += 1
            else:
                nextMatchesData.append([ temp[i], temp[i+1] ])
                i += 2

    # Reload next matches (women)
    nextMatchesData_w = []
    with open("./tmp/nextMatches_w.csv", encoding="utf-8") as file:
        temp = []
        csvreader = csv.reader(file)
        for row in csvreader:
            temp.append(row)
        i = 0
        while i < (len(temp) - 1):
            if temp[i][-1] == "header":
                nextMatchesData_w.append(temp[i])
                i += 1
            else:
                nextMatchesData_w.append([ temp[i], temp[i+1] ])
                i += 2

    # Reload previous matches if counter > 0
    prevMatchesData = []
    prevMatchesData_w = []
    with open("previousMatchesCounter", encoding="utf-8") as file:
        prevCounter = int(file.read())
    
    if prevCounter > 0:
        with open(f"./Previous_Matches/{prevCounter}.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < (len(temp) - 1):
                if temp[i][-1] == "header":
                    prevMatchesData.append(temp[i])
                    i += 1
                else:
                    prevMatchesData.append([ temp[i], temp[i+1] ])
                    i += 2
                    
        with open(f"./Previous_Matches/{prevCounter}_w.csv", encoding="utf-8") as file:
            temp = []
            csvreader = csv.reader(file)
            for row in csvreader:
                temp.append(row)
            i = 0
            while i < (len(temp) - 1):
                if temp[i][-1] == "header":
                    prevMatchesData_w.append(temp[i])
                    i += 1
                else:
                    prevMatchesData_w.append([ temp[i], temp[i+1] ])
                    i += 2

    flash("Data refreshed successfully!", "success")
    return redirect(url_for('searchPlayer'))

# RUNNING THE APP
if __name__ == "__main__":
    app.run(debug=True)
