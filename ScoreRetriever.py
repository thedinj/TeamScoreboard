import urllib3
from urllib3 import PoolManager, HTTPResponse
from bs4 import BeautifulSoup, Tag
from datetime import date, datetime, timedelta
import re
import time
import os

class Score(object):
    StartTime: datetime = None
    
    Period: str = ""
    TimeRemaining: str = ""

    __isFinal: bool = False

    def SetIsFinal(self, isFinal, teamNick):
        self.__isFinal = isFinal
        if not self.__isFinal:
            return None

        if self.TeamScore > self.OtherScore:
            scoreText = teamNick.upper() + " WIN!"
            color = (0, 255, 0)
        else:
            scoreText = teamNick + " lose"
            color = (255, 0, 0)

        self.FinalMessage = scoreText
        self.FinalMessageColor = color

    def GetIsFinal(self):
        return self.__isFinal

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
        if self.__isFinal:
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

    def __getResponse(self, url, headers = None) -> HTTPResponse:
        response: HTTPResponse = self.__http.request("GET", url, None, headers)
        if response.status != 200:
            return None
        return response



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
        result.TheScore.Period = "1st"
        result.TheScore.TimeRemaining = "12:00"
        if self.__simulationStep < 6:
            return result

        result.TheScore.AwayScore = 86
        result.TheScore.HomeScore = 99
        result.TheScore.OtherScore = result.TheScore.AwayScore
        result.TheScore.TeamScore = result.TheScore.HomeScore
        result.TheScore.Period = "4th"
        result.TheScore.TimeRemaining = "9:13"
        if self.__simulationStep < 7:
            return result
        
        if self.__simulationStep < 8:
            return ScoreResult()  # request failed entirely

        result.TheScore.AwayScore = 100
        result.TheScore.HomeScore = 140
        result.TheScore.OtherScore = result.TheScore.AwayScore
        result.TheScore.TeamScore = result.TheScore.HomeScore
        result.TheScore.Period = "4th"
        result.TheScore.TimeRemaining = "0:00"
        result.TheScore.SetIsFinal(True, teamNick)
        
        return result