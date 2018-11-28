from ScoreRetriever import ScoreRetriever, Score, ScoreResult
import urllib3
from urllib3 import PoolManager, HTTPResponse
from bs4 import BeautifulSoup, Tag
from datetime import date, datetime, timedelta
import re
import time
import os

SCORE_URL = "http://www.es" + "pn.com/nba/scoreboard/_/date/{}{}{}"  #20181127
USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Mobile Safari/537.36"

class ESPNScoreRetriever(ScoreRetriever):
    def GetScoreForTeam(self, teamAbbr: str, dateToUse: date, timeZoneDelta: int) -> ScoreResult:
        try:
            result: ScoreResult = ScoreResult()

            url = SCORE_URL.format(dateToUse.year, str(dateToUse.month).zfill(2), str(dateToUse.day).zfill(2))
            response = self._ScoreRetriever__getResponse(url, {"User-Agent": USER_AGENT})
            if response == None:
                return result

            result.RequestSucceeded = True
            result.Response = response

            soup: BeautifulSoup = BeautifulSoup(response.data, features="lxml")

            gameElements = soup.select(".scoreboard.basketball")
            if len(gameElements) < 1:
                return result

            result.ResponseValid = True

            for gameElement in gameElements:
                if not ("/nba/" in gameElement.decode_contents()):  # USA Today sent back NHL games, so it doesn't hurt to check...
                    continue
                result.AnyGamesFound = True
                teamA = ""
                teamB = ""
                try:
                    teamA = gameElement.find_all("td", "away")[0].text.strip()
                    teamB = gameElement.find_all("td", "home")[0].text.strip()
                except:
                    pass
                teamAAbbr = ScoreRetriever.TeamStrToTricode(teamA)
                teamBAbbr = ScoreRetriever.TeamStrToTricode(teamB)
                if teamAAbbr == teamAbbr or teamBAbbr == teamAbbr:
                    result.TeamGameFound = True
                    result.TheScore = self.__parseGame(gameElement, teamAbbr, dateToUse, timeZoneDelta)
                    break
        
        except Exception as e:
            result.IsException = True
            result.ExceptionDescription = str(e)
        
        return result


    def __parseGame(self, gameElement: Tag, teamAbbr: str, dateToUse: date, timeZoneDelta: int) -> Score:
        score: Score = Score()

        try:
            score.AwayTeamAbbr = ScoreRetriever.TeamStrToTricode(gameElement.find_all("td", "away")[0].text.strip())
            score.HomeTeamAbbr = ScoreRetriever.TeamStrToTricode(gameElement.find_all("td", "home")[0].text.strip())

            if score.HomeTeamAbbr == teamAbbr:
                score.TeamAbbr = score.HomeTeamAbbr
                score.OtherAbbr = score.AwayTeamAbbr
            else:
                score.TeamAbbr = score.AwayTeamAbbr
                score.OtherAbbr = score.HomeTeamAbbr
        except:
            pass

        try:
            score.AwayScore = int(gameElement.find_all("tr", "away")[0].select(".total")[0].text.strip())
            score.HomeScore = int(gameElement.find_all("tr", "home")[0].select(".total")[0].text.strip())

            if score.HomeTeamAbbr == teamAbbr:
                score.TeamScore = score.HomeScore
                score.OtherScore = score.AwayScore
            else:
                score.TeamScore = score.AwayScore
                score.OtherScore = score.HomeScore
        except:
            pass

        try:
            timerRaw: str = gameElement.select(".date-time")[0].text.strip()

            if timerRaw == "Final" or timerRaw == "Final/OT":
                score.IsFinal = True
            elif timerRaw == "Halftime":
                score.Period = "2nd"
                score.TimeRemaining = "0:00"
            elif timerRaw.startswith("End of "):
                score.Period = timerRaw[7:]
                score.TimeRemaining = "0:00"
            else:
                # is it a game in progress?
                regex = re.compile("\d?\d\:\d\d - \d.*")
                matches = regex.findall(timerRaw)
                if len(matches) > 0:
                    [score.TimeRemaining, score.Period] = matches[0].split(" - ")
                else:
                    # let's see if it's a start time
                    startTime: struct_time = time.strptime(timerRaw.replace(" ET",""), "%I:%M %p")
                    score.StartTime = datetime(dateToUse.year, dateToUse.month, dateToUse.day, startTime.tm_hour, startTime.tm_min) + timedelta(hours=timeZoneDelta)
        except:
            pass

        return score
    
if __name__ == '__main__':
    scoreRetriever: ESPNScoreRetriever = ESPNScoreRetriever()
    scoreResult = scoreRetriever.GetScoreForTeam("MIL", date(2018,11,28), -1)
    #if scoreResult .Response != None:
    #    textFile = open("ESPN_response.html", "wb")
    #    textFile.write(scoreResult .Response.data)
    #    textFile.close()
