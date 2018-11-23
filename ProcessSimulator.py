import sys
import time

#import os
#os.chdir("E:/Users/thedinj/Programming Files/Programs/TeamScoreboard/TeamScoreboard")

if __name__ == '__main__':
    seconds = 2
    if len(sys.argv) > 1:
        seconds = int(sys.argv[1])
    time.sleep(seconds)
