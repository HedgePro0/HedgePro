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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        
        response = supabase.table('todays_matches').select('*').execute()

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
                        print(f"Added prediction data to match at index {len(todayMatchesData)}")
                    else:
                        match.append({"has_prediction": False, "prediction_data": None})
                    
                    todayMatchesData.append(match)
        else:
            print("No data found in todays_matches table")
        
        '''
        Loading the women's data for todays matches from supabase
        '''
        response = supabase.table('todays_matches_w').select('*').execute()

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

        response = supabase.table('next_matches').select('*').order('id').execute()

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
        response = supabase.table('next_matches_w').select('*').order('id').execute()

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



# PLAYER SEARCH PAGE (Login Required)
@app.route("/", methods=['GET', 'POST'])
@login_required
def searchPlayer():
    # Declare globals at the beginning of the function
    global todayMatchesData, todayMatchesData_w
    global nextMatchesData, nextMatchesData_w
    global prevMatchesData, prevMatchesData_w

    # Reload data from Supabase if needed
    if not todayMatchesData or not todayMatchesData_w:
        load_todays_matches_from_supabase()

    if not nextMatchesData or not nextMatchesData_w:
        load_next_matches_from_supabase()
    
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



        # For today's matches: Upload prediction to Supabase using the correct function
        if not is_next_day:
            upload_success, upload_message = update_supabase_with_prediction(prediction_data, match_index, is_women)

            if not upload_success:
                return jsonify({"success": False, "error": f"Failed to upload to Supabase: {upload_message}"})

            return jsonify({
                "success": True,
                "message": "Prediction saved successfully to database!",
                "reload_needed": True
            })

        # For next day matches: Update Supabase database using the new function
        else:
            upload_success, upload_message = update_next_matches_supabase_with_prediction(prediction_data, match_index, is_women)

            if not upload_success:
                return jsonify({"success": False, "error": f"Failed to upload to Supabase: {upload_message}"})

            return jsonify({
                "success": True,
                "message": "Next day prediction saved successfully to database!",
                "reload_needed": True
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

def update_csv_with_prediction(prediction_data, match_index, is_women, is_next_day):
    """Update CSV files with prediction data (secondary operation)"""
    try:
        # Convert to string format: "prediction:JSON_DATA"
        prediction_string = f"prediction:{json.dumps(prediction_data)}"

        # Determine which file to use
        if is_next_day:
            file_name = "nextMatches_w.csv" if is_women else "nextMatches.csv"
        else:
            file_name = "todaysMatches_w.csv" if is_women else "todaysMatches.csv"

        # Read the current CSV file
        with open(file_name, 'r') as file:
            csvreader = csv.reader(file)
            rows = list(csvreader)

        # Find the match rows
        actual_match_count = 0
        row1_index = None
        row2_index = None

        i = 0
        while i < len(rows):
            # Skip empty rows
            if not rows[i] or len(rows[i]) == 0:
                i += 1
                continue

            # Skip header rows
            if rows[i][-1] == "header":
                i += 1
                continue

            # Check if this is a player1 row (followed by a player2 row)
            if (i+1 < len(rows) and
                len(rows[i]) > 0 and
                len(rows[i+1]) > 0):

                # This is a match (player1 + player2)
                if actual_match_count == match_index:
                    # This is the match we want to update
                    row1_index = i
                    row2_index = i+1
                    break

                actual_match_count += 1
                i += 2  # Skip both player rows
            else:
                i += 1

        # Add the new prediction to both player rows
        if row1_index is not None and row2_index is not None:
            # Remove any existing prediction
            rows[row1_index] = [item for item in rows[row1_index] if not (isinstance(item, str) and item.startswith('prediction:'))]
            rows[row2_index] = [item for item in rows[row2_index] if not (isinstance(item, str) and item.startswith('prediction:'))]

            # Add the new prediction
            rows[row1_index].append(prediction_string)
            rows[row2_index].append(prediction_string)

            # Write back to the file
            with open(file_name, 'w', newline='') as file:
                csvwriter = csv.writer(file)
                csvwriter.writerows(rows)

            return True
        else:
            return False

    except Exception as e:
        return False

# Function to reupload today's matches to Supabase
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
    except Exception as e:
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





# RUNNING THE APP
if __name__ == "__main__":
    app.run(debug=False)
