import time
import subprocess
import os
from ScoreRetriever import Score, ScoreRetriever
from PIL import Image, ImageFont, ImageDraw
import shlex

SCORE_FILE_NAME = "score.ppm"
TEMPLATE_FILE_NAME = "scoreboard_bg.ppm"

class Scoreboard(object):
    __fonts = {}
    __rows = 0
    __cols = 0
    __padding = 0

    def __init__(self, rows, cols, padding):
        self.__rows = rows
        self.__cols = cols
        self.__padding = padding

    def DrawScore(self, score: Score):
        print("Drawing score: {}".format(score))

        font = self.__getFontByName("FreeSansBold", 9)

        awayTeam = score.AwayTeamAbbr
        homeTeam = score.HomeTeamAbbr
    
        timer = score.TimeRemaining
        if len(timer) < 1:
            timer = "0:00"
        
        if score.IsFinal:
            period = "(F)"
            timer = ""
        else:
            period = score.Period
    
        scoreXOffset = 25
    
        awayScoreColor = Scoreboard.ColorScore()
        homeScoreColor = Scoreboard.ColorScore()
        if score.AwayScore > score.HomeScore:
            awayScoreColor = Scoreboard.ColorWinningScore()
        elif score.AwayScore < score.HomeScore:
            homeScoreColor = Scoreboard.ColorWinningScore()
    
        scoreTextData = []
        scoreTextData += [[awayTeam + ":", Scoreboard.ColorByTeam(awayTeam), font, [0, 0], "L"]]
        scoreTextData += [[str(score.AwayScore), awayScoreColor, font, [scoreXOffset, 0], "L"]]
        scoreTextData += [[homeTeam + ":", Scoreboard.ColorByTeam(homeTeam), font, [0, self.__rows/2], "L"]]
        scoreTextData += [[str(score.HomeScore), homeScoreColor, font, [scoreXOffset, self.__rows/2], "L"]]
        scoreTextData += [[period, Scoreboard.ColorScore(), font, [self.__cols, 0], "R"]]
        scoreTextData += [[timer, Scoreboard.ColorScore(), font, [self.__cols, self.__rows/2], "R"]]
    
        self.__writeTextToImage(scoreTextData, None, self.__getTemplateFilename())

    def DrawFinalScore(self, score: Score):
        print("Drawing final score banner: {}".format(score))

        font = self.__getFontByName("FreeSansBold", self.__rows)
    
        teamNick = ScoreRetriever.TricodeToNick(score.TeamAbbr)
        if score.TeamScore > score.OtherScore:
            scoreText = teamNick.upper() + " WIN!"
            color = (0, 255, 0)
        else:
            scoreText = teamNick + " lose"
            color = (255, 0, 0)
    
        scoreText += " ({}-{})".format(score.TeamScore, score.OtherScore)
    
        scoreTextData = []
        scoreTextData += [[scoreText, color, font, [self.__padding/2, 0], "L"]]
    
        width, ignore = font.getsize(scoreText)
    
        self.__writeTextToImage(scoreTextData, (width + self.__padding, self.__rows))

    def DrawMessage(self, message: str):
        print("Drawing message: {}".format(message))
        font = self.__getFontByName("FreeSans", self.__rows)
        color = (0, 255, 0)
        textData = []
        textData += [[message, color, font, [self.__padding/2, 0], "L"]]
        width, ignore = font.getsize(message)
        self.__writeTextToImage(textData, (width + self.__padding, self.__rows))

    def DisplayImage(self, seconds: int, scroll: bool=False, isBackground: bool=False):
        print("{} image ({}s)".format("Scrolling" if scroll else "Displaying", seconds))
        if os.name == "nt":  # windows -- simulate
            cmd = "python ./ProcessSimulator.py {}".format(seconds)
        else:
            if scroll:
                command = "sudo /home/pi/rpi-rgb-led-matrix/examples-api-use/demo"
                args = " --led-rows {} --led-cols {} --led-slowdown-gpio 2 -t {} -D 1 {} >/dev/null 2>&1".format(self.__rows, self.__cols, seconds, self.__getScoreFilename())
            else:
                command = "sudo /home/pi/rpi-rgb-led-matrix/utils/led-image-viewer"
                args = " -w {} -l 1 {} --led-rows {} --led-cols {} --led-slowdown-gpio 2 >/dev/null 2>&1".format(seconds, self.__getScoreFilename(), self.__rows, self.__cols)
            cmd = shlex.split(command + args)
        return self.__runCommand(cmd, isBackground)

    def __runCommand(self, cmd: str, isBackground: bool=False):
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if isBackground:
            return proc
        proc.wait() 
        return None

    def __writeTextToImage(self, textData, xy = None, templateFile = None):
        if templateFile != None:
            im = Image.open(templateFile)
        else:
            if xy == None:
                xy = (self.__cols, self.__rows)
            im = Image.new("RGB", xy, "black")
        draw = ImageDraw.Draw(im)
    
        for index in range(0, len(textData)):
            scoreTextDatum = textData[index]
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
        im.save(self.__getScoreFilename())

    def __getFontByName(self, fontName, fontSize):
        if (fontName, fontSize) in self.__fonts:
            return self.__fonts[(fontName, fontSize)]
        print("Loading font {}, size={}.".format(fontName, fontSize))
        fontPath = fontName + ".ttf"
        if os.name != "nt":
            fontPath = "/usr/share/fonts/truetype/freefont/" + fontPath
        font = ImageFont.truetype(fontPath, fontSize)
        self.__fonts[(fontName, fontSize)] = font
        return font

    def __getDirectory(self):
        return os.path.dirname(os.path.abspath(__file__))

    def __getScoreFilename(self):
        return self.__getDirectory() + "/" + SCORE_FILE_NAME

    def __getTemplateFilename(self):
        return self.__getDirectory() + "/" + TEMPLATE_FILE_NAME

    #https://teamcolorcodes.com/milwaukee-bucks-color-codes/
    @staticmethod
    def ColorByTeam(teamAbbr: str):
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
            "SAN": (196,206,211),
            "TOR": (206,17,65),
            "UTA": (0,43,92),
            "WAS": (100,64,0,60)
        }
        return switcher.get(teamAbbr, (255, 0, 255))
    
    @staticmethod
    def ColorScore():
        return (150, 150, 150)

    @staticmethod
    def ColorWinningScore():
        return (150, 150, 50)