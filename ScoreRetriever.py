import urllib3
from urllib3 import PoolManager, HTTPResponse
from bs4 import BeautifulSoup, Tag
from datetime import date, datetime, timedelta
import re
import time

SCORE_URL = "http://www.usatoday.com/sports/nba/scores/{}/{}/{}/"

class Score(object):
    StartTime: datetime = None
    
    Period: str = ""
    TimeRemaining: str = ""

    IsFinal: bool = False

    AwayTeamAbbr: str = ""
    HomeTeamAbbr: str = ""
    
    AwayScore: int = 0
    HomeScore: int = 0

    TeamScore: int = 0
    OtherScore: int = 0
    FinalMessage: str = ""
    FinalMessageColor: tuple = (0, 0, 0)

    def __str__(self):
        awayScoreStr: str = "{}: {}".format(self.AwayTeamAbbr, self.AwayScore)
        homeScoreStr: str = "{}: {}".format(self.HomeTeamAbbr, self.HomeScore)
        timeStr: str
        if self.IsFinal:
            timeStr = "F"
        else:
            timeStr = "{} {}".format(self.TimeRemaining, self.Period)
        return "{}, {} {}".format(awayScoreStr, homeScoreStr, timeStr)

class ScoreResult(object):
    IsException: bool = False
    ExceptionDescription: str = ""
    RequestSucceeded: bool = False
    Response: HTTPResponse = None
    ResponseValid: bool = False
    AnyGamesFound: bool = False

    TheScore: Score = None
    
class ScoreRetriever(object):
    __http: PoolManager = None

    def __init__(self):
        urllib3.disable_warnings()  # turn off InsecureRequestWarning
        self.__http = PoolManager()

    def GetScoreForTeam(self, teamAbbr: str, teamNick: str, dateToUse: date, timeZoneDelta: int) -> ScoreResult:
        try:
            result: ScoreResult = ScoreResult()

            response = self.__getResponse(dateToUse)
            if response == None:
                return result

            result.RequestSucceeded = True
            result.Response = response

            soup: BeautifulSoup = BeautifulSoup(response.data, features="html.parser")

            gameElements: list = self.__getGameElements(soup)
            if gameElements == None:
                return result
            
            result.ResponseValid = True

            for gameElement in gameElements:
                if not ("/nba/" in gameElement.decode_contents()):  # why would they send us NHL scores??????
                    continue
                result.AnyGamesFound = True
                teamNameElements = gameElement.select(".teamname")
                if len(teamNameElements) > 1:
                    teamA = gameElement.select(".teamname")[0].string.strip()
                    teamB = gameElement.select(".teamname")[1].string.strip()
                    if teamA == teamAbbr or teamB == teamAbbr:
                        result.TheScore = self.__parseGame(gameElement, teamAbbr, teamNick, dateToUse, timeZoneDelta)
                        break
        
        except Exception as e:
            result.IsException = True
            result.ExceptionDescription = str(e)
        
        return result

    def __getResponse(self, dateToUse: date) -> HTTPResponse:
        url = SCORE_URL.format(dateToUse.year, dateToUse.month, dateToUse.day)
        response: HTTPResponse = self.__http.request("GET", url)
        if response.status != 200:
            return None
        return response

    def __getGameElements(self, soup: BeautifulSoup) -> list:
        canary: list = soup.find_all("article", id="scorespage")
        if canary == None or len(canary) < 1:
            return None
        gameElements: list = soup.find_all("div", class_="game")
        if len(gameElements) < 1:
            return None
        return gameElements

    def __parseGame(self, gameElement: Tag, teamAbbr: str, teamNick: str, dateToUse: date, timeZoneDelta: int) -> Score:
        score: Score = Score()

        try:
            score.AwayTeamAbbr = gameElement.select(".teamname")[0].string.strip()
            score.HomeTeamAbbr = gameElement.select(".teamname")[1].string.strip()
        except:
            pass

        try:
            startTimeElement: Tag = gameElement.find(class_="outcome first")
            startTimeRaw = startTimeElement.string.strip()
            regex = re.compile("\d?\d\:\d\d\D\D ET")
            matches = regex.findall(startTimeRaw)
            startTimeET = datetime.strptime(matches[0].replace(" ET",""), "%I:%M%p")
            startDateET = datetime(dateToUse.year, dateToUse.month, dateToUse.day, startTimeET.hour, startTimeET.minute)
            score.StartTime = startDateET + timedelta(hours=timeZoneDelta)
        except:
            pass

        try:
            scoreElements: list = gameElement.select(".outcomes.total")
            visitorTeamScoreStr = scoreElements[0].string
            homeTeamScoreStr = scoreElements[1].string
            score.AwayScore = int(visitorTeamScoreStr.strip())
            score.HomeScore = int(homeTeamScoreStr.strip())

            if score.HomeTeamAbbr == teamAbbr:
                score.TeamScore = score.HomeScore
                score.OtherScore = score.AwayScore
            else:
                score.TeamScore = score.AwayScore
                score.OtherScore = score.HomeScore
        except:
            pass

        try:
            periodElement: Tag = startTimeElement.find_previous("li")
            score.Period = periodElement.string.strip()
            if score.period.isdigit():
                score.period = "Q" + score.period
        except:
            pass
    
        try:
            timerElement: Tag = gameElement.find("h3")
            timerRaw = timerElement.string.strip()
            if timerRaw == "Final" or timerRaw == "Final OT":
                score.IsFinal = True
                ScoreRetriever.SetFinalMessage(score, teamNick)
            elif timerRaw == "Halftime":
                score.TimeRemaining = "0:00"
            else:
                regex = re.compile("\d?\d\:\d\d")
                matches = regex.findall(timerRaw)
                if len(matches) > 0:
                    score.TimeRemaining = matches[0]
        except:
            pass

        return score
    
    @staticmethod
    def SetFinalMessage(score, teamNick):
        if not score.IsFinal:
            return None

        if score.TeamScore > score.OtherScore:
            scoreText = teamNick.upper() + " WIN!" #!!!!!
            color = (0, 255, 0)
        else:
            scoreText = teamNick + " lose"
            color = (255, 0, 0)

        score.FinalMessage = scoreText
        score.FinalMessageColor = color

    __simulationStep: int = -1

    def GetSimulatedScoreForTeam(self, teamAbbr: str, teamNick: str, dateToUse: date, timeZoneDelta: int) -> ScoreResult:
        time.sleep(2) #simulate lag

        self.__simulationStep = self.__simulationStep + 1

        result = ScoreResult()        
        if self.__simulationStep < 1:
            return result

        result.RequestSucceeded = True
        if self.__simulationStep < 2:
            return result

        result.ResponseValid = True        
        if self.__simulationStep < 3:
            return result

        result.AnyGamesFound = True
        result.TheScore = Score()
        result.TheScore.StartTime = datetime.now() + timedelta(seconds = 4)
        if self.__simulationStep < 4:
            return result

        result.TheScore.StartTime = datetime.now() + timedelta(seconds = -1)
        result.TheScore.AwayTeamAbbr = "CHI"
        result.TheScore.HomeTeamAbbr = "MIL"
        if self.__simulationStep < 5:
            return result

        result.TheScore.StartTime = None

        result.TheScore.AwayScore = 0
        result.TheScore.HomeScore = 0
        result.TheScore.OtherScore = result.TheScore.AwayScore
        result.TheScore.TeamScore = result.TheScore.HomeScore
        result.TheScore.Period = "Q1"
        result.TheScore.TimeRemaining = "12:00"
        if self.__simulationStep < 6:
            return result

        result.TheScore.AwayScore = 86
        result.TheScore.HomeScore = 99
        result.TheScore.OtherScore = result.TheScore.AwayScore
        result.TheScore.TeamScore = result.TheScore.HomeScore
        result.TheScore.Period = "Q4"
        result.TheScore.TimeRemaining = "9:13"
        if self.__simulationStep < 7:
            return result
        
        if self.__simulationStep < 8:
            return ScoreResult()  # request failed entirely

        result.TheScore.AwayScore = 100
        result.TheScore.HomeScore = 140
        result.TheScore.OtherScore = result.TheScore.AwayScore
        result.TheScore.TeamScore = result.TheScore.HomeScore
        result.TheScore.Period = "Q4"
        result.TheScore.TimeRemaining = "0:00"
        result.TheScore.IsFinal = True
        ScoreRetriever.SetFinalMessage(result.TheScore, teamNick)
        
        return result