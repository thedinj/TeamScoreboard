import signal
import os
import sys
import subprocess
import time
from ScoreRetriever import ScoreRetriever, ScoreResult, Score
from Scoreboard import Scoreboard
from datetime import datetime, date, timedelta

FAVORITE_TEAM = "MIL"
FAVORITE_TEAM_NICKNAME= "Bucks"
TIME_ZONE_DELTA = -1

ROWS = 16
COLS = 64
PADDING = 30

SHORT_TIMES = False
SIMULATED_DATA = False
SIMULATION_DATE = None #date(2018,11,21)

STARTUP_SEC = 20
LED_REFRESH_TIME_SEC = 60
FINAL_SCORE_TIME_SEC = 30       # seconds to scroll the win/loss message
ERROR_SLEEP_SEC = 30
SHOW_FINAL_SCORE_SEC = 30 * 60  # seconds to display the final score before shutting off
MAX_EXPECTED_RESPONSE_SEC = 20
MAX_SLEEP = 2 * 60 * 60

if SHORT_TIMES:
    STARTUP_SEC = 5
    LED_REFRESH_TIME_SEC = 5
    FINAL_SCORE_TIME_SEC = 5
    ERROR_SLEEP_SEC = 5
    SHOW_FINAL_SCORE_SEC = 15

MAX_NO_GAMES_CHECKS = 5

SAVING_RESPONSES = True
MAX_SAVED_RESPONSES = 100

class DrawResult(object):
    DrawSeconds: int = 0
    SleepSeconds: int = 0
    Scroll: bool = False

    def __init__(self, drawSeconds: int = 0, scroll: bool = False, sleepSeconds: int = 0):
        self.DrawSeconds = drawSeconds
        self.Scroll = scroll
        self.SleepSeconds = sleepSeconds


class TeamScoreboard(object):
    __teamAbbr = ""
    __teamNick = ""
    __timeZoneDelta = 0
    __scoreRetriever = None
    __scoreboard = None
    __noGameTodayCount = 0
    __finalFlag = False
    __finalTimestamp = None

    def __init__(self, teamAbbr: str, teamNick: str, timeZoneDelta: int):
        self.__teamAbbr = teamAbbr
        self.__teamNick = teamNick
        self.__timeZoneDelta = timeZoneDelta
        self.__scoreRetriever = ScoreRetriever()
        self.__scoreboard = Scoreboard(ROWS, COLS, PADDING)

    def RunDisplayScoreLoop(self):
        print("Main loop starting at {}.".format(datetime.now().strftime("%x %X")))

        self.__scoreboard.DrawMessage("Starting Up...")
        proc = self.__scoreboard.DisplayImage(STARTUP_SEC, True, True)

        while True:
            print("Main loop running at {}.".format(datetime.now().strftime("%x %X")))
            
            result: ScoreResult = self.__getScoreResult()

            if result.RequestSucceeded and SAVING_RESPONSES:
                filename = self.__getNextResponseFilename()
                print("Storing response as {}.".format(filename))
                textFile = open(self.__getDirectory() + "/" + filename, "wb")
                textFile.write(result.Response.data)
                textFile.close()

            drawResult: DrawResult = self.__processResult(result)

            if drawResult.SleepSeconds > 0:
                self.__sleep(drawResult.SleepSeconds)
                continue

            if proc != None:
                proc.wait()
                proc = None
            
            proc = self.__scoreboard.DisplayImage(drawResult.DrawSeconds, drawResult.Scroll, True)
            self.__sleep(drawResult.DrawSeconds - MAX_EXPECTED_RESPONSE_SEC)
    
    def __processResult(self, result: ScoreResult) -> DrawResult:
        print("Processing result.")
        if result.IsException:
            print("Exception loading score: {}".format(result.ExceptionDescription))
            return DrawResult(sleepSeconds = ERROR_SLEEP_SEC)
            
        if not result.RequestSucceeded:
            print("Request failed.")
            return DrawResult(sleepSeconds = ERROR_SLEEP_SEC)

        if not result.ResponseValid:
            print("Invalid response.")
            return DrawResult(sleepSeconds = ERROR_SLEEP_SEC)

        if not result.AnyGamesFound:
            self.__noGameTodayCount = self.__noGameTodayCount+1
            if self.__noGameTodayCount <= MAX_NO_GAMES_CHECKS:
                print("No games AT ALL found for today.")
                return DrawResult(sleepSeconds = ERROR_SLEEP_SEC)
            print("Exceeded max checks for no games AT ALL today.")
        else:
            self.__noGameTodayCount = 0
            
        if result.TheScore == None:
            print("No team game found for today. Going to sleep.")
            return DrawResult(sleepSeconds = TeamScoreboard.SecondsUntilTomorrow() + 1)

        score: Score = result.TheScore

        if score.StartTime != None:
            secondsUntilStart = TeamScoreboard.SecondsUntilTime(score.StartTime)
            if secondsUntilStart > 0:
                print("Game doesn't start until {}.".format(score.StartTime.strftime("%x %X")))
                return DrawResult(sleepSeconds = secondsUntilStart + 1)

        if score.IsFinal:
            if not self.__finalFlag:
                self.__finalFlag = True
                self.__finalTimestamp = datetime.now()
                print("Marking today's game as final.")
                self.__scoreboard.DrawFinalScore(score)
                return DrawResult(FINAL_SCORE_TIME_SEC, True)
            else:
                if (datetime.now() - self.__finalTimestamp).seconds >= SHOW_FINAL_SCORE_SEC:
                    print("Turning off the display of today's (final) score.")
                    return DrawResult(sleepSeconds = TeamScoreboard.SecondsUntilTomorrow() + 1)
        elif self.__finalFlag:
            print("Resetting final flags.")
            self.__finalFlag = False
            self.__finalTimestamp = None

        if len(score.Period) < 1:
            print("It's after gametime but no score yet.")
            return DrawResult(sleepSeconds = LED_REFRESH_TIME_SEC)

        self.__scoreboard.DrawScore(score)
        print("Drawing score image.")
        return DrawResult(LED_REFRESH_TIME_SEC, False)

    def __getScoreResult(self):
        if SIMULATION_DATE == None:
            dateToUse = datetime.now().date()
            if datetime.now().time().hour < 2:  # Before 2AM, might still be running yesterday's game
                dateToUse = dateToUse + timedelta(days = -1)
        else:
            dateToUse = SIMULATION_DATE
        if not SIMULATED_DATA:
            print("Retrieving score from the web.")
            return self.__scoreRetriever.GetScoreForTeam(self.__teamAbbr, self.__teamNick, dateToUse, self.__timeZoneDelta)
        else:
            print("Retrieving score from simulation data.")
            return self.__scoreRetriever.GetSimulatedScoreForTeam(self.__teamAbbr, self.__teamNick, dateToUse, self.__timeZoneDelta)

    def __sleep(self, seconds: int):
        if seconds < 1:
            return
        if seconds > MAX_SLEEP:
            seconds = MAX_SLEEP
        sleepUntil: datetime = datetime.now() + timedelta(0, seconds)
        print("Sleeping {}s (until {}).".format(seconds, sleepUntil.strftime("%x %X")))
        time.sleep(seconds)

    @staticmethod
    def SecondsUntilTomorrow():
        todaysDate = datetime.now().date()
        todaysDateTime = datetime(todaysDate.year, todaysDate.month, todaysDate.day)
        tomorrowDateTime = todaysDateTime + timedelta(days=1)
        return (tomorrowDateTime - datetime.now()).seconds

    @staticmethod
    def SecondsUntilTime(theTime):
        if not (type(theTime) is datetime):
            return 0
        timeUntilStart = theTime - datetime.now()
        if timeUntilStart.days < 0:  # this is how you check for a negative timedelta
            return 0
        return timeUntilStart.seconds
        
    def __getDirectory(self):
        return os.path.dirname(os.path.abspath(__file__))

    __currentResponseIndex: int = -1
    def __getNextResponseFilename(self):
        self.__currentResponseIndex = (self.__currentResponseIndex + 1) % MAX_SAVED_RESPONSES
        return "response_" + str(self.__currentResponseIndex+1) + ".html"


def signal_handler(sig, frame):
    sys.exit(0)


if __name__ == '__main__':
    print("Running. pid={}.".format(os.getpid()))
    
    signal.signal(signal.SIGINT, signal_handler)

    teamScoreboard: TeamScoreboard = TeamScoreboard(FAVORITE_TEAM, FAVORITE_TEAM_NICKNAME, TIME_ZONE_DELTA)
    teamScoreboard.RunDisplayScoreLoop()
    