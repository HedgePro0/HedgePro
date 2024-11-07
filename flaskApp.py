from flask import Flask, redirect, url_for, render_template, request, session, flash
import csv
import os
from datetime import timedelta
from functools import wraps 

app = Flask(__name__)
app.secret_key = '$4$4$4$6'  # Use a secure key for sessions
app.permanent_session_lifetime = timedelta(days=7)  # Session will last 7 days

# Simple credentials for your private use
USERNAME = 'Hedgepro44'
PASSWORD = '$4$4$4$6'

# Data Loading (Unchanged)
names = []
prevCounter = 0 
prevMatchesData = []
todayMatchesData = []
nextMatchesData = []
prevMatchesData_w = []
todayMatchesData_w = []
nextMatchesData_w = []
menRankedPlayers = []
femaleRankedPlayers = []

# Load Data (Unchanged)
with open("previousMatchesCounter") as file:
    prevCounter = int(file.read())
print(prevCounter)
    
if prevCounter > 0:
    for i in range(1, prevCounter+1):
        prevMatchesData.append([])
        with open(f"./Previous_Matches/{i}.csv") as file:
            csvreader = csv.reader(file)
            temp = []
            for row in csvreader:
                temp.append(row)
            j = 0
            while j < len(temp):
                if temp[j][-1] == "header":
                    prevMatchesData[i-1].append(temp[j])
                    j += 1
                else:
                    prevMatchesData[i-1].append([ temp[j], temp[j+1] ])
                    j += 2

        prevMatchesData_w.append([])
        with open(f"./Previous_Matches/{i}_w.csv") as file:
            csvreader = csv.reader(file)
            temp = []
            for row in csvreader:
                temp.append(row)
            j = 0
            while j < len(temp):
                if temp[j][-1] == "header":
                    prevMatchesData_w[i-1].append(temp[j])
                    j += 1
                else:
                    prevMatchesData_w[i-1].append([ temp[j], temp[j+1] ])
                    j += 2

for row in prevMatchesData:
    for elem in row:
        print(elem)
        
# Load other files (Unchanged)
with open('./playerLinks.csv') as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        names.append(row[0].lower())

with open("todaysMatches.csv") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < len(temp):
        if temp[i][-1] == "header":
            todayMatchesData.append(temp[i])
            i += 1
        else:
            todayMatchesData.append([ temp[i], temp[i+1] ])
            i += 2

with open("todaysMatches_w.csv") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < len(temp):
        if temp[i][-1] == "header":
            todayMatchesData_w.append(temp[i])
            i += 1
        else:
            todayMatchesData_w.append([ temp[i], temp[i+1] ])
            i += 2

with open("nextMatches.csv") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < len(temp):
        if temp[i][-1] == "header":
            nextMatchesData.append(temp[i])
            i += 1
        else:
            nextMatchesData.append([ temp[i], temp[i+1] ])
            i += 2

with open("nextMatches_w.csv") as file:
    temp = []
    csvreader = csv.reader(file)
    for row in csvreader:
        temp.append(row)
    i = 0
    while i < len(temp):
        if temp[i][-1] == "header":
            nextMatchesData_w.append(temp[i])
            i += 1
        else:
            nextMatchesData_w.append([ temp[i], temp[i+1] ])
            i += 2
    
with open("men_ranking.csv") as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        menRankedPlayers.append(row)
        
with open("women_ranking.csv") as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        femaleRankedPlayers.append(row)
    

def getData(name):
    # GETTING THE MATCH DATA FOR A PARTICULAR PERSON
    rows = []
    name = name.replace("%20", " ")
    with open(f'./FlashScore_database/{name}/match_details.csv') as file:
        csvreader = csv.reader(file)
        nextMatch = False
        length = 0
        temp_rows = []
        for row in csvreader:
            temp_rows.append(row)
        for i in range(len(temp_rows)):
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
    with open(f'./FlashScore_database/{name}/personal_details.csv') as file:
        csvreader = csv.reader(file)
        for row in csvreader:
            profileData.append(row)
        
    # GETTING THE SUMMARY TABLE FOR THE REQUIRED PLAYER
    summary = []
    with open(f'./FlashScore_database/{name}/career_details.csv') as file:
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
    return render_template('playerProfile.html', matches_info=matches_info, profileData=profileData, summary=summary)

# PLAYER SEARCH PAGE (Login Required)
@app.route("/", methods=['GET', 'POST'])
@login_required
def searchPlayer():
    if request.method == "POST":
        player_name = request.form.get("player_name")
        if player_name != "":
            return redirect(url_for('player_profile_page', name=player_name.lower()))
        
    return render_template('home.html', today_rows=todayMatchesData, next_rows=nextMatchesData, prev_rows=prevMatchesData, today_rows_w=todayMatchesData_w, next_rows_w=nextMatchesData_w, prev_rows_w=prevMatchesData_w)

# RANKED PLAYERS PAGE (Login Required)
@app.route("/ranked-players")
@login_required
def rankedPlayers():
    return render_template("ranked_players.html", men_data=menRankedPlayers, female_data=femaleRankedPlayers)

# RUNNING THE APP
if __name__ == "__main__":
    app.run(debug=True)
