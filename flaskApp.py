from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify
import csv
import os
from datetime import timedelta, datetime
from functools import wraps
import json
from os import listdir
from os.path import isfile, join
from supabase import create_client
from dotenv import load_dotenv
import time



# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Get configuration from environment variables
app.secret_key = os.getenv('SECRET_KEY', '$4$4$4$6')  # Use environment variable or fallback
app.permanent_session_lifetime = timedelta(days=7)  # Session will last 7 days

# Initialize Supabase client with credentials from environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

# Create Supabase client (using retry mechanism for timeout handling)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Retry mechanism for Supabase operations
def retry_supabase_operation(operation_func, max_retries=3, delay=5):
    """
    Retry a Supabase operation with exponential backoff
    """
    for attempt in range(max_retries):
        try:
            return operation_func()
        except Exception as e:
            error_str = str(e).lower()
            # Check for various timeout and connection error patterns
            is_timeout_error = any(pattern in error_str for pattern in [
                "timeout", "timed out", "connection", "network",
                "readtimeout", "connecttimeout", "httptimeout"
            ])

            if is_timeout_error:
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)  # Exponential backoff: 5s, 10s, 20s
                    print(f"⚠️ Supabase timeout/connection error on attempt {attempt + 1}/{max_retries}")
                    print(f"   Error: {str(e)}")
                    print(f"   Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Supabase operation failed after {max_retries} attempts: {str(e)}")
                    raise e
            else:
                # Non-timeout error, don't retry
                print(f"❌ Non-timeout Supabase error (not retrying): {str(e)}")
                raise e
    return None

# Add a custom filter to parse JSON strings
@app.template_filter('fromjson')
def from_json(value):
    try:
        return json.loads(value)
    except:
        return None

# Get credentials from environment variables
USERNAME = os.getenv('USERNAME', 'Hedgepro44')  # Use environment variable or fallback
PASSWORD = os.getenv('PASSWORD', '$4$4$4$6')  # Use environment variable or fallback
app.permanent_session_lifetime = timedelta(days=30)  # Session will last 30 days



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

# Data Loading (Using Supabase for today's matches)
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

# Function to load today's matches from Supabase
def load_todays_matches_from_supabase():
    global todayMatchesData, todayMatchesData_w
    
    # Clear existing data
    todayMatchesData = []
    todayMatchesData_w = []
    
    try:
        '''
        Loading the men's data for todays matches from supabase
        '''

        def get_mens_matches():
            return supabase.table('todays_matches').select('*').execute()

        response = retry_supabase_operation(get_mens_matches)

        if response.data:
            
            skip = False
            
            data = response.data
            data.sort(key=lambda x: list(x.values())[0])
            
            for i, row in enumerate(data):
                if skip:
                    skip = False
                    continue
                values = list(row.values())
                
                # Skip the ID (first value)
                values = values[1:]
                
                # Check if this is a header row
                if 'header' in values:
                    todayMatchesData.append(values)
                else:
                    if i+1 >= len(data):
                        print(f"Warning: Unexpected end of data at index {i}")
                        continue
                        
                    skip = True
                    match = []
                    row1 = list(data[i].values())[1:]
                    row2 = list(data[i+1].values())[1:]
                    
                    # Clean up None values
                    if row1[-1] == None:
                        row1.pop()
                    if row2[-1] == None:
                        row2.pop()
                        
                    for j, value in enumerate(row1):
                        if value == None:
                            row1[j] = "-"
                    for j, value in enumerate(row2):
                        if value == None:
                            row2[j] = "-"
                    
                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None

                    for item in row1 + row2:
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                raw_prediction_data = json.loads(prediction_json)

                                # Handle both old and new compact formats
                                if 'w' in raw_prediction_data:  # New compact format
                                    prediction_data = {
                                        "winner": raw_prediction_data.get('w', ''),
                                        "player1_score": raw_prediction_data.get('p1', ''),
                                        "player2_score": raw_prediction_data.get('p2', ''),
                                        "spread": raw_prediction_data.get('s', ''),
                                        "notes": raw_prediction_data.get('n', '')
                                    }
                                else:  # Old format
                                    prediction_data = raw_prediction_data

                            except Exception as e:
                                pass  # Silently ignore prediction parsing errors

                    match.append(row1)
                    match.append(row2)

                    # Always add prediction metadata as third element
                    if has_prediction and prediction_data:
                        match.append({"has_prediction": True, "prediction_data": prediction_data})
                        print(f"Added prediction data to match at index {len(todayMatchesData)} - Players: {row1[1]} vs {row2[1]}")
                    else:
                        match.append({"has_prediction": False, "prediction_data": None})
                    
                    todayMatchesData.append(match)
        else:
            print("No data found in todays_matches table")
        
        '''
        Loading the women's data for todays matches from supabase
        '''
        def get_womens_matches():
            return supabase.table('todays_matches_w').select('*').execute()

        response = retry_supabase_operation(get_womens_matches)

        if response.data:
            
            skip_w = False
            
            data_w = response.data
            data_w.sort(key=lambda x: list(x.values())[0])
            
            for i, row in enumerate(data_w):
                if skip_w:
                    skip_w = False
                    continue
                
                values = list(row.values())
                
                # Skip the ID (first value)
                values = values[1:]
                
                # Check if this is a header row
                if 'header' in values:
                    todayMatchesData_w.append(values)
                else:
                    if i+1 >= len(data_w):
                        print(f"Warning: Unexpected end of data at index {i}")
                        continue
                    
                    skip_w = True
                    match_w = []
                    
                    row1 = list(data_w[i].values())[1:]
                    row2 = list(data_w[i+1].values())[1:]
                    
                    # Clean up None values
                    if row1[-1] == None:
                        row1.pop()
                    if row2[-1] == None:
                        row2.pop()
                        
                    for j, value in enumerate(row1):
                        if value == None:
                            row1[j] = "-"
                    for j, value in enumerate(row2):
                        if value == None:
                            row2[j] = "-"
                    
                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None

                    for item in row1 + row2:
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                raw_prediction_data = json.loads(prediction_json)

                                # Handle both old and new compact formats
                                if 'w' in raw_prediction_data:  # New compact format
                                    prediction_data = {
                                        "winner": raw_prediction_data.get('w', ''),
                                        "player1_score": raw_prediction_data.get('p1', ''),
                                        "player2_score": raw_prediction_data.get('p2', ''),
                                        "spread": raw_prediction_data.get('s', ''),
                                        "notes": raw_prediction_data.get('n', '')
                                    }
                                else:  # Old format
                                    prediction_data = raw_prediction_data

                            except Exception as e:
                                pass  # Silently ignore prediction parsing errors

                    match_w.append(row1)
                    match_w.append(row2)

                    # Always add prediction metadata as third element
                    if has_prediction and prediction_data:
                        match_w.append({"has_prediction": True, "prediction_data": prediction_data})
                        print(f"Added prediction data to women's match at index {len(todayMatchesData_w)}")
                    else:
                        match_w.append({"has_prediction": False, "prediction_data": None})
                    
                    todayMatchesData_w.append(match_w)
        else:
            print("No data found in todays_matches_w table")
        
    except Exception as e:
        print(f"Error loading data from Supabase: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't use flash outside of a request context
        # flash(f"Error loading match data: {str(e)}", "danger")

# Function to load next day's matches from Supabase
def load_next_matches_from_supabase():
    global nextMatchesData, nextMatchesData_w

    # Clear existing data
    nextMatchesData = []
    nextMatchesData_w = []

    try:
        '''
        Loading the men's data for next day matches from supabase
        '''

        def get_next_mens_matches():
            return supabase.table('next_matches').select('*').order('id').execute()

        response = retry_supabase_operation(get_next_mens_matches)

        if response.data:

            skip = False

            data = response.data

            for i, row in enumerate(data):
                if skip:
                    skip = False
                    continue
                values = list(row.values())

                # Skip the ID (first value)
                values = values[1:]

                # Check if this is a header row
                if 'header' in values:
                    nextMatchesData.append(values)
                else:
                    if i+1 >= len(data):
                        print(f"Warning: Unexpected end of data at index {i}")
                        continue

                    skip = True
                    match = []
                    row1 = list(data[i].values())[1:]
                    row2 = list(data[i+1].values())[1:]

                    # Clean up None values
                    if row1[-1] == None:
                        row1.pop()
                    if row2[-1] == None:
                        row2.pop()

                    for j, value in enumerate(row1):
                        if value == None:
                            row1[j] = "-"
                    for j, value in enumerate(row2):
                        if value == None:
                            row2[j] = "-"

                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None

                    for item in row1 + row2:
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                raw_prediction_data = json.loads(prediction_json)

                                # Handle both old and new compact formats
                                if 'w' in raw_prediction_data:  # New compact format
                                    prediction_data = {
                                        "winner": raw_prediction_data.get('w', ''),
                                        "player1_score": raw_prediction_data.get('p1', ''),
                                        "player2_score": raw_prediction_data.get('p2', ''),
                                        "spread": raw_prediction_data.get('s', ''),
                                        "notes": raw_prediction_data.get('n', '')
                                    }
                                else:  # Old format
                                    prediction_data = raw_prediction_data

                            except Exception as e:
                                pass  # Silently ignore prediction parsing errors

                    match.append(row1)
                    match.append(row2)

                    # Always add prediction metadata as third element
                    if has_prediction and prediction_data:
                        match.append({"has_prediction": True, "prediction_data": prediction_data})
                    else:
                        match.append({"has_prediction": False, "prediction_data": None})

                    nextMatchesData.append(match)
        else:
            print("No data found in next_matches table")

        '''
        Loading the women's data for next day matches from supabase
        '''
        def get_next_womens_matches():
            return supabase.table('next_matches_w').select('*').order('id').execute()

        response = retry_supabase_operation(get_next_womens_matches)

        if response.data:

            skip_w = False

            data_w = response.data

            for i, row in enumerate(data_w):
                if skip_w:
                    skip_w = False
                    continue

                values = list(row.values())

                # Skip the ID (first value)
                values = values[1:]

                # Check if this is a header row
                if 'header' in values:
                    nextMatchesData_w.append(values)
                else:
                    if i+1 >= len(data_w):
                        print(f"Warning: Unexpected end of data at index {i}")
                        continue

                    skip_w = True
                    match_w = []

                    row1 = list(data_w[i].values())[1:]
                    row2 = list(data_w[i+1].values())[1:]

                    # Clean up None values
                    if row1[-1] == None:
                        row1.pop()
                    if row2[-1] == None:
                        row2.pop()

                    for j, value in enumerate(row1):
                        if value == None:
                            row1[j] = "-"
                    for j, value in enumerate(row2):
                        if value == None:
                            row2[j] = "-"

                    # Check for prediction data in either row
                    has_prediction = False
                    prediction_data = None

                    for item in row1 + row2:
                        if isinstance(item, str) and item.startswith('prediction:'):
                            has_prediction = True
                            try:
                                prediction_json = item.replace('prediction:', '', 1)
                                raw_prediction_data = json.loads(prediction_json)

                                # Handle both old and new compact formats
                                if 'w' in raw_prediction_data:  # New compact format
                                    prediction_data = {
                                        "winner": raw_prediction_data.get('w', ''),
                                        "player1_score": raw_prediction_data.get('p1', ''),
                                        "player2_score": raw_prediction_data.get('p2', ''),
                                        "spread": raw_prediction_data.get('s', ''),
                                        "notes": raw_prediction_data.get('n', '')
                                    }
                                else:  # Old format
                                    prediction_data = raw_prediction_data

                            except Exception as e:
                                pass  # Silently ignore prediction parsing errors

                    match_w.append(row1)
                    match_w.append(row2)

                    # Always add prediction metadata as third element
                    if has_prediction and prediction_data:
                        match_w.append({"has_prediction": True, "prediction_data": prediction_data})
                    else:
                        match_w.append({"has_prediction": False, "prediction_data": None})

                    nextMatchesData_w.append(match_w)
        else:
            print("No data found in next_matches_w table")

    except Exception as e:
        print(f"Error loading next day data from Supabase: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't use flash outside of a request context
        # flash(f"Error loading next day match data: {str(e)}", "danger")

# Load today's matches from Supabase on startup
load_todays_matches_from_supabase()

# Load next day's matches from Supabase on startup
load_next_matches_from_supabase()

# LOGIN ROUTE
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Simple authentication using the hardcoded credentials
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            session.permanent = True
            flash("Login successful!", "success")
            return redirect(url_for('searchPlayer'))
        else:
            flash("Invalid username or password", "danger")

    return render_template('login.html')

# LOGOUT ROUTE
@app.route("/logout")
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# Load other data from CSV files (unchanged for now)
with open("previousMatchesCounter") as file:
    prevCounter = int(file.read())

if prevCounter > 0:
    with open(f"./Previous_Matches/{prevCounter}.csv") as file:
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
                
    with open(f"./Previous_Matches/{prevCounter}_w.csv") as file:
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
        
names = [f for f in listdir("./FlashScore_database/") if not isfile(join("./FlashScore_database/", f))]

# Next matches are now loaded from Supabase in load_next_matches_from_supabase() function

# Load rankings data (unchanged)
with open("men_ranking.csv") as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        menRankedPlayers.append(row)
        
with open("women_ranking.csv") as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        femaleRankedPlayers.append(row)

# Update the reload_data route to reload only from Supabase
@app.route("/reload_data")
@login_required
def reload_data():
    """Force reload of today's match data from Supabase"""
    load_todays_matches_from_supabase()
    flash("Today's matches data refreshed from Supabase!", "success")
    return redirect(url_for('searchPlayer'))

# Helper function to validate data structure
def validate_match_data(data, label):
    print(f"Validating {label} data structure...")
    
    if not data:
        print(f"{label} is empty")
        return
    
    for i, item in enumerate(data):
        if isinstance(item, list):
            if len(item) == 1 and item[0][-1] == "header":
                print(f"{label}[{i}] is a header row")
            elif len(item) >= 2:
                print(f"{label}[{i}] is a match with {len(item)} elements")
                
                # Check player rows
                for j, player in enumerate(item[:2]):
                    if not isinstance(player, list):
                        print(f"WARNING: {label}[{i}][{j}] is not a list: {player}")
                    elif len(player) < 9:
                        print(f"WARNING: {label}[{i}][{j}] has fewer than 9 elements: {player}")
                
                # Check prediction data
                if len(item) > 2:
                    if not isinstance(item[2], dict):
                        print(f"WARNING: {label}[{i}][2] is not a dict: {item[2]}")
                    elif "has_prediction" not in item[2]:
                        print(f"WARNING: {label}[{i}][2] missing 'has_prediction' key: {item[2]}")
            else:
                print(f"WARNING: {label}[{i}] has unexpected structure: {item}")
        else:
            print(f"WARNING: {label}[{i}] is not a list: {item}")

@app.route("/<name>")
@login_required
def player_profile_page(name):
    # Handle URL encoding (replace %20 with spaces)
    decoded_name = name.replace("%20", " ")

    # Check if player exists using case-insensitive matching (same as searchPlayer function)
    if decoded_name.lower() not in [n.lower() for n in names]:
        flash("Player not found in database.", "danger")
        return redirect(url_for('searchPlayer'))

    # Find the exact name match from the names list (preserving original case)
    exact_name = None
    for n in names:
        if n.lower() == decoded_name.lower():
            exact_name = n
            break

    if not exact_name:
        flash("Player not found in database.", "danger")
        return redirect(url_for('searchPlayer'))

    try:
        matches_info, profileData, summary = getData(exact_name)
        print(f"DEBUG: Loaded {len(matches_info)} match items for {exact_name}")
        for i, item in enumerate(matches_info[:5]):  # Show first 5 items
            if isinstance(item, list) and len(item) > 0:
                if isinstance(item[0], list):
                    print(f"DEBUG: Match {i}: [{item[0][:3]}...] vs [{item[1][:3]}...]")
                else:
                    print(f"DEBUG: Header {i}: {item[:3]}...")
        return render_template('playerProfile.html', matches_info=matches_info, profileData=profileData, summary=summary)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        flash(f"Error loading player data: {str(e)}", "danger")
        return redirect(url_for('searchPlayer'))

@app.route("/", methods=['GET', 'POST'])
@login_required
def searchPlayer():
    global todayMatchesData, todayMatchesData_w, nextMatchesData, nextMatchesData_w, prevMatchesData, prevMatchesData_w

    # Always reload data from Supabase on every page refresh to ensure fresh data
    print("🔄 Refreshing data from Supabase on page load...")
    load_todays_matches_from_supabase()
    load_next_matches_from_supabase()
    print("✅ Data refreshed successfully")

    if request.method == "POST":
        player_name = request.form.get("player_name")
        if player_name and player_name.lower() in [n.lower() for n in names]:
            return redirect(url_for('player_profile_page', name=player_name))
        else:
            flash("Player not found.", "danger")

    return render_template(
        'home.html',
        today_rows=todayMatchesData,
        next_rows=nextMatchesData,
        prev_rows=prevMatchesData,
        today_rows_w=todayMatchesData_w,
        next_rows_w=nextMatchesData_w,
        prev_rows_w=prevMatchesData_w
    )

def getData(name):
    rows = []
    name = name.replace("%20", " ")

    # Load match details with error handling
    try:
        with open(f'./FlashScore_database/{name}/match_details.csv', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            nextMatch = False
            temp_rows = [row for row in csvreader if row]
            print(f"DEBUG: Total rows in CSV: {len(temp_rows)}")
            for i in range(1, len(temp_rows)):  # Start from index 1 to skip CSV header
                if not len(temp_rows[i]):
                    continue

                # Skip empty/separator rows (rows with only empty strings and dashes)
                if all(cell in ['', '-'] for cell in temp_rows[i]):
                    continue

                if nextMatch:
                    nextMatch = False
                    continue
                if (len(temp_rows[i]) > 2 and temp_rows[i][2] == 'header') or temp_rows[i][-1] == 'header':
                    rows.append(temp_rows[i])
                else:
                    print(f"DEBUG: Found match at row {i}: {temp_rows[i][:3]}...")
                    if i + 1 < len(temp_rows):  # Check bounds
                        match_data = [temp_rows[i], temp_rows[i+1]]
                        rows.append(match_data)
                        nextMatch = True
                    else:
                        print(f"DEBUG: Skipping last row {i} - no pair available")
            print(f"DEBUG: Total rows processed: {len(rows)}")
            if len(rows) > 0:
                print(f"DEBUG: First row: {rows[0][:3]}...")
            matches_info = rows  # Don't skip the first row
            print(f"DEBUG: Final matches_info length: {len(matches_info)}")
    except FileNotFoundError:
        matches_info = []
    except Exception as e:
        matches_info = []

    # Load profile data with error handling
    profileData = []
    try:
        with open(f'./FlashScore_database/{name}/personal_details.csv', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            profileData.extend(csvreader)
    except FileNotFoundError:
        profileData = [["No profile image available"], ["Name: " + name], ["No additional details available"]]
    except Exception as e:
        profileData = [["No profile image available"], ["Name: " + name], ["Error loading details"]]

    # Load career summary with error handling
    summary = []
    try:
        with open(f'./FlashScore_database/{name}/career_details.csv', encoding="utf-8") as file:
            csvreader = csv.reader(file)
            summary.extend(csvreader)
    except FileNotFoundError:
        summary = [["Year", "Summary", "Clay", "Hard", "Indoors", "Grass", "Not Set"], ["No data", "No career data available", "-", "-", "-", "-", "-"]]
    except Exception as e:
        summary = [["Year", "Summary", "Clay", "Hard", "Indoors", "Grass", "Not Set"], ["Error", "Error loading career data", "-", "-", "-", "-", "-"]]

    return matches_info, profileData, summary


# RANKED PLAYERS PAGE (Login Required)
@app.route("/ranked-players")
@login_required
def rankedPlayers():
    return render_template("ranked_players.html", men_data=menRankedPlayers, female_data=femaleRankedPlayers)

# TEST PREDICTIONS API (Login Required)
@app.route("/test-api/<player_name>")
@login_required
def test_api(player_name):
    """Test route to directly call the player predictions API"""
    try:
        # Call the API function directly
        result = get_player_predictions(player_name)
        return f"<h1>API Test for {player_name}</h1><pre>{result.get_data(as_text=True)}</pre>"
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"

# PLAYER PREDICTIONS API (Login Required)
@app.route("/api/player-predictions/<player_name>")
@login_required
def get_player_predictions(player_name):
    """Get all predictions from the predictions table that include the specified player name"""
    try:
        # Decode URL encoding
        decoded_name = player_name.replace("%20", " ")
        print(f"DEBUG: API called for player: '{decoded_name}'")

        # Query only the predictions table for matches with actual predictions
        all_predictions = []

        # Check predictions table for matches involving this player
        response = supabase.table("predictions").select('*').order('id').execute()
        if response.data:
            all_predictions.extend(response.data)
            print(f"DEBUG: Found {len(response.data)} rows in predictions table")

        if not all_predictions:
            print("DEBUG: No data returned from any match tables")
            return jsonify({"success": True, "predictions": []})

        # Helper function to normalize player names for comparison
        def normalize_name(name):
            if not name:
                return ""
            # Remove rankings, parentheses, and extra spaces
            import re
            # Remove content in parentheses like "(3)" or "(WC)"
            name = re.sub(r'\([^)]*\)', '', name)
            # Remove extra spaces and convert to lowercase
            name = ' '.join(name.split()).lower()
            print(f"DEBUG: Normalized '{name}' from original")
            return name

        # Helper function to check if names match
        def names_match(profile_name, prediction_name):
            # Normalize both names
            norm_profile = normalize_name(profile_name)
            norm_prediction = normalize_name(prediction_name)

            print(f"DEBUG: Comparing '{norm_profile}' vs '{norm_prediction}'")

            # Simple exact match first
            if norm_profile == norm_prediction:
                print(f"DEBUG: Exact match found")
                return True

            # Split into parts
            profile_parts = norm_profile.split()
            prediction_parts = norm_prediction.split()

            # Need at least 2 parts (first name, last name) for both
            if len(profile_parts) < 2 or len(prediction_parts) < 2:
                print(f"DEBUG: Insufficient name parts: {len(profile_parts)} vs {len(prediction_parts)}")
                return False

            # Check if last names match (first word in each)
            if profile_parts[0] != prediction_parts[0]:
                print(f"DEBUG: Last names don't match: '{profile_parts[0]}' vs '{prediction_parts[0]}'")
                return False

            print(f"DEBUG: Last names match: '{profile_parts[0]}'")

            # Check first names (second word in each)
            profile_first = profile_parts[1]
            prediction_first = prediction_parts[1]

            print(f"DEBUG: Comparing first names: '{profile_first}' vs '{prediction_first}'")

            # Direct match
            if profile_first == prediction_first:
                print(f"DEBUG: First names are identical")
                return True

            # Check if one is abbreviation of the other
            # Remove any dots from abbreviations
            profile_first_clean = profile_first.replace('.', '')
            prediction_first_clean = prediction_first.replace('.', '')

            print(f"DEBUG: Cleaned first names: '{profile_first_clean}' vs '{prediction_first_clean}'")

            # Check if one starts with the other
            # Special case: single letter abbreviations (like "J" for "Jannik")
            if len(prediction_first_clean) == 1 and len(profile_first_clean) > 1:
                if profile_first_clean.lower().startswith(prediction_first_clean.lower()):
                    print(f"DEBUG: Single letter abbreviation match found: '{prediction_first_clean}' matches '{profile_first_clean}'")
                    return True
            elif len(profile_first_clean) == 1 and len(prediction_first_clean) > 1:
                if prediction_first_clean.lower().startswith(profile_first_clean.lower()):
                    print(f"DEBUG: Single letter abbreviation match found: '{profile_first_clean}' matches '{prediction_first_clean}'")
                    return True
            # For longer abbreviations, require at least 2 characters
            elif len(profile_first_clean) >= 2 and len(prediction_first_clean) >= 2:
                if (profile_first_clean.startswith(prediction_first_clean) or
                    prediction_first_clean.startswith(profile_first_clean)):
                    print(f"DEBUG: Multi-character abbreviation match found")
                    return True

            print(f"DEBUG: No first name match")
            return False

        # Filter predictions that include the player name
        player_predictions = []

        print(f"DEBUG: Looking for predictions for player: '{decoded_name}'")
        print(f"DEBUG: Normalized search name: '{normalize_name(decoded_name)}'")
        print(f"DEBUG: Total rows in predictions table: {len(all_predictions)}")

        # Count how many rows have actual predictions
        prediction_count = 0
        for row in all_predictions:
            if row.get('Header', '') and 'prediction:' in str(row.get('Header', '')):
                prediction_count += 1

        print(f"DEBUG: Found {prediction_count} rows with actual predictions")

        # Show first few rows for debugging
        for debug_i, row in enumerate(all_predictions[:10]):
            print(f"DEBUG: Row {debug_i}: Name='{row.get('Name', '')}', Header='{row.get('Header', '')}'")

        # Helper function to find the header for a given match index
        def find_header_for_match(match_index):
            # Backtrack from the match index to find the most recent header
            for j in range(match_index - 1, -1, -1):
                if all_predictions[j].get('Header') == 'header':
                    return all_predictions[j], j
            return None, -1

        # Process matches in pairs and track which headers we've already added
        added_headers = set()
        i = 0
        actual_match_index = 0  # Track the actual match index for saving predictions

        while i < len(all_predictions) - 1:  # -1 because we need pairs
            row1 = all_predictions[i]
            row2 = all_predictions[i + 1]

            # Skip header rows when processing matches
            if row1.get('Header') == 'header':
                i += 1
                continue

            if row2.get('Header') == 'header':
                i += 1
                continue

            # Check if this match has actual predictions (either player has prediction data)
            has_prediction = (
                (row1.get('Header', '') and 'prediction:' in str(row1.get('Header', ''))) or
                (row2.get('Header', '') and 'prediction:' in str(row2.get('Header', '')))
            )

            # Only process matches that have predictions
            if not has_prediction:
                i += 2  # Skip this match pair
                actual_match_index += 1  # Still increment match index even if no prediction
                continue

            # Check if either player in this pair matches our target player
            player1_name = row1.get('Name', '')
            player2_name = row2.get('Name', '')

            player1_matches = player1_name and names_match(decoded_name, player1_name)
            player2_matches = player2_name and names_match(decoded_name, player2_name)

            if player1_matches or player2_matches:
                print(f"DEBUG: Found match pair - Player1: '{player1_name}', Player2: '{player2_name}'")

                # Find the header for this match by backtracking
                header_row, header_index = find_header_for_match(i)

                # Add header if we found one and haven't added it yet
                if header_row and header_index not in added_headers:
                    print(f"DEBUG: Adding header: '{header_row.get('Name', '')}' for match at index {i}")
                    header_data = [header_row.get('Time', ''), header_row.get('Name', ''), 'header']
                    player_predictions.append(header_data)
                    added_headers.add(header_index)

                # Create match pair with actual match index embedded
                match_row1 = [
                    row1.get('Time', ''),
                    row1.get('Name', ''),
                    row1.get('S', ''),
                    row1.get('1', ''),
                    row1.get('2', ''),
                    row1.get('3', ''),
                    row1.get('4', ''),
                    row1.get('5', ''),
                    row1.get('H2H', ''),
                    row1.get('H', ''),
                    row1.get('A', ''),
                    row1.get('Header', ''),  # This contains prediction data
                    actual_match_index  # Add the actual match index as the 13th element
                ]

                match_row2 = [
                    row2.get('Time', ''),
                    row2.get('Name', ''),
                    row2.get('S', ''),
                    row2.get('1', ''),
                    row2.get('2', ''),
                    row2.get('3', ''),
                    row2.get('4', ''),
                    row2.get('5', ''),
                    row2.get('H2H', ''),
                    row2.get('H', ''),
                    row2.get('A', ''),
                    row2.get('Header', ''),  # This contains prediction data
                    actual_match_index  # Add the actual match index as the 13th element
                ]

                # Add the match pair
                player_predictions.append([match_row1, match_row2])

            # Always move by 2 to process pairs
            actual_match_index += 1  # Increment actual match index
            i += 2

        print(f"DEBUG: Found {len(player_predictions)} prediction items for {decoded_name}")

        return jsonify({
            "success": True,
            "predictions": player_predictions,
            "player_name": decoded_name
        })

    except Exception as e:
        print(f"Error fetching player predictions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

def find_header_for_match_in_table(table_data, match_index):
    """
    Generic helper function to find the header row associated with a given match index in any table data.

    Args:
        table_data: List of rows from the database table
        match_index: The index of the match (0-based)

    Returns:
        tuple: (header_row, header_index) or (None, -1) if no header found
    """
    try:
        # Count actual matches (skip headers) to find the position of our target match
        current_match = 0
        target_match_start_index = None

        i = 0
        while i < len(table_data):
            row = table_data[i]

            # Skip header rows
            if (row.get("Header", "") == "header" or
                row.get('Time', '') == 'Time' or
                'header' in str(row.get('Name', '')).lower() or
                row.get('Name', '') in ['S', '1', '2', '3', '4', '5', 'H', 'A', 'H2H']):
                i += 1
                continue

            # This is a match row
            if current_match == match_index:
                target_match_start_index = i
                break

            # Skip to next match (matches come in pairs)
            current_match += 1
            i += 2

        if target_match_start_index is None:
            return None, -1

        # Now backtrack from the target match to find the most recent header
        for j in range(target_match_start_index - 1, -1, -1):
            row = table_data[j]
            if (row.get("Header", "") == "header" or
                'header' in str(row.get('Name', '')).lower()):
                return row, j

        return None, -1

    except Exception as e:
        print(f"Error finding header for match: {str(e)}")
        return None, -1

def upload_prediction_to_supabase(prediction_string, match_index, is_women):
    """Upload only the prediction data to specific rows in Supabase"""
    try:
        # Determine which table to use
        table_name = "todays_matches_w" if is_women else "todays_matches"

        print(f"Uploading prediction to {table_name} table for match index {match_index}...")

        # Get all rows from the table
        response = supabase.table(table_name).select('*').execute()
        if not response.data:
            return False, "No data found in table"

        all_rows = response.data
        print(f"Found {len(all_rows)} total rows in {table_name}")

        # Find the rows that correspond to this match
        # Skip header rows and count actual match rows
        actual_match_count = 0
        target_row_indices = []

        # First, check if there's already a prediction for this match_index
        # by looking for existing predictions in the data
        existing_prediction_rows = []
        for i, row in enumerate(all_rows):
            # Check if this row contains a prediction
            for col, value in row.items():
                if col != 'id' and isinstance(value, str) and value.startswith('prediction:'):
                    existing_prediction_rows.append(i)
                    break

        # Now find the target rows for this match
        for i, row in enumerate(all_rows):
            # Check if this is a header row (contains "Time" in first column)
            first_col_key = list(row.keys())[1] if len(row.keys()) > 1 else None  # Skip 'id' column
            if first_col_key and row.get(first_col_key) == "Time":
                continue  # Skip header row

            # This is a match row
            if actual_match_count == match_index * 2:  # Player 1 row
                target_row_indices.append(i)
            elif actual_match_count == match_index * 2 + 1:  # Player 2 row
                target_row_indices.append(i)
                break  # We found both rows for this match

            actual_match_count += 1

        if len(target_row_indices) != 2:
            return False, f"Could not find both player rows for match index {match_index}"

        print(f"Found target rows at indices: {target_row_indices}")

        # Update both rows with the prediction string
        success_count = 0
        for row_index in target_row_indices:
            target_row = all_rows[row_index]
            row_id = target_row['id']

            # First, clear any existing predictions from ALL columns in this row
            clear_data = {}
            existing_prediction_columns = []
            for col, value in target_row.items():
                if col != 'id' and isinstance(value, str) and value.startswith('prediction:'):
                    existing_prediction_columns.append(col)
                    clear_data[col] = None  # Clear the existing prediction

            if existing_prediction_columns:
                print(f"Clearing existing predictions from row {row_id} columns: {existing_prediction_columns}")
                # Clear existing predictions first
                clear_result = supabase.table(table_name).update(clear_data).eq('id', row_id).execute()
                if not clear_result.data:
                    print(f"Warning: Failed to clear existing predictions from row {row_id}")

            # Now add the new prediction to the Header column
            available_columns = list(target_row.keys())
            print(f"Available columns: {available_columns}")

            # Use the "Header" column specifically for new predictions
            if 'Header' in available_columns:
                update_column = 'Header'
                print(f"Using 'Header' column for prediction in row {row_id}")
            else:
                print(f"'Header' column not found in row {row_id}. Available columns: {available_columns}")
                # Fallback to other columns if Header doesn't exist
                if 'A' in available_columns:
                    update_column = 'A'
                    print(f"Fallback: Using column 'A' for prediction in row {row_id}")
                else:
                    # Use the last available column (excluding 'id')
                    non_id_columns = [col for col in available_columns if col != 'id']
                    if non_id_columns:
                        update_column = non_id_columns[-1]
                    else:
                        continue

            # Update the row with the new prediction
            update_data = {update_column: prediction_string}
            update_result = supabase.table(table_name).update(update_data).eq('id', row_id).execute()

            if update_result.data:
                success_count += 1
                print(f"Successfully updated row {row_id} with new prediction in column '{update_column}'")
            else:
                print(f"Failed to update row {row_id}")

        if success_count == 2:
            print(f"Successfully updated both rows for match {match_index}")

            # Reload the data from Supabase to refresh the in-memory data
            load_todays_matches_from_supabase()

            return True, "Prediction saved successfully to database"
        else:
            return False, f"Only updated {success_count} out of 2 rows"
        

    except Exception as e:
        print(f"Error uploading prediction to Supabase: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Upload error: {str(e)}"

def sync_prediction_by_player_names(match_table, player1_name, player2_name, prediction_data, is_women=False):
    """
    Sync prediction to original match tables by finding the match using player names
    """
    try:
        print(f"🔍 SYNC BY NAMES: Searching {match_table} table for '{player1_name}' vs '{player2_name}'")

        # Determine table name
        if match_table == "today":
            table_name = "todays_matches_w" if is_women else "todays_matches"
        elif match_table == "next":
            table_name = "next_matches_w" if is_women else "next_matches"
        else:
            return False

        # Get all rows from the table
        def get_table_data():
            return supabase.table(table_name).select('*').order('id').execute()

        all_rows = retry_supabase_operation(get_table_data)
        if not all_rows or not all_rows.data:
            print(f"⚠️ SYNC BY NAMES: No data found in {table_name}")
            return False

        # Search for the match by player names
        for i in range(len(all_rows.data) - 1):
            row1 = all_rows.data[i]
            row2 = all_rows.data[i + 1]

            # Check if these rows contain our target players
            name1 = row1.get("Name", "").strip()
            name2 = row2.get("Name", "").strip()

            # Check both possible orders: player1-player2 or player2-player1
            if ((name1 == player1_name.strip() and name2 == player2_name.strip()) or
                (name1 == player2_name.strip() and name2 == player1_name.strip())):

                print(f"✅ SYNC BY NAMES: Found matching players at rows {i} and {i+1}")

                # Convert prediction data to compact format with "prediction:" prefix
                compact_data = {
                    "w": prediction_data.get("winner", ""),
                    "p1": prediction_data.get("player1_score", ""),
                    "p2": prediction_data.get("player2_score", ""),
                    "s": prediction_data.get("spread", ""),
                    "n": prediction_data.get("notes", "")
                }
                compact_prediction = "prediction:" + json.dumps(compact_data)

                # Update both player rows with the prediction
                player1_id = row1.get("id")
                player2_id = row2.get("id")

                if player1_id and player2_id:
                    def update_player1():
                        return supabase.table(table_name).update({"Header": compact_prediction}).eq('id', player1_id).execute()

                    def update_player2():
                        return supabase.table(table_name).update({"Header": compact_prediction}).eq('id', player2_id).execute()

                    update_result1 = retry_supabase_operation(update_player1)
                    update_result2 = retry_supabase_operation(update_player2)

                    if update_result1.data and update_result2.data:
                        print(f"✅ SYNC BY NAMES: Successfully updated {table_name} table")
                        return True
                    else:
                        print(f"❌ SYNC BY NAMES: Failed to update {table_name} table")
                        return False
                else:
                    print(f"❌ SYNC BY NAMES: Missing player IDs in {table_name}")
                    return False

        print(f"⚠️ SYNC BY NAMES: Players not found in {table_name}")
        return False

    except Exception as e:
        print(f"❌ SYNC BY NAMES: Error syncing to {match_table}: {str(e)}")
        return False


def manage_prediction_unified(match_table, match_index, prediction_data, is_women=False):
    """
    Unified prediction management system - handles match tables only
    """
    try:
        print(f"\n🎯 UNIFIED PREDICTION MANAGEMENT")
        print(f"Table: {match_table}, Index: {match_index}, Women: {is_women}")
        print(f"Prediction Data: {prediction_data}")

        # Convert prediction data to compact string format (shortened keys to fit database limit)
        compact_data = {
            "w": prediction_data.get("winner", ""),
            "p1": prediction_data.get("player1_score", ""),
            "p2": prediction_data.get("player2_score", ""),
            "s": prediction_data.get("spread", ""),
            "n": prediction_data.get("notes", "")
        }
        compact_prediction = f"prediction:{json.dumps(compact_data, separators=(',', ':'))}"

        print(f"📏 Compact prediction length: {len(compact_prediction)} characters")
        print(f"📝 Compact prediction: {compact_prediction}")

        # Check if still too long for database (100 char limit)
        if len(compact_prediction) > 100:
            # Further compress by truncating notes if necessary
            max_notes_length = 100 - len(f"prediction:{json.dumps({k: v for k, v in compact_data.items() if k != 'n'}, separators=(',', ':'))}") - 10  # 10 chars buffer
            if max_notes_length > 0:
                compact_data["n"] = compact_data["n"][:max_notes_length]
            else:
                compact_data["n"] = ""  # Remove notes entirely if no space

            compact_prediction = f"prediction:{json.dumps(compact_data, separators=(',', ':'))}"
            print(f"📏 Truncated prediction length: {len(compact_prediction)} characters")
            print(f"📝 Truncated prediction: {compact_prediction}")

        # Determine table name
        if match_table == "predictions":
            table_name = "predictions"
        elif match_table == "today":
            table_name = "todays_matches_w" if is_women else "todays_matches"
        else:  # next
            table_name = "next_matches_w" if is_women else "next_matches"

        print(f"Using table: {table_name}")

        # Get all rows from the table with retry mechanism
        def get_table_data():
            return supabase.table(table_name).select('*').order('id').execute()

        all_rows = retry_supabase_operation(get_table_data)
        if not all_rows.data:
            return False, "No match data found"

        # Find the target match rows (player 1 and player 2)
        match_rows = []
        current_match = 0
        i = 0

        while i < len(all_rows.data):
            row = all_rows.data[i]

            # Skip header rows
            if row.get("Header", "") == "header":
                i += 1
                continue

            # This should be a player row
            if current_match == match_index:
                # Found our target match - get both players
                if i + 1 < len(all_rows.data):
                    player1_row = all_rows.data[i]
                    player2_row = all_rows.data[i + 1]

                    # Skip if next row is a header
                    if player2_row.get("Header", "") == "header":
                        return False, "Invalid match structure"

                    match_rows = [player1_row, player2_row]
                    break
                else:
                    return False, "Incomplete match data"

            # Skip to next match (skip both player rows)
            current_match += 1
            i += 2

        if not match_rows:
            return False, "Match not found"

        player1_row, player2_row = match_rows
        player1_id = player1_row["id"]
        player2_id = player2_row["id"]

        print(f"Found match: {player1_row.get('Name')} vs {player2_row.get('Name')}")
        print(f"Player IDs: {player1_id}, {player2_id}")

        # Update the table with prediction data using retry mechanism
        print(f"🔄 Updating {table_name} table...")

        def update_player1():
            return supabase.table(table_name).update({"Header": compact_prediction}).eq('id', player1_id).execute()

        def update_player2():
            return supabase.table(table_name).update({"Header": compact_prediction}).eq('id', player2_id).execute()

        update_result1 = retry_supabase_operation(update_player1)
        update_result2 = retry_supabase_operation(update_player2)

        if not update_result1.data or not update_result2.data:
            return False, f"Failed to update {table_name} table"

        print(f"✅ {table_name} table updated successfully")

        # If we're updating a match table (not predictions), also sync to predictions table
        if match_table != "predictions":
            # Step 2: Also update the predictions table to keep data synchronized
            print(f"🔄 Step 2: Updating predictions table...")
            try:
                # Always ensure the predictions table has the match data
                # First, find and ensure the header exists in predictions table
                print(f"🔍 Step 2a: Finding header for match {match_index}...")
                header_row, _ = find_header_for_match_in_table(all_rows.data, match_index)

                # Get current predictions table data with retry
                def get_predictions_data():
                    return supabase.table("predictions").select('*').order('id').execute()

                pred_all_rows = retry_supabase_operation(get_predictions_data)

                # Ensure header exists in predictions table (only if we found a header)
                if header_row:
                    print(f"📋 Found header: '{header_row.get('Name', '')}'")

                    # Check if this header already exists in predictions table
                    header_exists = False
                    if pred_all_rows.data:
                        for pred_row in pred_all_rows.data:
                            if (pred_row.get("Header", "") == "header" and
                                pred_row.get("Name", "") == header_row.get("Name", "")):
                                header_exists = True
                                print(f"📋 Header already exists in predictions table")
                                break

                    # If header doesn't exist, add it to predictions table FIRST
                    if not header_exists:
                        print(f"📋 Adding header to predictions table BEFORE player rows...")
                        header_data = {
                            "Time": header_row.get("Time", ""),
                            "Name": header_row.get("Name", ""),
                            "S": header_row.get("S", ""),
                            "1": header_row.get("1", ""),
                            "2": header_row.get("2", ""),
                            "3": header_row.get("3", ""),
                            "4": header_row.get("4", ""),
                            "5": header_row.get("5", ""),
                            "H2H": header_row.get("H2H", ""),
                            "H": header_row.get("H", ""),
                            "A": header_row.get("A", ""),
                            "Header": "header"  # Mark as header
                        }

                        header_insert_result = supabase.table("predictions").insert(header_data).execute()
                        if header_insert_result.data:
                            print(f"✅ Header added to predictions table successfully")
                            # Refresh predictions table data
                            pred_all_rows = supabase.table("predictions").select('*').order('id').execute()
                        else:
                            print(f"⚠️ Warning: Failed to add header to predictions table")
                else:
                    print(f"⚠️ Warning: No header found for match {match_index}")

                # Now find the same match in predictions table by matching player names
                pred_match_rows = []
                player1_name = player1_row.get("Name", "")
                player2_name = player2_row.get("Name", "")

                print(f"🔍 Looking for prediction rows with players: '{player1_name}' and '{player2_name}'")

                if pred_all_rows.data:
                    i = 0
                    while i < len(pred_all_rows.data):
                        row = pred_all_rows.data[i]

                        # Skip header rows
                        if row.get("Header", "") == "header":
                            i += 1
                            continue

                        # Check if this row matches player1
                        if row.get("Name", "") == player1_name:
                            # Found player1, check if next row is player2
                            if i + 1 < len(pred_all_rows.data):
                                next_row = pred_all_rows.data[i + 1]

                                # Skip if next row is a header
                                if next_row.get("Header", "") == "header":
                                    i += 1
                                    continue

                                # Check if next row matches player2
                                if next_row.get("Name", "") == player2_name:
                                    pred_match_rows = [row, next_row]
                                    print(f"✅ Found matching prediction rows by player names")
                                    break

                        i += 1

                # Handle updating existing predictions or creating new ones
                if pred_match_rows:
                    pred_player1_row, pred_player2_row = pred_match_rows
                    pred_player1_id = pred_player1_row["id"]
                    pred_player2_id = pred_player2_row["id"]

                    print(f"Found matching prediction rows: IDs {pred_player1_id}, {pred_player2_id}")

                    # Update predictions table with the same data
                    pred_update1 = supabase.table("predictions").update({"Header": compact_prediction}).eq('id', pred_player1_id).execute()
                    pred_update2 = supabase.table("predictions").update({"Header": compact_prediction}).eq('id', pred_player2_id).execute()

                    if pred_update1.data and pred_update2.data:
                        print(f"✅ Predictions table updated successfully")
                    else:
                        print(f"⚠️ Warning: Failed to update predictions table")
                else:
                    print(f"📋 No matching rows found in predictions table, creating new ones...")

                    # First, ensure the header exists in predictions table if we have one
                    if header_row:
                        # Check if this header already exists in predictions table
                        header_exists = False
                        if pred_all_rows.data:
                            for pred_row in pred_all_rows.data:
                                if (pred_row.get("Header", "") == "header" and
                                    pred_row.get("Name", "") == header_row.get("Name", "")):
                                    header_exists = True
                                    print(f"📋 Header already exists in predictions table")
                                    break

                        # If header doesn't exist, add it to predictions table FIRST
                        if not header_exists:
                            print(f"📋 Adding header to predictions table BEFORE creating new player rows...")
                            header_data = {
                                "Time": header_row.get("Time", ""),
                                "Name": header_row.get("Name", ""),
                                "S": header_row.get("S", ""),
                                "1": header_row.get("1", ""),
                                "2": header_row.get("2", ""),
                                "3": header_row.get("3", ""),
                                "4": header_row.get("4", ""),
                                "5": header_row.get("5", ""),
                                "H2H": header_row.get("H2H", ""),
                                "H": header_row.get("H", ""),
                                "A": header_row.get("A", ""),
                                "Header": "header"  # Mark as header
                            }

                            header_insert_result = supabase.table("predictions").insert(header_data).execute()
                            if header_insert_result.data:
                                print(f"✅ Header added to predictions table successfully")
                            else:
                                print(f"⚠️ Warning: Failed to add header to predictions table")

                    # Create new prediction rows based on the match table rows
                    player1_data = {
                        "Time": player1_row.get("Time", ""),
                        "Name": player1_row.get("Name", ""),
                        "S": player1_row.get("S", ""),
                        "1": player1_row.get("1", ""),
                        "2": player1_row.get("2", ""),
                        "3": player1_row.get("3", ""),
                        "4": player1_row.get("4", ""),
                        "5": player1_row.get("5", ""),
                        "H2H": player1_row.get("H2H", ""),
                        "H": player1_row.get("H", ""),
                        "A": player1_row.get("A", ""),
                        "Header": compact_prediction  # Add the prediction data
                    }

                    player2_data = {
                        "Time": player2_row.get("Time", ""),
                        "Name": player2_row.get("Name", ""),
                        "S": player2_row.get("S", ""),
                        "1": player2_row.get("1", ""),
                        "2": player2_row.get("2", ""),
                        "3": player2_row.get("3", ""),
                        "4": player2_row.get("4", ""),
                        "5": player2_row.get("5", ""),
                        "H2H": player2_row.get("H2H", ""),
                        "H": player1_row.get("H", ""),
                        "A": player2_row.get("A", ""),
                        "Header": compact_prediction  # Add the prediction data
                    }

                    # Insert both player rows
                    pred_insert1 = supabase.table("predictions").insert(player1_data).execute()
                    pred_insert2 = supabase.table("predictions").insert(player2_data).execute()

                    if pred_insert1.data and pred_insert2.data:
                        print(f"✅ New prediction rows created successfully in predictions table")
                    else:
                        print(f"⚠️ Warning: Failed to create new prediction rows")

            except Exception as pred_error:
                print(f"⚠️ Warning: Error updating predictions table: {str(pred_error)}")
                # Don't fail the whole operation if predictions table update fails

        # Reload data from Supabase to refresh the in-memory data
        print(f"🔄 Reloading data from Supabase...")
        if match_table == "predictions":
            # For predictions table, no need to reload match data
            print(f"✅ Predictions table updated, no match data reload needed")
        elif match_table == "today":
            load_todays_matches_from_supabase()  # This will reload both men and women data
        else:
            load_next_matches_from_supabase()  # This will reload next day data

        print(f"✅ Data reloaded successfully")
        print(f"✅ Unified prediction management completed successfully")
        return True, "Prediction saved successfully"

    except Exception as e:
        print(f"❌ Error in unified prediction management: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Error: {str(e)}"



def update_supabase_with_prediction(prediction_data, match_index, is_women):
    """Update Supabase database directly with prediction data for today's matches"""
    try:
        # Determine which table to use
        table_name = "todays_matches_w" if is_women else "todays_matches"

        # Get all rows from the table ordered by ID to ensure consistent ordering
        all_rows = supabase.table(table_name).select('*').order('id').execute()

        if not all_rows.data:
            print("No data found in Supabase table")
            return False, "No match data found in database"

        # Find the match rows by counting actual matches (skip headers)
        actual_match_count = 0
        target_player1_row = None
        target_player2_row = None

        i = 0
        while i < len(all_rows.data):
            current_row = all_rows.data[i]

            # Skip header rows - they contain column headers like "Time", "S", etc.
            # Header rows can be identified by:
            # 1. Having "Time" in the Time column
            # 2. Having "header" in any field
            # 3. Having column names like "S", "1", "2", etc. in the Name field

            # Check if this is a header row
            time_value = current_row.get('Time', '')
            name_value = current_row.get('Name', '')

            if (time_value == 'Time' or
                'header' in str(name_value).lower() or
                name_value in ['S', '1', '2', '3', '4', '5', 'H', 'A', 'H2H'] or
                'header' in str(time_value).lower()):
                print(f"Skipping header row: Time='{time_value}', Name='{name_value}'")
                i += 1
                continue

            # Check if this is a player1 row (followed by a player2 row)
            if i + 1 < len(all_rows.data):
                next_row = all_rows.data[i + 1]

                # Check if next row is also a header
                next_time_value = next_row.get('Time', '')
                next_name_value = next_row.get('Name', '')

                if (next_time_value == 'Time' or
                    'header' in str(next_name_value).lower() or
                    next_name_value in ['S', '1', '2', '3', '4', '5', 'H', 'A', 'H2H'] or
                    'header' in str(next_time_value).lower()):
                    print(f"Skipping next header row: Time='{next_time_value}', Name='{next_name_value}'")
                    i += 1
                    continue

                # This is a match (player1 + player2)
                if actual_match_count == match_index:
                    target_player1_row = current_row
                    target_player2_row = next_row
                    break

                actual_match_count += 1
                i += 2  # Skip both player rows
            else:
                i += 1

        if not target_player1_row or not target_player2_row:
            return False, "Match not found in database"

        # Update both player rows with the prediction
        player1_id = target_player1_row.get('id')
        player2_id = target_player2_row.get('id')

        # Use the "Header" column for predictions (as requested)
        available_columns = list(target_player1_row.keys())

        # First, clear any existing predictions from ALL columns in both rows
        # This ensures we don't have duplicate predictions
        clear_data = {}
        for col in available_columns:
            if col != 'id':
                # Check if either row has a prediction in this column
                player1_value = target_player1_row.get(col, '')
                player2_value = target_player2_row.get(col, '')

                if (isinstance(player1_value, str) and player1_value.startswith('prediction:')) or \
                   (isinstance(player2_value, str) and player2_value.startswith('prediction:')):
                    clear_data[col] = None

        # Clear existing predictions from both rows if any exist
        if clear_data:
            supabase.table(table_name).update(clear_data).eq('id', player1_id).execute()
            supabase.table(table_name).update(clear_data).eq('id', player2_id).execute()

        # Determine which column to use for the new prediction
        update_column = None

        # Use the "Header" column specifically for new predictions
        if 'Header' in available_columns:
            update_column = 'Header'
        else:
            # Fallback to other columns if Header doesn't exist
            excluded_columns = ['id', 'Time', 'Name']
            for col in available_columns:
                if col not in excluded_columns:
                    update_column = col
                    break

        if not update_column:
            return False, "No suitable column found to store prediction"

        # Create a compact prediction string that fits in database column (max 100 chars)
        # Use abbreviated keys to save space
        compact_data = {
            "w": prediction_data['winner'],  # winner
            "p1": prediction_data.get('player1_score', ''),  # player1_score
            "p2": prediction_data.get('player2_score', ''),  # player2_score
            "s": prediction_data.get('spread', ''),  # spread
            "n": prediction_data.get('notes', '')[:20] if prediction_data.get('notes') else ''  # notes (truncated)
        }

        # Remove empty fields to save more space
        compact_data = {k: v for k, v in compact_data.items() if v}

        prediction_json = json.dumps(compact_data, separators=(',', ':'))  # No spaces
        compact_prediction = f"prediction:{prediction_json}"

        # Ensure it's under database limits (100 characters)
        if len(compact_prediction) > 95:  # Leave some margin
            # Further truncate if still too long
            compact_data = {
                "w": prediction_data['winner'],  # Only keep winner
                "p1": prediction_data.get('player1_score', '')[:5],  # Truncate scores
                "p2": prediction_data.get('player2_score', '')[:5]
            }
            # Remove empty fields
            compact_data = {k: v for k, v in compact_data.items() if v}
            prediction_json = json.dumps(compact_data, separators=(',', ':'))
            compact_prediction = f"prediction:{prediction_json}"

        # Update player 1 row
        update_result1 = supabase.table(table_name).update({update_column: compact_prediction}).eq('id', player1_id).execute()

        # Update player 2 row
        update_result2 = supabase.table(table_name).update({update_column: compact_prediction}).eq('id', player2_id).execute()

        # Verify the updates were successful
        if not update_result1.data or not update_result2.data:
            return False, "Failed to update prediction in database"

        print(f"\n🔄 TODAY'S MATCHES SYNC DEBUG: Starting sync process")
        print(f"Table: {table_name}")
        print(f"Player 1 ID: {player1_id}, Player 2 ID: {player2_id}")
        print(f"Compact Prediction: {compact_prediction}")

        # Get the updated rows from the database for sync
        print(f"🔍 Fetching updated rows from database...")
        updated_player1 = supabase.table(table_name).select("*").eq('id', player1_id).execute()
        updated_player2 = supabase.table(table_name).select("*").eq('id', player2_id).execute()

        print(f"📊 Updated Player 1 result: {updated_player1}")
        print(f"📊 Updated Player 2 result: {updated_player2}")

        print(f"✅ Successfully updated both player rows in match table")

        # Also update the predictions table to keep data synchronized
        print(f"🔄 Updating predictions table with header...")
        try:
            # Check if predictions table exists and has data
            predictions_response = supabase.table("predictions").select('*').limit(1).execute()

            if predictions_response.data:
                print(f"📋 Predictions table exists, updating it as well...")

                # Find the corresponding header for this match
                header_row, _ = find_header_for_match_in_table(all_rows.data, match_index)

                if header_row:
                    print(f"📋 Found header: '{header_row.get('Name', '')}' for match {match_index}")

                    # Get current predictions table data
                    pred_all_rows = supabase.table("predictions").select('*').order('id').execute()

                    if pred_all_rows.data:
                        # Check if this header already exists in predictions table
                        header_exists = False
                        for pred_row in pred_all_rows.data:
                            if (pred_row.get("Header", "") == "header" and
                                pred_row.get("Name", "") == header_row.get("Name", "")):
                                header_exists = True
                                print(f"📋 Header already exists in predictions table")
                                break

                        # If header doesn't exist, add it to predictions table
                        if not header_exists:
                            print(f"📋 Adding header to predictions table...")
                            header_data = {
                                "Time": header_row.get("Time", ""),
                                "Name": header_row.get("Name", ""),
                                "S": header_row.get("S", ""),
                                "1": header_row.get("1", ""),
                                "2": header_row.get("2", ""),
                                "3": header_row.get("3", ""),
                                "4": header_row.get("4", ""),
                                "5": header_row.get("5", ""),
                                "H2H": header_row.get("H2H", ""),
                                "H": header_row.get("H", ""),
                                "A": header_row.get("A", ""),
                                "Header": "header"  # Mark as header
                            }

                            header_insert_result = supabase.table("predictions").insert(header_data).execute()
                            if header_insert_result.data:
                                print(f"✅ Header added to predictions table successfully")
                            else:
                                print(f"⚠️ Warning: Failed to add header to predictions table")
                else:
                    print(f"⚠️ Warning: No header found for match {match_index}")
            else:
                print(f"📋 Predictions table is empty or doesn't exist, skipping header update...")

        except Exception as pred_error:
            print(f"⚠️ Warning: Error updating predictions table with header: {str(pred_error)}")
            # Don't fail the whole operation if predictions table update fails

        # Reload data from Supabase to refresh the in-memory data
        load_todays_matches_from_supabase()

        return True, "Prediction saved successfully to database"

    except Exception as e:
        print(f"Error updating Supabase with prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Database error: {str(e)}"

def update_next_matches_supabase_with_prediction(prediction_data, match_index, is_women):
    """Update Supabase database directly with prediction data for next day's matches"""
    try:
        # Determine which table to use
        table_name = "next_matches_w" if is_women else "next_matches"

        # Get all rows from the table ordered by ID to ensure consistent ordering
        all_rows = supabase.table(table_name).select('*').order('id').execute()

        if not all_rows.data:
            print("No data found in Supabase table")
            return False, "No match data found in database"

        # Find the match rows by counting actual matches (skip headers)
        actual_match_count = 0
        target_player1_row = None
        target_player2_row = None

        i = 0
        while i < len(all_rows.data):
            current_row = all_rows.data[i]

            # Skip header rows - they contain column headers like "Time", "S", etc.
            # Header rows can be identified by:
            # 1. Having "Time" in the Time column
            # 2. Having "header" in any field
            # 3. Having column names like "S", "1", "2", etc. in the Name field

            # Check if this is a header row
            time_value = current_row.get('Time', '')
            name_value = current_row.get('Name', '')

            if (time_value == 'Time' or
                'header' in str(name_value).lower() or
                name_value in ['S', '1', '2', '3', '4', '5', 'H', 'A', 'H2H'] or
                'header' in str(time_value).lower()):
                print(f"Skipping header row: Time='{time_value}', Name='{name_value}'")
                i += 1
                continue

            # Check if this is a player1 row (followed by a player2 row)
            if i + 1 < len(all_rows.data):
                next_row = all_rows.data[i + 1]

                # Check if next row is also a header
                next_time_value = next_row.get('Time', '')
                next_name_value = next_row.get('Name', '')

                if (next_time_value == 'Time' or
                    'header' in str(next_name_value).lower() or
                    next_name_value in ['S', '1', '2', '3', '4', '5', 'H', 'A', 'H2H'] or
                    'header' in str(next_time_value).lower()):
                    print(f"Skipping next header row: Time='{next_time_value}', Name='{next_name_value}'")
                    i += 1
                    continue

                # This is a match (player1 + player2)
                if actual_match_count == match_index:
                    target_player1_row = current_row
                    target_player2_row = next_row
                    break

                actual_match_count += 1
                i += 2  # Skip both player rows
            else:
                i += 1

        if not target_player1_row or not target_player2_row:
            return False, "Match not found in database"

        # Update both player rows with the prediction
        player1_id = target_player1_row.get('id')
        player2_id = target_player2_row.get('id')

        # Use the "Header" column for predictions (as requested)
        available_columns = list(target_player1_row.keys())

        # First, clear any existing predictions from ALL columns in both rows
        # This ensures we don't have duplicate predictions
        clear_data = {}
        for col in available_columns:
            if col != 'id':
                # Check if either row has a prediction in this column
                player1_value = target_player1_row.get(col, '')
                player2_value = target_player2_row.get(col, '')

                if (isinstance(player1_value, str) and player1_value.startswith('prediction:')) or \
                   (isinstance(player2_value, str) and player2_value.startswith('prediction:')):
                    clear_data[col] = None

        # Clear existing predictions from both rows if any exist
        if clear_data:
            supabase.table(table_name).update(clear_data).eq('id', player1_id).execute()
            supabase.table(table_name).update(clear_data).eq('id', player2_id).execute()

        # Determine which column to use for the new prediction
        update_column = None

        # Use the "Header" column specifically for new predictions
        if 'Header' in available_columns:
            update_column = 'Header'
        else:
            # Fallback to other columns if Header doesn't exist
            excluded_columns = ['id', 'Time', 'Name']
            for col in available_columns:
                if col not in excluded_columns:
                    update_column = col
                    break

        if not update_column:
            return False, "No suitable column found to store prediction"

        # Create a compact prediction string that fits in database column (max 100 chars)
        # Use abbreviated keys to save space
        compact_data = {
            "w": prediction_data['winner'],  # winner
            "p1": prediction_data.get('player1_score', ''),  # player1_score
            "p2": prediction_data.get('player2_score', ''),  # player2_score
            "s": prediction_data.get('spread', ''),  # spread
            "n": prediction_data.get('notes', '')[:20] if prediction_data.get('notes') else ''  # notes (truncated)
        }

        # Remove empty fields to save more space
        compact_data = {k: v for k, v in compact_data.items() if v}

        prediction_json = json.dumps(compact_data, separators=(',', ':'))  # No spaces
        compact_prediction = f"prediction:{prediction_json}"

        # Ensure it's under database limits (100 characters)
        if len(compact_prediction) > 95:  # Leave some margin
            # Further truncate if still too long
            compact_data = {
                "w": prediction_data['winner'],  # Only keep winner
                "p1": prediction_data.get('player1_score', '')[:5],  # Truncate scores
                "p2": prediction_data.get('player2_score', '')[:5]
            }
            # Remove empty fields
            compact_data = {k: v for k, v in compact_data.items() if v}
            prediction_json = json.dumps(compact_data, separators=(',', ':'))
            compact_prediction = f"prediction:{prediction_json}"

        # Update player 1 row
        update_result1 = supabase.table(table_name).update({update_column: compact_prediction}).eq('id', player1_id).execute()

        # Update player 2 row
        update_result2 = supabase.table(table_name).update({update_column: compact_prediction}).eq('id', player2_id).execute()

        # Verify the updates were successful
        if not update_result1.data or not update_result2.data:
            return False, "Failed to update prediction in database"

        print(f"\n🔄 NEXT MATCHES SYNC DEBUG: Starting sync process")
        print(f"Table: {table_name}")
        print(f"Player 1 ID: {player1_id}, Player 2 ID: {player2_id}")
        print(f"Compact Prediction: {compact_prediction}")

        # Get the updated rows from the database for sync
        print(f"🔍 Fetching updated rows from database...")
        updated_player1 = supabase.table(table_name).select("*").eq('id', player1_id).execute()
        updated_player2 = supabase.table(table_name).select("*").eq('id', player2_id).execute()

        print(f"📊 Updated Player 1 result: {updated_player1}")
        print(f"📊 Updated Player 2 result: {updated_player2}")

        print(f"✅ Successfully updated both player rows in next matches table")

        # Also update the predictions table to keep data synchronized
        print(f"🔄 Updating predictions table with header...")
        try:
            # Check if predictions table exists and has data
            predictions_response = supabase.table("predictions").select('*').limit(1).execute()

            if predictions_response.data:
                print(f"📋 Predictions table exists, updating it as well...")

                # Find the corresponding header for this match
                header_row, _ = find_header_for_match_in_table(all_rows.data, match_index)

                if header_row:
                    print(f"📋 Found header: '{header_row.get('Name', '')}' for match {match_index}")

                    # Get current predictions table data
                    pred_all_rows = supabase.table("predictions").select('*').order('id').execute()

                    if pred_all_rows.data:
                        # Check if this header already exists in predictions table
                        header_exists = False
                        for pred_row in pred_all_rows.data:
                            if (pred_row.get("Header", "") == "header" and
                                pred_row.get("Name", "") == header_row.get("Name", "")):
                                header_exists = True
                                print(f"📋 Header already exists in predictions table")
                                break

                        # If header doesn't exist, add it to predictions table
                        if not header_exists:
                            print(f"📋 Adding header to predictions table...")
                            header_data = {
                                "Time": header_row.get("Time", ""),
                                "Name": header_row.get("Name", ""),
                                "S": header_row.get("S", ""),
                                "1": header_row.get("1", ""),
                                "2": header_row.get("2", ""),
                                "3": header_row.get("3", ""),
                                "4": header_row.get("4", ""),
                                "5": header_row.get("5", ""),
                                "H2H": header_row.get("H2H", ""),
                                "H": header_row.get("H", ""),
                                "A": header_row.get("A", ""),
                                "Header": "header"  # Mark as header
                            }

                            header_insert_result = supabase.table("predictions").insert(header_data).execute()
                            if header_insert_result.data:
                                print(f"✅ Header added to predictions table successfully")
                            else:
                                print(f"⚠️ Warning: Failed to add header to predictions table")
                else:
                    print(f"⚠️ Warning: No header found for match {match_index}")
            else:
                print(f"📋 Predictions table is empty or doesn't exist, skipping header update...")

        except Exception as pred_error:
            print(f"⚠️ Warning: Error updating predictions table with header: {str(pred_error)}")
            # Don't fail the whole operation if predictions table update fails

        # Reload data from Supabase to refresh the in-memory data
        load_next_matches_from_supabase()

        return True, "Next day prediction saved successfully to database"

    except Exception as e:
        return False, f"Database error: {str(e)}"

# Add this route to handle saving predictions
@app.route("/save_prediction", methods=['POST'])
@login_required
def save_prediction():

    try:
        # Declare globals at the beginning of the function
        global todayMatchesData, todayMatchesData_w
        global nextMatchesData, nextMatchesData_w

        # Get data from request
        data = request.json
        match_index = int(data.get('match_index'))
        is_women = data.get('is_women') == True
        is_next_day = data.get('is_next_day') == True
        is_profile = data.get('is_profile') == True or data.get('is_profile') == 'true'  # New parameter for profile page predictions
        winner = data.get('winner', '')
        player1_score = data.get('player1_score', '')
        player2_score = data.get('player2_score', '')
        spread = data.get('spread', '')
        notes = data.get('notes', '')




        # Validate required fields
        if not winner:
            return jsonify({"success": False, "error": "Winner is required"})

        # Format prediction data as a JSON object (same as reference implementation)
        prediction_data = {
            "winner": winner,
            "player1_score": player1_score,
            "player2_score": player2_score,
            "spread": spread,
            "notes": notes
        }

        # Convert to string format: "prediction:JSON_DATA" (exactly same as reference implementation)
        prediction_string = f"prediction:{json.dumps(prediction_data)}"

        # Get the correct in-memory data based on gender and day
        if is_next_day:
            if is_women:
                matches_data = nextMatchesData_w
            else:
                matches_data = nextMatchesData
        else:
            if is_women:
                matches_data = todayMatchesData_w
            else:
                matches_data = todayMatchesData

        # Find the match in the in-memory data and add prediction string to both player rows
        actual_match_count = 0
        target_match_index = None

        for i, item in enumerate(matches_data):
            # Skip header rows
            if isinstance(item, list) and len(item) == 1 and item[0][-1] == "header":
                continue

            # This is a match
            if actual_match_count == match_index:
                target_match_index = i
                break

            actual_match_count += 1

        if target_match_index is None:
            return jsonify({"success": False, "error": f"Match with index {match_index} not found"})

        # Get the match data
        match_data = matches_data[target_match_index]

        if len(match_data) < 2:
            return jsonify({"success": False, "error": "Invalid match data structure"})

        # Remove any existing prediction from both player rows
        player1_row = [item for item in match_data[0] if not (isinstance(item, str) and item.startswith('prediction:'))]
        player2_row = [item for item in match_data[1] if not (isinstance(item, str) and item.startswith('prediction:'))]

        # Add the new prediction string to both player rows
        player1_row.append(prediction_string)
        player2_row.append(prediction_string)

        # Update the match data
        match_data[0] = player1_row
        match_data[1] = player2_row

        # Update or add the prediction metadata (third element)
        if len(match_data) > 2:
            match_data[2] = {"has_prediction": True, "prediction_data": prediction_data}
        else:
            match_data.append({"has_prediction": True, "prediction_data": prediction_data})



        # Handle profile page predictions differently
        # For profile page predictions, we need to update both the predictions table
        # AND the corresponding original match table (today's or next day's)
        if is_profile:
            print(f"🔄 PROFILE PREDICTION: Starting dual-table update process")

            # First, update the predictions table
            print(f"🔄 Step 1: Updating predictions table...")
            upload_success, upload_message = manage_prediction_unified("predictions", match_index, prediction_data, is_women)

            if upload_success:
                print(f"✅ Step 1 completed: Predictions table updated successfully")

                # Now find the player names from the predictions table to locate the match in original tables
                print(f"🔄 Step 2: Finding player names for match synchronization...")
                try:
                    # Get the prediction match data to extract player names
                    pred_response = retry_supabase_operation(lambda: supabase.table("predictions").select('*').order('id').execute())
                    if pred_response and pred_response.data:
                        # Find the match by counting actual matches (skip headers)
                        actual_match_count = 0
                        player1_name = None
                        player2_name = None

                        i = 0
                        while i < len(pred_response.data):
                            row = pred_response.data[i]

                            # Skip header rows
                            if row.get("Header", "") == "header":
                                i += 1
                                continue

                            # This should be a player row
                            if actual_match_count == match_index:
                                # Found our target match - get both players
                                if i + 1 < len(pred_response.data):
                                    player1_row = pred_response.data[i]
                                    player2_row = pred_response.data[i + 1]

                                    # Skip if next row is a header
                                    if player2_row.get("Header", "") == "header":
                                        print(f"⚠️ Invalid match structure in predictions table")
                                        break

                                    player1_name = player1_row.get("Name", "")
                                    player2_name = player2_row.get("Name", "")
                                    print(f"🔍 Found match players: '{player1_name}' vs '{player2_name}'")
                                    break
                                else:
                                    print(f"⚠️ Incomplete match data in predictions table")
                                    break

                            # Skip to next match (skip both player rows)
                            actual_match_count += 1
                            i += 2

                        if player1_name and player2_name:
                            # Now use player names to find and update the match in original tables
                            original_table_updated = False

                            print(f"🔄 Step 3: Searching for match in original tables using player names...")

                            # ONLY use the new player name matching approach - don't use the old index-based approach
                            # Try today's matches first using player name matching
                            try:
                                print(f"🔄 Step 3a: Searching today's matches table using player names...")
                                today_success = sync_prediction_by_player_names("today", player1_name, player2_name, prediction_data, is_women)
                                if today_success:
                                    original_table_updated = True
                                    print(f"✅ Profile prediction synced to today's matches table using player names")
                            except Exception as e:
                                print(f"⚠️ Could not sync to today's matches table using player names: {str(e)}")

                            # If not found in today's matches, try next day's matches using player name matching
                            if not original_table_updated:
                                try:
                                    print(f"🔄 Step 3b: Searching next day's matches table using player names...")
                                    next_success = sync_prediction_by_player_names("next", player1_name, player2_name, prediction_data, is_women)
                                    if next_success:
                                        original_table_updated = True
                                        print(f"✅ Profile prediction synced to next day's matches table using player names")
                                except Exception as e:
                                    print(f"⚠️ Could not sync to next day's matches table using player names: {str(e)}")

                            if not original_table_updated:
                                print(f"⚠️ Warning: Could not find matching players in original tables")
                            else:
                                print(f"✅ PROFILE PREDICTION: Dual-table sync completed successfully using player names")
                        else:
                            print(f"⚠️ Warning: Could not extract player names from predictions table")
                    else:
                        print(f"⚠️ Warning: Could not retrieve predictions table data")

                except Exception as e:
                    print(f"⚠️ Error during player name extraction: {str(e)}")
            else:
                print(f"❌ Step 1 failed: Could not update predictions table: {upload_message}")

            return jsonify({
                'success': upload_success,
                'message': upload_message,
                'reload_needed': True  # Always reload for profile predictions
            })
        else:
            # Determine which table to update based on the request
            if is_next_day:
                match_table = "next"
            else:
                match_table = "today"

            # Use the new unified prediction management system
            upload_success, upload_message = manage_prediction_unified(match_table, match_index, prediction_data, is_women)

            # ALWAYS check if this prediction should also be synchronized to other tables
            # This ensures that predictions are consistent across all tables
            print(f"🔄 SYNC: Starting synchronization for {match_table} table...")

            # If we updated predictions table, try to sync to original match tables
            if match_table == "predictions":
                try:
                    today_success, _ = manage_prediction_unified("today", match_index, prediction_data, is_women)
                    if today_success:
                        print(f"✅ SYNC: Prediction also updated in today's matches")
                except Exception as e:
                    print(f"⚠️ SYNC: Error updating today's matches: {str(e)}")

                try:
                    next_success, _ = manage_prediction_unified("next", match_index, prediction_data, is_women)
                    if next_success:
                        print(f"✅ SYNC: Prediction also updated in next day's matches")
                except Exception as e:
                    print(f"⚠️ SYNC: Error updating next day's matches: {str(e)}")

            # If we updated today's or next day's matches, try to sync to predictions table
            elif match_table in ["today", "next"]:
                try:
                    pred_success, _ = manage_prediction_unified("predictions", match_index, prediction_data, is_women)
                    if pred_success:
                        print(f"✅ SYNC: Prediction also updated in predictions table")
                except Exception as e:
                    print(f"⚠️ SYNC: Error updating predictions table: {str(e)}")

                # Also try to sync to the other match table
                other_table = "next" if match_table == "today" else "today"
                try:
                    other_success, _ = manage_prediction_unified(other_table, match_index, prediction_data, is_women)
                    if other_success:
                        print(f"✅ SYNC: Prediction also updated in {other_table}'s matches")
                except Exception as e:
                    print(f"⚠️ SYNC: Error updating {other_table}'s matches: {str(e)}")

        if not upload_success:
            return jsonify({"success": False, "error": f"Failed to save prediction: {upload_message}"})

        # Reload data from Supabase to refresh the in-memory data
        if is_profile:
            # For profile predictions, reload both today's and next day's matches
            # since we don't know which table was updated
            load_todays_matches_from_supabase()
            load_next_matches_from_supabase()
        elif is_next_day:
            load_next_matches_from_supabase()
        else:
            load_todays_matches_from_supabase()

        return jsonify({
            "success": True,
            "message": "Prediction saved and synced successfully!",
            "reload_needed": True
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def reupload_todays_matches_to_supabase(is_women=False):
    """Reupload today's matches data to Supabase"""
    try:
        file_name = "todaysMatches_w.csv" if is_women else "todaysMatches.csv"
        table_name = "todays_matches_w" if is_women else "todays_matches"
        
        # Read the CSV file
        rows = []
        with open(file_name, 'r') as file:
            csvreader = csv.reader(file)
            rows = list(csvreader)
        
        # Clear the table first
        supabase.table(table_name).delete().neq('id', 0).execute()
        
        # Insert rows one by one
        for row in rows:
            # Skip empty rows
            if not row:
                continue
                
            # Create a dictionary for the row
            row_dict = {}
            
            # Add each column with a generic name
            for j, value in enumerate(row):
                if j == 0:
                    row_dict["Date&Time"] = value
                elif j == 1:
                    row_dict["Name"] = value
                else:
                    row_dict[f"Column{j}"] = value
            
            # Insert the row
            supabase.table(table_name).insert(row_dict).execute()
            
        # Reload the data from Supabase
        load_todays_matches_from_supabase()

        return True
    except Exception:
        return False



# Single route for reuploading today's matches
@app.route("/reupload_todays_matches")
@login_required
def reupload_todays_matches():
    """Force reupload of today's match data to Supabase"""
    men_result = reupload_todays_matches_to_supabase(is_women=False)
    women_result = reupload_todays_matches_to_supabase(is_women=True)

    if men_result and women_result:
        flash("Today's matches data reuploaded to Supabase successfully!", "success")
    else:
        flash("Error reuploading today's matches data to Supabase.", "danger")

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
    with open("todaysMatches.csv") as file:
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
    with open("todaysMatches_w.csv") as file:
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

    # Reload next matches from Supabase
    load_next_matches_from_supabase()

    # Reload previous matches if counter > 0
    prevMatchesData = []
    prevMatchesData_w = []
    with open("previousMatchesCounter") as file:
        prevCounter = int(file.read())
    
    if prevCounter > 0:
        with open(f"./Previous_Matches/{prevCounter}.csv") as file:
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
                    
        with open(f"./Previous_Matches/{prevCounter}_w.csv") as file:
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





# Add a diagnostic route to check Supabase connection and data
@app.route("/check_supabase")
@login_required
def check_supabase():
    try:
        # Check connection to Supabase
        supabase.table('todays_matches').select('*').limit(1).execute()

        # Get table structure
        men_structure = {}
        women_structure = {}

        # Get a sample row from men's table
        men_response = supabase.table('todays_matches').select('*').limit(1).execute()
        if men_response.data and len(men_response.data) > 0:
            men_structure = men_response.data[0]

        # Get a sample row from women's table
        women_response = supabase.table('todays_matches_w').select('*').limit(1).execute()
        if women_response.data and len(women_response.data) > 0:
            women_structure = women_response.data[0]

        # Count rows in each table
        men_count_response = supabase.table('todays_matches').select('count', count='exact').execute()
        women_count_response = supabase.table('todays_matches_w').select('count', count='exact').execute()

        men_count = men_count_response.count if hasattr(men_count_response, 'count') else 'Unknown'
        women_count = women_count_response.count if hasattr(women_count_response, 'count') else 'Unknown'

        # Force reload data
        load_todays_matches_from_supabase()

        # Return diagnostic information
        return jsonify({
            "connection": "success",
            "men_table_count": men_count,
            "women_table_count": women_count,
            "men_sample_structure": men_structure,
            "women_sample_structure": women_structure,
            "todayMatchesData_length": len(todayMatchesData),
            "todayMatchesData_w_length": len(todayMatchesData_w)
        })
    except Exception as e:
        return jsonify({
            "connection": "failed",
            "error": str(e)
        })

# Add a debug route to check in-memory data structure
@app.route("/debug_data")
@login_required
def debug_data():
    try:
        # Check the first few matches in todayMatchesData
        debug_info = {
            "todayMatchesData_length": len(todayMatchesData),
            "todayMatchesData_w_length": len(todayMatchesData_w),
            "sample_matches": []
        }

        # Show first 3 matches from men's data
        for i, match in enumerate(todayMatchesData[:3]):
            if isinstance(match, list):
                if len(match) == 1 and match[0][-1] == "header":
                    debug_info["sample_matches"].append({
                        "index": i,
                        "type": "header",
                        "data": match[0][:3]  # First 3 elements
                    })
                elif len(match) >= 2:
                    match_info = {
                        "index": i,
                        "type": "match",
                        "player1_name": match[0][1] if len(match[0]) > 1 else "Unknown",
                        "player2_name": match[1][1] if len(match[1]) > 1 else "Unknown",
                        "has_prediction_metadata": len(match) > 2,
                    }

                    if len(match) > 2:
                        match_info["prediction_metadata"] = match[2]

                    # Check if prediction data is in player rows
                    prediction_in_rows = False
                    for row in match[:2]:
                        for item in row:
                            if isinstance(item, str) and item.startswith('prediction:'):
                                prediction_in_rows = True
                                match_info["prediction_in_rows"] = True
                                match_info["prediction_data"] = item[:50] + "..."
                                break
                        if prediction_in_rows:
                            break

                    debug_info["sample_matches"].append(match_info)

        return jsonify(debug_info)
    except Exception as e:
        return jsonify({
            "error": str(e)
        })


# PREDICTIONS TABLE ROUTES
@app.route("/predictions")
@login_required
def predictions_table():
    """Display the predictions table with editing capabilities"""
    try:
        # Get all rows from the predictions table
        response = supabase.table("predictions").select('*').order('id').execute()

        if response.data:
            predictions_data = response.data
        else:
            predictions_data = []

        return render_template("predictions_table.html", predictions_data=predictions_data)

    except Exception as e:
        print(f"Error loading predictions table: {str(e)}")
        flash(f"Error loading predictions table: {str(e)}", "danger")
        return redirect(url_for('searchPlayer'))


@app.route("/edit_prediction_row", methods=['POST'])
@login_required
def edit_prediction_row():
    """Edit a specific row in the predictions table and sync to original match tables"""
    try:
        data = request.json
        row_id = data.get('row_id')
        updated_data = data.get('updated_data', {})

        if not row_id:
            return jsonify({"success": False, "error": "Row ID is required"})

        if not updated_data:
            return jsonify({"success": False, "error": "No valid data to update"})

        # Define allowed columns for editing (exclude id)
        allowed_columns = ['Time', 'Name', 'S', '1', '2', '3', '4', '5', 'H2H', 'H', 'A', 'Header']

        # Filter to only allowed columns
        filtered_data = {}
        for column, value in updated_data.items():
            if column in allowed_columns:
                # Convert empty strings to None for database
                filtered_data[column] = value if value.strip() else None

        if not filtered_data:
            return jsonify({"success": False, "error": "No valid columns to update"})

        # First, get the current row data to understand what we're updating
        current_row_result = supabase.table("predictions").select('*').eq('id', row_id).execute()
        if not current_row_result.data:
            return jsonify({"success": False, "error": "Row not found in predictions table"})

        # Update the row in Supabase predictions table
        result = supabase.table("predictions").update(filtered_data).eq('id', row_id).execute()

        if not result.data:
            return jsonify({"success": False, "error": "Failed to update row in predictions table"})

        print(f"✅ Successfully updated predictions table row {row_id}")

        # Now sync the changes to original match tables if this is a prediction update
        # Check if the Header column was updated (contains prediction data)
        if 'Header' in filtered_data and filtered_data['Header']:
            try:
                print(f"🔄 SYNC: Starting synchronization for prediction edit...")

                # Parse the prediction data from the Header column
                header_value = filtered_data['Header']
                if header_value and ('prediction:' in str(header_value) or '{' in str(header_value)):
                    # Try to extract prediction data
                    prediction_data = None

                    if 'prediction:' in str(header_value):
                        # Old format: prediction:{"w":"Player1","p1":"6-4","p2":"6-2","s":"","n":""}
                        try:
                            pred_part = str(header_value).split('prediction:')[1]
                            prediction_data = json.loads(pred_part)
                        except:
                            print(f"⚠️ Could not parse old format prediction data")
                    elif '{' in str(header_value):
                        # New compact format: {"w":"Player1","p1":"6-4","p2":"6-2","s":"","n":""}
                        try:
                            prediction_data = json.loads(str(header_value))
                        except:
                            print(f"⚠️ Could not parse new format prediction data")

                    if prediction_data:
                        # Convert compact format back to full format for sync
                        full_prediction_data = {
                            "winner": prediction_data.get("w", ""),
                            "player1_score": prediction_data.get("p1", ""),
                            "player2_score": prediction_data.get("p2", ""),
                            "spread": prediction_data.get("s", ""),
                            "notes": prediction_data.get("n", "")
                        }

                        print(f"🔄 SYNC: Extracted prediction data: {full_prediction_data}")

                        # Find the match index by looking for the paired row in predictions table
                        # Get all predictions table rows to find the match pair
                        all_predictions = supabase.table("predictions").select('*').order('id').execute()
                        if all_predictions.data:
                            # Find the current row and its pair
                            current_index = None
                            for i, row in enumerate(all_predictions.data):
                                if row['id'] == int(row_id):
                                    current_index = i
                                    break

                            if current_index is not None:
                                # Calculate match index (every 2 rows = 1 match, but account for headers)
                                match_index = 0
                                actual_match_rows = 0

                                for i in range(current_index + 1):  # Include current row
                                    row = all_predictions.data[i]
                                    # Skip header rows (they have index -1 or specific header indicators)
                                    if (row.get('Name') and
                                        not str(row.get('Name', '')).startswith('Tournament:') and
                                        not str(row.get('Name', '')).startswith('Round:') and
                                        row.get('Name') != 'Header'):
                                        actual_match_rows += 1

                                match_index = (actual_match_rows - 1) // 2  # Convert to 0-based match index

                                print(f"🔄 SYNC: Calculated match index: {match_index}")

                                # Try to sync to both today's and next day's matches
                                sync_success = False

                                # Try women's tables first, then men's tables
                                for is_women in [True, False]:
                                    if sync_success:
                                        break

                                    # Try today's matches
                                    try:
                                        today_success, _ = manage_prediction_unified("today", match_index, full_prediction_data, is_women)
                                        if today_success:
                                            sync_success = True
                                            print(f"✅ SYNC: Prediction synced to today's matches ({'women' if is_women else 'men'})")
                                            break
                                    except Exception as e:
                                        print(f"⚠️ SYNC: Could not sync to today's matches ({'women' if is_women else 'men'}): {str(e)}")

                                    # Try next day's matches
                                    try:
                                        next_success, _ = manage_prediction_unified("next", match_index, full_prediction_data, is_women)
                                        if next_success:
                                            sync_success = True
                                            print(f"✅ SYNC: Prediction synced to next day's matches ({'women' if is_women else 'men'})")
                                            break
                                    except Exception as e:
                                        print(f"⚠️ SYNC: Could not sync to next day's matches ({'women' if is_women else 'men'}): {str(e)}")

                                if not sync_success:
                                    print(f"⚠️ SYNC: Could not sync prediction to any original match table")
                            else:
                                print(f"⚠️ SYNC: Could not find current row in predictions table")
                        else:
                            print(f"⚠️ SYNC: Could not retrieve predictions table data for sync")
                    else:
                        print(f"⚠️ SYNC: Could not extract prediction data from Header column")
                else:
                    print(f"🔄 SYNC: Header update does not contain prediction data, skipping sync")

            except Exception as sync_error:
                print(f"⚠️ SYNC: Error during synchronization: {str(sync_error)}")
                # Don't fail the whole operation if sync fails
                import traceback
                traceback.print_exc()

        return jsonify({"success": True, "message": "Row updated successfully and synced to match tables"})

    except Exception as e:
        print(f"Error editing prediction row: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/delete_prediction_row", methods=['POST'])
@login_required
def delete_prediction_row():
    """Delete a specific row from the predictions table"""
    try:
        data = request.json
        row_id = data.get('row_id')

        if not row_id:
            return jsonify({"success": False, "error": "Row ID is required"})

        # Delete the row from Supabase
        result = supabase.table("predictions").delete().eq('id', row_id).execute()

        if result.data:
            return jsonify({"success": True, "message": "Row deleted successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to delete row from database"})

    except Exception as e:
        print(f"Error deleting prediction row: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


@app.route("/update_predictions_table")
@login_required
def update_predictions_table():
    """Trigger update of predictions table from today's matches"""
    try:
        # This could trigger a sync operation if needed
        # For now, just redirect back to the predictions table
        flash("Predictions table updated successfully", "success")
        return redirect(url_for('predictions_table'))

    except Exception as e:
        print(f"Error updating predictions table: {str(e)}")
        flash(f"Error updating predictions table: {str(e)}", "danger")
        return redirect(url_for('predictions_table'))


@app.route("/debug_player_predictions/<player_name>")
@login_required
def debug_player_predictions(player_name):
    """Debug route to check what predictions exist for a specific player"""
    try:
        decoded_name = player_name.replace("%20", " ")

        # Get all predictions from predictions table
        response = supabase.table("predictions").select('*').order('id').execute()
        all_predictions = response.data if response.data else []

        # Get all predictions from todays_matches table
        today_response = supabase.table("todays_matches").select('*').order('id').execute()
        today_predictions = today_response.data if today_response.data else []

        # Filter predictions that contain this player's name
        player_predictions = []
        today_player_predictions = []

        for row in all_predictions:
            if decoded_name.lower() in str(row.get('Name', '')).lower():
                player_predictions.append(row)

        for row in today_predictions:
            if decoded_name.lower() in str(row.get('Name', '')).lower():
                today_player_predictions.append(row)

        debug_info = {
            "player_name": decoded_name,
            "predictions_table_total_rows": len(all_predictions),
            "todays_matches_total_rows": len(today_predictions),
            "predictions_table_player_rows": len(player_predictions),
            "todays_matches_player_rows": len(today_player_predictions),
            "predictions_table_rows": player_predictions,
            "todays_matches_rows": today_player_predictions,
            "predictions_with_data": [],
            "todays_matches_with_data": []
        }

        # Check which rows have actual prediction data
        for row in player_predictions:
            if row.get('Header', '') and 'prediction:' in str(row.get('Header', '')):
                debug_info["predictions_with_data"].append(row)

        for row in today_player_predictions:
            if row.get('Header', '') and 'prediction:' in str(row.get('Header', '')):
                debug_info["todays_matches_with_data"].append(row)

        return jsonify(debug_info)

    except Exception as e:
        return jsonify({"error": str(e)})


# RUNNING THE APP
if __name__ == "__main__":
    app.run(debug=False)
