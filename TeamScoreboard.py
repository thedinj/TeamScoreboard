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

MAX_NO_GAMES_CHECKS = 5

SHORT_TIMES = True

STARTUP_SEC = 20
LED_REFRESH_TIME_SEC = 60
FINAL_SCORE_TIME_SEC = 30  # seconds to scroll the win/loss message
ERROR_SLEEP_SEC = 10
MAX_SLEEP = 2 * 60 * 60
SHOW_FINAL_SCORE_SEC = 30 * 60  # seconds to display the final score before shutting off

if SHORT_TIMES:
    STARTUP_SEC = 5
    LED_REFRESH_TIME_SEC = 5
    FINAL_SCORE_TIME_SEC = 5
    SHOW_FINAL_SCORE_SEC = 30

SIMULATION_DATE = None #date(2018,11,21)

#https://stackoverflow.com/questions/3718657/how-to-properly-determine-current-script-directory
#os.path.dirname(os.path.abspath(__file__))


class TeamScoreboard(object):
    __teamAbbr = ""
    __timeZoneDelta = 0
    __scoreRetriever = None
    __scoreboard = None
    __noGameTodayCount = 0
    __finalFlag = False
    __finalTimestamp = None

    def __init__(self, teamAbbr: str, timeZoneDelta: int):
        self.__teamAbbr = teamAbbr
        self.__timeZoneDelta = timeZoneDelta
        self.__scoreRetriever = ScoreRetriever()
        self.__scoreboard = Scoreboard()

    def RunDisplayScoreLoop(self):
        print("Main loop running at {}.".format(time.ctime()))

        proc = self.__scoreboard.DisplayMessage("Starting Up...", STARTUP_SEC, True, True)
        while True:
            result: ScoreResult = self.__getScoreResult()

            if result.IsException:
                print("Exception loading score: {}".format(result.ExceptionDescription))
                self.__sleep(ERROR_SLEEP_SEC)
                continue
            
            if not result.RequestSucceeded:
                print("Request failed.")
                self.__sleep(ERROR_SLEEP_SEC)
                continue

            if not result.ResponseValid:
                print("Invalid response.")
                self.__sleep(ERROR_SLEEP_SEC)
                continue

            if not result.AnyGamesFound:
                self.__noGameTodayCount = self.__noGameTodayCount+1
                if self.__noGameTodayCount <= MAX_NO_GAMES_CHECKS:
                    print("No games AT ALL found for today.")
                    self.__sleep(ERROR_SLEEP_SEC)
                    continue
                print("Exceeded max checks for no games AT ALL today.")
            else:
                self.__noGameTodayCount = 0
            
            if result.TheScore == None:
                print("No team game found for today. Going to sleep.")
                self.__sleep(TeamScoreboard.SecondsUntilTomorrow() + 1)
                continue

            score: Score = result.TheScore

            if score.StartTime != None:
                secondsUntilStart = TeamScoreboard.SecondsUntilTime(score.StartTime)
                if secondsUntilStart > 0:
                    print("Game doesn't start until {}.".format(score.StartTime))
                    self.__sleep(secondsUntilStart + 1)
                    continue

            if score.IsFinal:
                if not self.__finalFlag:
                    self.__finalFlag = True
                    self.__finalTimestamp = datetime.now()
                    print("Marking today's game as final.")
                    proc = self.__displayFinalScore(score)
                    continue
                else:
                    if (datetime.now() - self.__finalTimestamp).seconds >= SHOW_FINAL_SCORE_SEC:
                        print("Turning off the display of today's final score.")
                        self.__sleep(TeamScoreboard.SecondsUntilTomorrow() + 1)
                        continue
            elif self.__finalFlag:
                print("Resetting final flags.")
                self.__finalFlag = False
                self.__finalTimestamp = None

            if len(score.Period) < 1:
                print("It's after gametime but no score yet.")
                self.__sleep(LED_REFRESH_TIME_SEC)
                continue

            if proc != None:
                proc.wait()
            
            proc = self.__displayScore(score)
    
    def __getScoreResult(self):
        if SIMULATION_DATE == None:
            dateToUse = datetime.now().date()
            if datetime.now().time().hour < 2:  # Before 2AM, might still be running yesterday's game
                dateToUse = dateToUse + timedelta(days = -1)
        else:
            dateToUse = SIMULATION_DATE
        return self.__scoreRetriever.GetScoreForTeam(self.__teamAbbr, dateToUse, self.__timeZoneDelta)

    def __sleep(self, seconds):
        if seconds > MAX_SLEEP:
            seconds = MAX_SLEEP
        sleepUntil: datetime = datetime.now() + timedelta(0, seconds)
        print("Sleeping {}s (until {}).".format(seconds, sleepUntil.strftime("%x %X")))
        time.sleep(seconds)

    def __displayFinalScore(self, score):
        return self.__scoreboard.DisplayFinalScore(score, FINAL_SCORE_TIME_SEC, True)

    def __displayScore(self, score):
        return self.__scoreboard.DisplayScore(score, LED_REFRESH_TIME_SEC, True)

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


def signal_handler(sig, frame):
    sys.exit(0)


if __name__ == '__main__':
    print("Running. pid={}.".format(os.getpid()))
    
    signal.signal(signal.SIGINT, signal_handler)

    teamScoreboard: TeamScoreboard = TeamScoreboard(FAVORITE_TEAM, TIME_ZONE_DELTA)
    teamScoreboard.RunDisplayScoreLoop()
    