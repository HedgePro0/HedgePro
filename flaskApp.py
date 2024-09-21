from flask import Flask, redirect, url_for, render_template, request
import csv

names = []
with open('./PlayerNames.csv') as file:
    csvreader = csv.reader(file)
    for row in csvreader:
        names.append(row[0])
names = names[2120::]

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

# INITIALIZING FLASK APP
app = Flask(__name__)

@app.route('/<name>')
def player_profile_page(name):
    matches_info, profileData, summary = getData(name)
    return render_template('playerProfile.html', matches_info = matches_info, profileData = profileData, summary = summary)

# PLAYER SEARCH PAGE
@app.route("/", methods = ['GET', 'POST'])
def searchPlayer():
    if request.method == "POST":
        player_name = request.form.get("player_name")
        if player_name != "":
            return redirect(url_for('player_profile_page', name = player_name.lower()))
    
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)