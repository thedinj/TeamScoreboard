import urllib3
from datetime import date,datetime,timedelta
from bs4 import BeautifulSoup
import re

MAX_RETRIES = 10

_failCount = 0

def GetScoreForTeam(findTeamAbbr, dateToUse, etTimeZoneDelta):
    global _failCount
    result = GetScoreForTeamCore(findTeamAbbr, dateToUse, etTimeZoneDelta)
    if result[0] == False:
        _failCount = _failCount + 1
        if _failCount > MAX_RETRIES:  #there might not actually be a game today, and it's not just the website messing up
            print("Reached max retries ({})".format(MAX_RETRIES))
            _failCount = 0
            return [True, None]
    else:
        _failCount = 0
    return result

def GetScoreForTeamCore(findTeamAbbr, dateToUse, etTimeZoneDelta):
    try:
        urllib3.disable_warnings()  # turn off InsecureRequestWarning
        http = urllib3.PoolManager()
        url = "http://www.usatoday.com/sports/nba/scores/{}/{}/{}/".format(dateToUse.year, dateToUse.month, dateToUse.day)
        response = http.request('GET', url)
        
        text_file = open("/home/pi/TeamScoreboard/last_response.html", "w")
        text_file.write(response.data)
        text_file.close()
        
        if response.status != 200:
            print("Error: Response status = {}".format(response.status))
            return [False, None]
        
        soup = BeautifulSoup(response.data, features="lxml")
        
        canary = soup.find_all("article", id="scorespage")
        if canary == None or len(canary) < 1:
            print("Error: No <article id=\"scorespage\">")
            return [False, None]
    
        gameElements = soup.find_all("div", class_="game")
        if len(gameElements) < 1:
            print("Error: No <div class=\"game\">")
            return [False, None]
        
        foundAGame = False
        
        for gameIndex in range(0, len(gameElements)):
            gameElement = gameElements[gameIndex]
            if not ("/nba/" in gameElement.decode_contents()):  # why would they send us NHL scores??????
                continue
            foundAGame = True
            teamNameElements = gameElement.select(".teamname")
            if len(teamNameElements) > 1:
                teamA = gameElement.select(".teamname")[0].string.strip()
                teamB = gameElement.select(".teamname")[1].string.strip()
                if teamA == findTeamAbbr or teamB == findTeamAbbr:
                    return [True, ParseGame(gameElement, findTeamAbbr, dateToUse, etTimeZoneDelta)]
        
        if not foundAGame:
            return [False, None]
        
        print("No game today.")
        return [True, None]
    except Exception as e:
        print("Error: Exception = " + str(e))
        return [False, None]
    return [True, None]


def ParseGame(gameElement, findTeamAbbr, dateToUse, etTimeZoneDelta):
    startTime = None
    visitorTeamScore = None
    homeTeamScore = None
    period = None
    timeRem = None
    isFinal = False

    visitorTeamAbbr = gameElement.select(".teamname")[0].string.strip()
    homeTeamAbbr = gameElement.select(".teamname")[1].string.strip()

    startTimeElement = gameElement.find(class_="outcome first")
    startTimeRaw = startTimeElement.string.strip()
    regex = re.compile("\d?\d\:\d\d\D\D ET")
    matches = regex.findall(startTimeRaw)
    if len(matches) > 0:
        try:
            startTimeET = datetime.strptime(matches[0].replace(" ET",""), "%I:%M%p")
            startDateET = datetime(dateToUse.year, dateToUse.month, dateToUse.day, startTimeET.hour, startTimeET.minute)
            startTime = startDateET + timedelta(hours=etTimeZoneDelta)
        except:
            startTime = None

    scoreElements = gameElement.select(".outcomes.total")
    if len(scoreElements) > 1:
        visitorTeamScoreStr = scoreElements[0].string
        homeTeamScoreStr = scoreElements[1].string
        if visitorTeamScoreStr != None and len(visitorTeamScoreStr) > 0:
            visitorTeamScore = int(visitorTeamScoreStr.strip())
        if homeTeamScoreStr != None and len(homeTeamScoreStr) > 0:
            homeTeamScore = int(homeTeamScoreStr.strip())
    
    if homeTeamAbbr == findTeamAbbr:
        teamScore = homeTeamScore
        otherScore = visitorTeamScore
    else:
        teamScore = visitorTeamScore
        otherScore = homeTeamScore

    periodElement = startTimeElement.find_previous("li")
    if periodElement != None and periodElement.string != None and len(periodElement.string) > 0:
        period = periodElement.string.strip()
    
    timerElement = gameElement.find("h3")
    if timerElement != None and timerElement.string != None and len(timerElement.string) > 0:
        timerRaw = timerElement.string.strip()
        if timerRaw == "Final" or timerRaw == "Final OT":
            isFinal = True
        elif timerRaw == "Halftime":
            timeRem = "0:00"
        else:
            regex = re.compile("\d?\d\:\d\d")
            matches = regex.findall(timerRaw)
            if len(matches) > 0:
                timeRem = matches[0]

    return {
            "startTime": startTime,
            "visitorTeam": visitorTeamAbbr,
            "visitorScore": visitorTeamScore,
            "homeTeam": homeTeamAbbr,
            "homeScore": homeTeamScore,
            "isFinal": isFinal,
            "period": period,
            "timeRem": timeRem,
            "teamScore": teamScore,
            "otherScore": otherScore
           }

#fd = None
#def printToLog(*args, **kwargs):
#    global fd
#    if fd == None:
#        fd = open("/home/pi/TeamScoreboard/log.txt", "w", 0)
#    fd.write(*args)
    
if __name__ == '__main__':
  print(GetScoreForTeam("MIL", date.today(), -1)[1])
