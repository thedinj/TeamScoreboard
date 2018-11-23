import time
import subprocess
import os
from ScoreRetriever import Score
from PIL import Image, ImageFont, ImageDraw

ROWS = 16
COLS = 64
PADDING = 30
SCORE_FILE_NAME = "score.ppm"  #! used to have path: /home/pi/TeamScoreboard/
TEMPLATE_FILE_NAME = "scoreboard_bg.ppm"  #! this too: /home/pi/TeamScoreboard/

class Scoreboard(object):
    __fonts = {}

    def DisplayScore(self, score: Score, seconds: int, isBackground: bool=False):
        print("Displaying score: {} ({}s)".format(score, seconds))
        return self.__displayImage(scroll, isBackground)

    def DisplayFinalScore(self, score: Score, seconds: int, isBackground: bool=False):
        print("Scrolling final score banner: {} ({}s)".format(score, seconds))
        return self.__displayImage(scroll, isBackground)

    def DisplayMessage(self, message: str, seconds: int, scroll: bool=False, isBackground: bool=False):
        print("{} message: {} ({}s)".format("Scrolling" if scroll else "Displaying", message, seconds))
        font = self.__getFontByName("FreeSans", ROWS)
        color = (0, 255, 0)
        textData = []
        textData += [[message, color, font, [PADDING/2, 0], "L"]]
        width, ignore = font.getsize(message)
        self.__writeScoreboardImages(textData, (width + PADDING, ROWS))
        return self.__displayImage(scroll, isBackground)

    def __displayImage(self, seconds: int, scroll: bool=False, isBackground: bool=False):
        if os.name == "nt":  # windows -- simulate
            cmd = "python ./ProcessSimulator.py {}".format(seconds)
        else:
            if scroll:
                command = "sudo /home/pi/rpi-rgb-led-matrix/examples-api-use/demo"
                args = " --led-rows {} --led-cols {} --led-slowdown-gpio 2 -t {} -D 1 {} >/dev/null 2>&1".format(ROWS, COLS, displayTime, SCORE_FILE_NAME)
            else:
                command = "sudo /home/pi/rpi-rgb-led-matrix/utils/led-image-viewer"
                args = " -w {} -l 1 {} --led-rows {} --led-cols {} --led-slowdown-gpio 2 >/dev/null 2>&1".format(displayTime, SCORE_FILE_NAME, ROWS, COLS)
            cmd = shlex.split(command + args)
        return self.__runCommand(cmd, isBackground)

    def __runCommand(self, cmd: str, isBackground: bool=False):
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if isBackground:
            return proc
        proc.wait() 
        return None

    def __writeScoreboardImages(self, textData, xy = None, templateFile = None):
        if templateFile != None:
            im = Image.open(templateFile)
        else:
            if xy == None:
                xy = (COLS, ROWS)
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
        im.save(SCORE_FILE_NAME)

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
            "SAS": (196,206,211),
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