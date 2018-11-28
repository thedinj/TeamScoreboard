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

    AwayTeamAbbr: str = ""
    HomeTeamAbbr: str = ""
    
    AwayScore: int = 0
    HomeScore: int = 0

    TeamAbbr: str = ""
    OtherAbbr: str = ""

    TeamScore: int = 0
    OtherScore: int = 0
    
    IsFinal: bool = False

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
    TeamGameFound: bool = False

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

    @staticmethod
    def TeamStrToTricode(teamStr):
        teamStr = teamStr.lower()
        if (teamStr.find("hawks") >= 0) or (teamStr.find("atlanta") >= 0): return "ATL"
        if (teamStr.find("celtics") >= 0) or (teamStr.find("boston") >= 0): return "BOS"
        if (teamStr.find("brooklyn") >= 0): return "BKN"
        if (teamStr.find("hornets") >= 0) or (teamStr.find("charlotte") >= 0): return "CHA"
        if (teamStr.find("bulls") >= 0) or (teamStr.find("chicago") >= 0): return "CHI"
        if (teamStr.find("cavaliers") >= 0) or (teamStr.find("cavs") >= 0) or (teamStr.find("cleveland") >= 0): return "CLE"
        if (teamStr.find("mavericks") >= 0) or (teamStr.find("mavs") >= 0) or (teamStr.find("dallas") >= 0): return "DAL"
        if (teamStr.find("nuggets") >= 0) or (teamStr.find("denver") >= 0): return "DEN"
        if (teamStr.find("pistons") >= 0) or (teamStr.find("detroit") >= 0): return "DET"
        if (teamStr.find("warriors") >= 0) or (teamStr.find("golden state") >= 0): return "GOL"
        if (teamStr.find("rockets") >= 0) or (teamStr.find("houston") >= 0): return "HOU"
        if (teamStr.find("pacers") >= 0) or (teamStr.find("indiana") >= 0): return "IND"
        if (teamStr.find("clippers") >= 0): return "LAC"
        if (teamStr.find("lakers") >= 0): return "LAL"
        if (teamStr.find("grizzlies") >= 0) or (teamStr.find("memphis") >= 0): return "MEM"
        if (teamStr.find("heat") >= 0) or (teamStr.find("miami") >= 0): return "MIA"
        if (teamStr.find("bucks") >= 0) or (teamStr.find("milwaukee") >= 0): return "MIL"
        if (teamStr.find("timberwolves") >= 0) or (teamStr.find("minnesota") >= 0): return "MIN"
        if (teamStr.find("pelicans") >= 0) or (teamStr.find("new orleans") >= 0): return "NOP"
        if (teamStr.find("knicks") >= 0) or (teamStr.find("new york") >= 0): return "NYK"
        if (teamStr.find("thunder") >= 0) or (teamStr.find("oklahoma city") >= 0): return "OKC"
        if (teamStr.find("magic") >= 0) or (teamStr.find("orlando") >= 0): return "ORL"
        if (teamStr.find("76ers") >= 0) or (teamStr.find("philadelphia") >= 0): return "PHI"
        if (teamStr.find("suns") >= 0) or (teamStr.find("phoenix") >= 0): return "PHO"
        if (teamStr.find("trail blazers") >= 0) or (teamStr.find("blazers") >= 0) or (teamStr.find("portland") >= 0): return "POR"
        if (teamStr.find("kings") >= 0) or (teamStr.find("sacramento") >= 0): return "SAC"
        if (teamStr.find("spurs") >= 0) or (teamStr.find("san antonio") >= 0): return "SAN"
        if (teamStr.find("raptors") >= 0) or (teamStr.find("toronto") >= 0): return "TOR"
        if (teamStr.find("jazz") >= 0) or (teamStr.find("salt lake city") >= 0): return "UTA"
        if (teamStr.find("wizards") >= 0) or (teamStr.find("washington") >= 0): return "WAS"
        return "???"

    @staticmethod
    def TricodeToNick(tricode):
        tricode = tricode.upper()
        if (tricode == "ATL"): return "Hawks"
        if (tricode == "BOS"): return "Celtics"
        if (tricode == "BKN"): return "Nets"
        if (tricode == "CHA"): return "Hornets"
        if (tricode == "CHI"): return "Bulls"
        if (tricode == "CLE"): return "Cavaliers"
        if (tricode == "DAL"): return "Mavericks"
        if (tricode == "DEN"): return "Nuggets"
        if (tricode == "DET"): return "Pistons"
        if (tricode == "GOL"): return "Warriors"
        if (tricode == "HOU"): return "Rockets"
        if (tricode == "IND"): return "Pacers"
        if (tricode == "LAC"): return "Clippers"
        if (tricode == "LAL"): return "Lakers"
        if (tricode == "MEM"): return "Grizzlies"
        if (tricode == "MIA"): return "Heat"
        if (tricode == "MIL"): return "Bucks"
        if (tricode == "MIN"): return "Timberwolves"
        if (tricode == "NOP"): return "Pelicans"
        if (tricode == "NYK"): return "Knicks"
        if (tricode == "OKC"): return "Thunder"
        if (tricode == "ORL"): return "Magic"
        if (tricode == "PHI"): return "76ers"
        if (tricode == "PHO"): return "Suns"
        if (tricode == "POR"): return "Trail Blazers"
        if (tricode == "SAC"): return "Kings"
        if (tricode == "SAN"): return "Spurs"
        if (tricode == "TOR"): return "Raptors"
        if (tricode == "UTA"): return "Jazz"
        if (tricode == "WAS"): return "Wizards"
        return "???"


    __simulationStep: int = -1

    def GetSimulatedScoreForTeam(self, teamAbbr: str, dateToUse: date, timeZoneDelta: int) -> ScoreResult:
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
        result.TheScore.IsFinal = True
        
        return result