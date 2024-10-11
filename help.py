from cmu_graphics import *

##################################
# help
##################################

def help_onAppStart(app):
    print('In help_onAppStart')

def help_onScreenActivate(app):
    print('In help_onScreenActivate')

def help_onKeyPress(app, key):
    if key == 's': setActiveScreen('startSudoku')

def help_onMousePress(app, mouseX, mouseY):
    pass

def help_redrawAll(app):
    drawImage(app.help, app.width/2, app.height/2, align='center', 
              width=app.width, height=app.height)
