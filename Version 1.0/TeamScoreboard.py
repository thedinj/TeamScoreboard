import time
import signal
import sys
from ScoreGetter import GetScoreForTeam
from datetime import datetime, timedelta, date #date is sometimes commented out
from PIL import Image, ImageFont, ImageDraw
import subprocess
import shlex
import os

#team consts
FAVORITE_TEAM = "MIL"
FAVORITE_TEAM_NICKNAME= "Bucks"
TIME_ZONE_DELTA = -1

#display consts
ROWS = 16
COLS = 64
PADDING = 30
SCORE_FILE_NAME = "/home/pi/TeamScoreboard/score.ppm"
TEMPLATE_FILE_NAME = "/home/pi/TeamScoreboard/scoreboard_bg.ppm"

#testing consts
REAL_MODE = True
SHORT_TIMES = False
SimulationStep = 1
SIMULATION_DATE = None #date(2018,10,9)

#timing consts
LED_REFRESH_TIME_SEC = 60
FINAL_SCORE_TIME_SEC = 30  # time to scroll the win/loss message
FETCH_NEW_SCORE_SEC = 10   # time to show the last score while we grab another
SHOW_FINAL_SCORE_SEC = 30 * 60
TRY_AGAIN_SEC = 60
MAX_SLEEP = 2 * 60 * 60
STARTUP_SEC = 20


if SHORT_TIMES:
    LED_REFRESH_TIME_SEC = 10
    FINAL_SCORE_TIME_SEC = 5
    FETCH_NEW_SCORE_SEC = 10
    SHOW_FINAL_SCORE_SEC = 30
    MAX_SLEEP = 30
    STARTUP_SEC = 5

#if REAL_MODE:
#    sys.stdout = open("teamscoreboard.txt", "w")

#cache globals
fonts = {}

#timing globals
todaysGameIsFinal = False
finalTimestamp = None
justShowedImage = False


def Run():
    global todaysGameIsFinal
    global finalTimestamp
    global justShowedImage
    
    result = RequestTodaysGame()
    if result[0] == False:
        print("Failed to obtain game data -- trying again in a moment")
        return TRY_AGAIN_SEC  #something went wrong--wait a bit and try again
    todaysGame = result[1]
    if todaysGame == None:
        print("No game today. Snoozing until tomorrow.")
        return SecondsUntilTomorrow() + 1
    
    justShowedImage = False
    
    if todaysGame["startTime"] != None:
        secondsUntilStart = SecondsUntilStartTime(todaysGame["startTime"])
        if secondsUntilStart > 0:
            print("Game doesn't start until {}".format(todaysGame["startTime"]))
            return secondsUntilStart + 1
    
    if todaysGame["isFinal"]:
        if not todaysGameIsFinal:
            todaysGameIsFinal = True
            finalTimestamp = datetime.now()
            print("Marking today's game as final at {}".format(finalTimestamp))
            DisplayFinalScore(todaysGame)
            return 0
        else:
            if (datetime.now() - finalTimestamp).seconds >= SHOW_FINAL_SCORE_SEC:
                print("Turning off the display of today's score")
                return SecondsUntilTomorrow() + 1
    elif todaysGameIsFinal:
        print("Resetting final flags")
        todaysGameIsFinal = False
        finalTimestamp = None
    elif todaysGame["period"] == None or len(todaysGame["period"]) < 1:
        print("It's after gametime but no score yet")
        return LED_REFRESH_TIME_SEC  #game started but no score yet
    
    DisplayScore(todaysGame, LED_REFRESH_TIME_SEC)
    justShowedImage = True
    
    return 0


def RequestTodaysGame():
    global justShowedImage
    global SimulationStep
    
    proc = None
    if justShowedImage:
        print("Displaying image while I fetch a new score")
        proc = DisplayImage(FETCH_NEW_SCORE_SEC, False, True)
    
    if REAL_MODE:
        if SIMULATION_DATE == None:
            dateToUse = datetime.now().date()
            if datetime.now().time().hour < 2:  #before 2AM, might still be running yesterday's game
                dateToUse = dateToUse + timedelta(days = -1)
        else:
            dateToUse = SIMULATION_DATE
        print("Loading game information from the web")
        result = GetScoreForTeam(FAVORITE_TEAM, dateToUse, TIME_ZONE_DELTA)
    else:
        print("Loading sumulated game data, step #{}".format(SimulationStep))
        time.sleep(1) #simulate lag
        switcher = {
            1:  [True, {
                "startTime": datetime.now() + timedelta(seconds = 5)
                }],
            2:  [True, {
                "startTime": datetime.now() + timedelta(seconds = -5),
                "visitorTeam": "CHI",
                "visitorScore": None,
                "homeTeam": "MIL",
                "homeScore": None,
                "isFinal": False,
                "period": None,
                "timeRem": None,
                "otherScore": None,
                "teamScore": None   
                }],
            3:  [True, {
                "startTime": datetime.now() + timedelta(seconds = -5),
                "visitorTeam": "CHI",
                "visitorScore": 0,
                "homeTeam": "MIL",
                "homeScore": 0,
                "isFinal": False,
                "period": "1",
                "timeRem": "12:00",
                "otherScore": 0,
                "teamScore": 0   
                }],
            4:  [True, {
                "startTime": None,
                "visitorTeam": "CHI",
                "visitorScore": 66,
                "homeTeam": "MIL",
                "homeScore": 81,
                "isFinal": False,
                "period": "3",
                "timeRem": "0:32",
                "otherScore": 66,
                "teamScore": 81       
                }],
            5:  [False, None],
            6:  [True, {
                "startTime": None,
                "visitorTeam": "CHI",
                "visitorScore": 66,
                "homeTeam": "MIL",
                "homeScore": 81,
                "isFinal": False,
                "period": "3",
                "timeRem": "0:32",
                "otherScore": 66,
                "teamScore": 81       
                }]
            }
            
        result = switcher.get(SimulationStep, 
            [True, {
            "startTime": None,
            "visitorTeam": "CHI",
            "visitorScore": 82,
            "homeTeam": "MIL",
            "homeScore": 116,
            "isFinal": True,
            "period": "4",
            "timeRem": "",
            "otherScore": 82,
            "teamScore": 116        
            }])
            
        SimulationStep += 1
    
    if proc:
        proc.wait()
        
    return result
    

def DisplayStartupMessage():
    font = GetFontByName("FreeSans", ROWS)
    
    scoreText = "Starting up..."
    color = (0, 255, 0)
    
    scoreTextData = []
    scoreTextData += [[scoreText, color, font, [PADDING/2, 0], "L"]]
    
    width, ignore = font.getsize(scoreText)
    
    WriteScoreImages(scoreTextData, (width + PADDING, ROWS))
    DisplayImage(STARTUP_SEC, True)
    
def DisplayScore(todaysGame, displayTime):
    font = GetFontByName("FreeSansBold", 9)
    colorScore = ColorScore()
    colorWinningScore = ColorWinningScore()
    visitorTeam = todaysGame["visitorTeam"]
    homeTeam = todaysGame["homeTeam"]
    
    timer = todaysGame["timeRem"]
    if (timer == None) or (len(timer) < 1):
        timer = "0:00"
    if todaysGame["isFinal"]:
        period = "(F)"
        timer = ""
    else:
        period = todaysGame["period"]
        if period.isdigit():
            period = "Q" + period
    
    scoreXOffset = 25
    
    visitorColor = colorScore
    homeColor = colorScore
    if todaysGame["visitorScore"] != None and todaysGame["homeScore"] != None:
        if todaysGame["visitorScore"] > todaysGame["homeScore"]:
            visitorColor = colorWinningScore
            homeColor = colorScore
        elif todaysGame["visitorScore"] < todaysGame["homeScore"]:
            visitorColor = colorScore
            homeColor = colorWinningScore
    
    scoreTextData = []
    scoreTextData += [[visitorTeam + ":", ColorByTeam(visitorTeam), font, [0, 0], "L"]]
    scoreTextData += [[str(todaysGame["visitorScore"]), visitorColor, font, [scoreXOffset, 0], "L"]]
    scoreTextData += [[homeTeam + ":", ColorByTeam(homeTeam), font, [0, ROWS/2], "L"]]
    scoreTextData += [[str(todaysGame["homeScore"]), homeColor, font, [scoreXOffset, ROWS/2], "L"]]
    scoreTextData += [[period, colorScore, font, [COLS, 0], "R"]]
    scoreTextData += [[timer, colorScore, font, [COLS, ROWS/2], "R"]]
    
    print("Score: {}-{}".format(todaysGame["visitorScore"], todaysGame["homeScore"]))
    
    WriteScoreImages(scoreTextData, None, TEMPLATE_FILE_NAME)
    DisplayImage(displayTime, False)


def DisplayFinalScore(todaysGame):
    font = GetFontByName("FreeSansBold", ROWS)
    
    if todaysGame["teamScore"] > todaysGame["otherScore"]:
        scoreText = FAVORITE_TEAM_NICKNAME.upper() + " WIN!"
        color = (0, 255, 0)
    else:
        scoreText = FAVORITE_TEAM_NICKNAME + " lose "
        color = (255, 0, 0)
    
    scoreText += " ({}-{})".format(todaysGame["teamScore"], todaysGame["otherScore"])
    
    scoreTextData = []
    scoreTextData += [[scoreText, color, font, [PADDING/2, 0], "L"]]
    
    width, ignore = font.getsize(scoreText)
    
    WriteScoreImages(scoreTextData, (width + PADDING, ROWS))
    DisplayImage(FINAL_SCORE_TIME_SEC, True)
    

def WriteScoreImages(scoreTextData, xy = None, templateFile = None):
    if templateFile != None:
        im = Image.open(templateFile)
    else:
        if xy == None:
            xy = (COLS, ROWS)
        im = Image.new("RGB", xy, "black")
    draw = ImageDraw.Draw(im)
    
    for index in range(0, len(scoreTextData)):
        scoreTextDatum = scoreTextData[index]
        scoreText = scoreTextDatum[0]
        color = scoreTextDatum[1]
        font = scoreTextDatum[2]
        pos = scoreTextDatum[3]
        align = scoreTextDatum[4]
        if align == "R":
             width, ignore = font.getsize(scoreText)
             pos[0] -= width
        pos[1] -= 1  # nothing goes above the line
        draw.text(pos, scoreText, color, font=font)
    im.save(SCORE_FILE_NAME)


def DisplayImage(displayTime, scroll = False, isBackground = False):
    print("Displaying image on LEDs ({}s)".format(displayTime))
    if scroll:
        command = "sudo /home/pi/rpi-rgb-led-matrix/examples-api-use/demo"
        args = " --led-rows {} --led-cols {} --led-slowdown-gpio 2 -t {} -D 1 {} >/dev/null 2>&1".format(ROWS, COLS, displayTime, SCORE_FILE_NAME)
    else:
        command = "sudo /home/pi/rpi-rgb-led-matrix/utils/led-image-viewer"
        args = " -w {} -l 1 {} --led-rows {} --led-cols {} --led-slowdown-gpio 2 >/dev/null 2>&1".format(displayTime, SCORE_FILE_NAME, ROWS, COLS)
    #print(command+args)
    #subprocess.call(command + args, shell = True)
    cmd = shlex.split(command + args)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not isBackground:
        proc.wait()
    return proc

def GetFontByName(fontName, fontSize):
    global fonts
    if (fontName, fontSize) in fonts:
        return fonts[(fontName, fontSize)]
    print("Loading font {}, size={}".format(fontName, fontSize))
    font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/{}.ttf".format(fontName), fontSize)
    fonts[(fontName, fontSize)] = font
    return font


def SecondsUntilTomorrow():
    todaysDate = datetime.now().date()
    todaysDateTime = datetime(todaysDate.year, todaysDate.month, todaysDate.day)
    tomorrowDateTime = todaysDateTime + timedelta(days=1)
    return (tomorrowDateTime - datetime.now()).seconds


def SecondsUntilStartTime(startTime):
    if not (type(startTime) is datetime):
        return 0
    timeUntilStart = startTime - datetime.now()
    if timeUntilStart.days < 0:  # this is how you check for a negative timedelta
        return 0
    return timeUntilStart.seconds

#https://teamcolorcodes.com/milwaukee-bucks-color-codes/
def ColorByTeam(team):
    switcher = {
        "ATL": (225,68,52),
        "BKN": (255,255,255),
        "BOS": (0,122,51),
        "CLE": (111,38,61),
        "CHA": (29,17,96),
        "CHI": (206,17,65),
        "DAL": (0,83,188),
        "DEN": (29,66,138),
        "DET": (29,66,138),
        "GSW": (253,185,39),
        "HOU": (206,17,65),
        "IND": (253,187,48),
        "LAC": (200,16,46),
        "LAL": (85,37,130),
        "MEM": (93,118,169),
        "MIA": (249,160,27),
        "MIL": (0,71,27),
        "MIN": (120,190,32),
        "NOP": (180,151,90),
        "NY":  (0,107,182),
        "OKC": (239,59,36),
        "ORL": (0,125,197),
        "PHI": (0,107,182),
        "PHX": (229,95,32),
        "POR": (224,58,62),
        "SAC": (91,43,130),
        "SAS": (196,206,211),
        "TOR": (206,17,65),
        "UTA": (0,43,92),
        "WAS": (100,64,0,60)
    }
    return switcher.get(team, (255, 0, 255))


def ColorScore():
    return (150, 150, 150)

def ColorWinningScore():
    return (150, 150, 50)

def signal_handler(sig, frame):
    sys.exit(0)
        

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    print("Run: pid={}".format(os.getpid()))
    DisplayStartupMessage()
    while True:
        print("Main loop running at {}".format(time.ctime()))
        sleepSec = Run()
        if sleepSec > 0:
            if sleepSec > MAX_SLEEP:
                sleepSec = MAX_SLEEP
            sleepUntil = datetime.now() + timedelta(0, sleepSec)
            print("Sleeping {}s (until {})".format(sleepSec, sleepUntil))
            time.sleep(sleepSec)

    
