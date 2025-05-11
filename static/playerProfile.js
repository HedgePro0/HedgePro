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