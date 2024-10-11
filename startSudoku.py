from cmu_graphics import *
from PIL import Image

def startSudoku_onAppStart(app):
    print('In startSudoku_onAppStart')
    app.width = 1350
    app.height = 900
    app.image = Image.open('image/start.png')
    app.image = CMUImage(app.image)
    app.bgPic = Image.open('image/playBackground.png')
    app.bgPic = CMUImage(app.bgPic)
    app.help = Image.open('image/help.png')
    app.help = CMUImage(app.help)
    app.easy = Image.open('image/easy.png')
    app.easy = CMUImage(app.easy)
    app.medium = Image.open('image/medium.png')
    app.medium = CMUImage(app.medium)
    app.hard = Image.open('image/hard.png')
    app.hard = CMUImage(app.hard)
    app.expert = Image.open('image/expert.png')
    app.expert = CMUImage(app.expert)
    app.evil = Image.open('image/evil.png')
    app.evil = CMUImage(app.evil)
    app.filter = None
    app.level = ['easy', 'medium', 'hard', 'expert', 'evil']

def startSudoku_onScreenActivate(app):
    print('In startSudoku_onScreenActivate')

def startSudoku_redrawAll(app):
    drawImage(app.image, app.width/2, app.height/2, align='center', 
              width=app.width, height=app.height)

def startSudoku_onMousePress(app, mouseX, mouseY):
    for i in range(5):
        if app.width/2-180 <= mouseX <= app.width/2+180 and 410+i*67-25 <= mouseY <= 410+i*67+25:
            app.filter = app.level[i]
            setActiveScreen('play')
    if 270 <= mouseX <= 630 and 720<=mouseY<=770:
        setActiveScreen('help')
        
def startSudoku_onKeyPress(app, key):
    pass

