def __init__ (self):
    myBotFiles = ["Score_m1p1.txt", "Score_m2p1.txt", "Score_m3p1.txt", "Score_m4p1.txt",
             "Score_m1p2.txt", "Score_m2p2.txt", "Score_m3p2.txt", "Score_m4p2.txt",
             "Score_m1p3.txt", "Score_m2p3.txt", "Score_m3p3.txt", "Score_m4p3.txt",
             "Score_m1p4.txt", "Score_m2p4.txt", "Score_m3p4.txt","Score_m4p4.txt"]
    
    PyFredFiles = ["ScoreOpponent_m1p1.txt", "ScoreOpponent_m2p1.txt", "ScoreOpponent_m3p1.txt", "ScoreOpponent_m4p1.txt",
             "ScoreOpponent_m1p2.txt", "ScoreOpponent_m2p2.txt", "ScoreOpponent_m3p2.txt", "ScoreOpponent_m4p2.txt",
             "ScoreOpponent_m1p3.txt", "ScoreOpponent_m2p3.txt", "ScoreOpponent_m3p3.txt", "ScoreOpponent_m4p3.txt",
             "ScoreOpponent_m1p4.txt", "ScoreOpponent_m2p4.txt", "ScoreOpponent_m3p4.txt","ScoreOpponent_m4p4.txt"]
    
    myBotScore = []
    PyBotScore = []
    
    for i in myBotFiles:
        file = open(i)
        score = 0
        for line in file:
            score += line
        myBotScore.append(score)
    for i in PyFredFiles:
        file = open(i)
        score = 0
        for line in file:
            score += line
        PyBotScore.appent(score)