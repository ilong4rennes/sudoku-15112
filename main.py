from cmu_graphics import *

from startSudoku import *
from play import *
from help import *

'''
Extra Feature:
1. Autoplayed Singletons
    - automatically showing + setting all the singletons.
2. Undo and Redo
3. Beautiful UI
'''

##################################
# App
##################################

def onAppStart(app):
    print('In onAppStart')

def onAppStop(app):
    print('In onAppStop')

##################################
# main 
##################################

def main():
    runAppWithScreens(initialScreen='startSudoku')

main()