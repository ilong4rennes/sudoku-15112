from cmu_graphics import *
from PIL import Image
import copy, random, os, time, itertools

'''
Extra Feature:
1. Autoplayed Singletons
    - automatically showing + setting all the singletons.
2. Undo and Redo
3. Beautiful UI
'''

def play_onScreenActivate(app):
    print('In play_onScreenActivate')

def play_onAppStart(app):
    print('In play_onAppStart')
    reset(app)

def reset(app):
    # board:
    app.rows = 9
    app.cols = 9
    app.boardLeft = 560
    app.boardTop = 90
    app.boardWidth = 640
    app.boardHeight = 640
    app.cellBorderWidth = 0.5
    app.width = 1350
    app.height = 900
    # select number/cell:
    app.selectedNumber = '0'
    app.selectedCell = None, None
    # hints:
    app.autoCandidate = False
    app.showAllSingles = False
    app.showSingle = False
    app.highlightedSingles = []
    app.showObviousTuples = False
    app.highlightedTuples = []
    app.showSolution = False
    app.bannedValuePos = []
    app.bannedLegals = []
    app.bannedPos = []
    app.bannedNum = dict()
    app.solution = None
    app.tempBoard = None
    app.legalityViolationPositions = []
    app.numberOpacity = getInitNumberOpacity()
    app.buttonFill = [None] * 5
    app.noSinglesMessage = False
    app.hint1cancelMessage = False
    # undo and redo:
    app.moves = []
    app.undoneMoves = []
    # hint 2:
    app.showHint2 = False
    app.targets = []
    app.values = []
    app.regions = []
    app.highlightedTarget = None
    app.highlightedValue = None
    app.highlightedRegion = None
    app.noLegalsToRemoveMessage = False
    app.removedTargets = []  

    app.showSelectedLevel = True
    app.state = State()

def getInitNumberOpacity():
    result = []
    for _ in range(3):
        newLine = [50] * 3
        result.append(newLine)
    return result

################################################################
# Board Loading
# From: https://www.cs.cmu.edu/~112-3/notes/tp-sudoku-hints.html
################################################################

def readFile(path):
    with open(path, "rt") as f:
        return f.read()

def loadBoardPaths(filters):
    boardPaths = [ ]
    for filename in os.listdir(f'tp-starter-files/boards/'):
        if filename.endswith('.txt'):
            if filters in filename:
                boardPaths.append(f'tp-starter-files/boards/{filename}')
    return boardPaths

def loadRandomBoard(app):
    boardPaths = loadBoardPaths(app.filter)
    filename = random.choice(boardPaths)
    board = loadBoard(filename)
    return board

def loadEmptyBoard():
    board = []
    for _ in range(9):
        newLine = ['0'] * 9
        board.append(newLine)
    return board

def loadBoard(filename):
    contents = readFile(filename)
    board = []
    for line in contents.splitlines():
        newLine = []
        for number in line.split(' '):
            newLine.append(number)
        board.append(newLine)
    return board

########################################
# State Class
########################################

class State():
    def __init__(self):
        # initialize board
        board = loadEmptyBoard()
        self.board = board
        self.originalBoard = copy.deepcopy(self.board)
        self.rows, self.cols = len(self.board), len(self.board[0])
        self.solution = None

        # initialize legals
        State.getLegals(self)
        self.originalLegals = copy.deepcopy(self.legals)

    def getLegals(self):
        # initialize all the legals:
        self.legals = State.initializeAllLegals(self)

        # update the initial legals:
        for row in range(self.rows):
            for col in range(self.cols):
                if self.board[row][col] != '0':
                    # there are no legal values in fixed cells
                    self.legals[row][col] = set()
                else: # update the legal values in non-fixed cells
                    State.ban(self, row, col)

    def initializeAllLegals(self):
        allLegals = []
        for row in range(self.rows):
            newRow = []
            for col in range(self.cols):
                allNumbers = set((1, 2, 3, 4, 5, 6, 7, 8, 9))
                newRow.append(allNumbers)
            allLegals.append(newRow)
        return allLegals

    def ban(self, row, col):
        # for non-fixed cell at (row, col), remove any numbers
        # that already exist in the same row, column, or block
        allLegalsInCell = self.legals[row][col]
        cellRegions = State.getCellRegions(self, row, col)
        allLegalsInCell = State.removeNumbersInCellRegions(self, cellRegions, allLegalsInCell)
        self.legals[row][col] = allLegalsInCell

    def removeNumbersInCellRegions(self, region, allLegalsInCell):
        for (row, col) in region:
            number = int(self.board[row][col])
            if number in allLegalsInCell:
                allLegalsInCell.remove(number)
        return allLegalsInCell

    def unban(self, row, col, allLegalsInCell, number):
        if self.originalBoard[row][col] == '0':
            allLegalsInCell = self.legals[row][col]
            if number != '0':
                if int(number) in self.originalLegals[row][col]:
                    allLegalsInCell.add(int(number))
        self.legals[row][col] = allLegalsInCell

    '''
    Regions
    * A region is a list of 9 (row,col) tuples
    '''

    def getRowRegion(self, row):
        rowRegion = [tuple((row, col)) for col in range(self.cols)]
        return rowRegion
        
    def getColRegion(self, col):
        colRegion = [tuple((row, col)) for row in range(self.rows)]
        return colRegion

    def getBlockRegion(self, block):
        rowNumber = block // 3
        colNumber = block % 3
        blockRegion = []
        for i in range(3):
            for j in range(3):
                blockRegion.append(tuple((rowNumber*3+i, colNumber*3+j)))
        return blockRegion

    def getBlock(self, row, col):
        if 0 <= row <= 2 and 0 <= col <= 2: return 0
        elif 0 <= row <= 2 and 3 <= col <= 5: return 1
        elif 0 <= row <= 2 and 6 <= col <= 8: return 2
        elif 3 <= row <= 5 and 0 <= col <= 2: return 3
        elif 3 <= row <= 5 and 3 <= col <= 5: return 4
        elif 3 <= row <= 5 and 6 <= col <= 8: return 5
        elif 6 <= row <= 8 and 0 <= col <= 2: return 6
        elif 6 <= row <= 8 and 3 <= col <= 5: return 7
        elif 6 <= row <= 8 and 6 <= col <= 8: return 8

    def getBlockRegionByCell(self, row, col):
        blockRow = row // 3
        blockCol = col // 3
        blockRegion = []
        for i in range(3):
            for j in range(3):
                blockRegion.append(tuple((blockRow*3+i, blockCol*3+j)))
        return blockRegion

    def getCellRegions(self, row, col):
        cellRegions = State.getRowRegion(self, row) + State.getColRegion(self, col) + State.getBlockRegionByCell(self, row, col)
        return sorted(set(cellRegions))

    def getAllRegions(self):
        allRegions = []
        for i in range(9):
            allRegions.append(State.getRowRegion(self, i))
            allRegions.append(State.getColRegion(self, i))
            allRegions.append(State.getBlockRegion(self,i))
        return allRegions

    def getAllRegionsThatContainTargets(self, targets):
        result = []
        for row in range(app.rows):
            for col in range(app.cols):
                if targets == self.legals[row][col]:
                    result.append((row, col))
        return result

########################################
# View Function
########################################

def play_redrawAll(app):
    # background:
    drawImage(app.bgPic, app.width/2, app.height/2, align='center',
                width=app.width, height=app.height)

    # board:
    drawBoard(app)
    drawBoardBorder(app)
    drawSelectionBoard(app)
    for i in range(5):
        drawRect(0, 107+77*i, 450, 71, border=None, fill=app.buttonFill[i], opacity=20)

    # show solution
    if app.showSolution:
        pass

    # game over:
    elif isGameOver(app):
        drawRect(0, 0, app.width, app.height, fill='white', opacity=60)
        drawLabel('YOU WIN!', app.width/2, app.height/2-100, size=130, align='center', bold=True)
        drawLabel('Press to start a new game.', app.width/2, app.height/2+30, size=30, bold=True)

    # two buttons on the down right corner:
    hint1fill = 'lightSteelBlue' if app.showSingle else 'lightGray'
    hint2fill = 'rosyBrown' if app.showHint2 else 'lightGray'
    drawRect(1000, 775, 80, 60, fill=hint1fill, opacity=30)
    drawRect(1100, 775, 80, 60, fill=hint2fill, opacity=30)
    hint1fill = 'midnightBlue' if app.showSingle else 'gray'
    hint2fill = 'darkRed' if app.showHint2 else 'gray'
    hint1message = 'Set' if not app.hint1cancelMessage else 'Cancel'
    hint2message = 'Ban' if not app.noLegalsToRemoveMessage else 'Cancel'
    drawLabel(hint1message, 1000+80/2, 775+60/2, fill=hint1fill, size=18)
    drawLabel(hint2message, 1100+80/2, 775+60/2, fill=hint2fill, size=18)
    if app.showSingle:
        if app.noSinglesMessage:
            drawLabel('There are no obvious singles on board. ', 900, 50, size=20, bold=True)
            drawRect(550, 770, 260, 70, fill='white', opacity=50)
    if app.showHint2:
        if app.noLegalsToRemoveMessage:
            drawLabel('All the N unique legal values outside of N cells in all regions are banned. ', 900, 50, size=20, bold=True)
        
    # show player's level:
    if app.showSelectedLevel:
        if app.filter == 'easy': pic = app.easy
        elif app.filter == 'medium': pic = app.medium
        elif app.filter == 'hard': pic = app.hard
        elif app.filter == 'expert': pic = app.expert
        elif app.filter == 'evil': pic = app.evil
        drawImage(pic, app.width/2, app.height/2, align='center', width=app.width, height=app.height)

################################################################################
# DrawBoard
# from: https://cs3-112-f22.academy.cs.cmu.edu/exercise/4962
################################################################################

def drawBoard(app):
    for row in range(app.rows):
        for col in range(app.cols):
            drawCell(app, row, col)

def drawBoardBorder(app):
    # 3*3 border
    for i in range(3):
        for j in range(3):
            drawRect(app.boardLeft+i*app.boardWidth/3, app.boardTop+j*app.boardHeight/3,
                    app.boardWidth/3, app.boardHeight/3, fill=None,
                    border='black', borderWidth=1.5*app.cellBorderWidth)
    # 9*9 border
    drawRect(app.boardLeft, app.boardTop, app.boardWidth, app.boardHeight,
            fill=None, border='black', borderWidth=3.5*app.cellBorderWidth)

def drawCell(app, row, col):
    cellLeft, cellTop = getCellLeftTop(app, row, col)
    cellWidth, cellHeight = getCellSize(app)

    # draw shade
    if app.state.originalBoard[row][col] != '0':
        drawRect(cellLeft, cellTop, cellWidth, cellHeight,
                fill='gainsboro', border=None, opacity=80)

    # draw highlighted cell
    if (row, col) == app.selectedCell:
        drawRect(cellLeft, cellTop, cellWidth, cellHeight,
                fill='moccasin', border=None, opacity=80)

    # draw number
    numberColor = getNumberColor(app, row, col) # highlight number if differ from solution
    if app.state.board[row][col] != '0':
        drawLabel(f'{app.state.board[row][col]}', cellLeft+cellWidth/2,
                    cellTop+cellHeight/2, size=30, fill=numberColor)

    if (row, col) in app.highlightedSingles:
        highlightSingles(app, row, col)

    # show singles position (hint1)
    if (row, col) == singlePosition(app):
        highlightSingles(app, row, col)

    # show obvious tuples position (hint2)
    if app.showHint2 and app.highlightedTarget != None:
        for position in app.highlightedTarget:
            if (row, col) ==  position:
                highlightTuples(app, row, col)

    if (row, col) in app.highlightedTuples and not app.showSolution:
        highlightTuples(app, row, col)

    # show all legals (auto candidate mode)
    if app.autoCandidate and app.state.board[row][col] == '0':
        if (len(app.state.legals[row][col]) == 1 and (row, col) == singlePosition(app)):
            pass
        elif len(app.state.legals[row][col]) == 1 and app.showAllSingles:
            pass
        else:
            for number in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                if number in app.state.legals[row][col]:
                    addRowDist = ((number-1)%3) * (cellWidth/3) + cellWidth/6
                    addColDist = ((number-1)//3) * (cellHeight/3) + cellHeight/6
                    # highlight legals that can be banned:
                    fill = getFill(app, row, col, number)
                    drawLabel(f'{number}', cellLeft+addRowDist,
                            cellTop+addColDist, size=15, fill=fill)

    # draw red dot for incorrect values:
    if (row, col) in app.legalityViolationPositions:
        drawCircle(cellLeft+10, cellTop+10, 4, fill='crimson')


    # draw cell border
    drawRect(cellLeft, cellTop, cellWidth, cellHeight,
            fill=None, border='black', borderWidth=app.cellBorderWidth)

def getFill(app, row, col, number):
    if (row, col) not in app.bannedPos:
        fill = 'gray'
    elif (row, col) in app.highlightedTuples:
        fill = 'gray'
    else:
        if number in app.bannedNum[(row, col)]:
            fill = 'crimson'
        else:
            fill = 'gray'
    return fill

def getNumberColor(app, row, col):
    numberColor = 'black'
    if app.state.solution != None:
        if int(app.state.board[row][col]) != int(app.state.solution[row][col]):
            numberColor = 'crimson'
    return numberColor

def getCellLeftTop(app, row, col):
    cellWidth, cellHeight = getCellSize(app)
    cellLeft = app.boardLeft + col * cellWidth
    cellTop = app.boardTop + row * cellHeight
    return (cellLeft, cellTop)

def getCellSize(app):
    cellWidth = app.boardWidth / app.cols
    cellHeight = app.boardHeight / app.rows
    return (cellWidth, cellHeight)

def drawSelectionBoard(app):
    left = 90
    top = 535
    length = 75
    for i in range(3):
        for j in range(3):
            drawRect(left+95*i, top+95*j, length, length, fill='white', opacity=app.numberOpacity[i][j])
            drawLabel(f'{3*j+i+1}', left+95*i+length/2, top+95*j+length/2, size=32)

def highlightSingles(app, row, col):
    cellLeft, cellTop = getCellLeftTop(app, row, col)
    cellWidth, cellHeight = getCellSize(app)
    drawRect(cellLeft, cellTop, cellWidth, cellHeight, fill='lightSteelBlue',
            border=None, opacity=70)
    for value in app.state.legals[row][col]:
        drawLabel(f'{value}', cellLeft+cellWidth/2,
                    cellTop+cellHeight/2, size=28, fill='white')

def highlightTuples(app, row, col):
    cellLeft, cellTop = getCellLeftTop(app, row, col)
    cellWidth, cellHeight = getCellSize(app)
    drawRect(cellLeft, cellTop, cellWidth, cellHeight, fill='rosyBrown',
            border=None, opacity=35)

########################################
# Controller Function
########################################

'''
onMouse Events:
'''

def play_onMouseMove(app, mouseX, mouseY):
    # highlight numbers:
    left = 90
    top = 535
    length = 75
    if 90 <= mouseX <= 355 and 535 <= mouseY <= 800:
        for i in range(3):
            for j in range(3):
                if ((left+95*i <= mouseX <= left+95*i+length) and
                    (top+95*j <= mouseY <= top+95*j+length)):
                        app.numberOpacity = getInitNumberOpacity()
                        app.numberOpacity[i][j] = 30
    else:
        app.numberOpacity = getInitNumberOpacity()

    # highlight buttons:
    for i in range(5):
        if 0 <= mouseX <= 450 and 107+77*i <= mouseY <= 178+77*i:
            app.buttonFill=[None]*5
            app.buttonFill[i] = 'white'
        elif mouseX > 450 or mouseY < 107 or mouseY >= 486:
            app.buttonFill=[None]*5

def play_onMousePress(app, mouseX, mouseY):
    if app.state.board == loadEmptyBoard(): # only on first press: load random board
        app.state.board = loadRandomBoard(app)
        app.state.originalBoard = copy.deepcopy(app.state.board)
        app.showSelectedLevel = False
        app.state.getLegals()
        app.state.originalLegals = copy.deepcopy(app.state.legals)
        app.state.solution = solveSuDoku(app, app.state.originalBoard)
    else:
        if isGameOver(app) and not app.showSolution:
            reset(app)
            setActiveScreen('startSudoku')
        selectCell(app, mouseX, mouseY)
        selectNumber(app, mouseX, mouseY)
        putNumber(app)
        pressButtonLeftside(app, mouseX, mouseY) # deal with the five buttons on the left side
        pressButtonDownSide(app, mouseX, mouseY) # deal with the four buttons on the down side
        updateHighlightedSingles(app)
        updateHighlightedTuples(app)
        getHint2(app)

def selectCell(app, mouseX, mouseY):
    app.selectedNumber = '0'
    if not app.showSolution:
        for row in range(app.rows):
            for col in range(app.cols):
                cellLeft, cellTop = getCellLeftTop(app, row, col)
                cellWidth, cellHeight = getCellSize(app)
                if (cellLeft <= mouseX <= cellLeft + cellWidth and
                    cellTop <= mouseY <= cellTop + cellHeight):
                    app.selectedCell = row, col
                    app.state.ban(row, col)

def selectNumber(app, mouseX, mouseY):
    if app.selectedCell != (None, None):
        left = 90
        top = 535
        length = 75
        for i in range(3):
            for j in range(3):
                if ((left+95*i <= mouseX <= left+95*i+length) and
                    (top+95*j <= mouseY <= top+95*j+length)):
                        app.selectedNumber = str(3*j+i+1)

def putNumber(app):
    row, col = app.selectedCell
    deleteThenSet = False
    if app.selectedCell != (None, None) and app.state.originalBoard[row][col] == '0':
        if int(app.selectedNumber) != 0:
            numberInCell = app.state.board[row][col]
            if numberInCell != '0':
                deleteNumber(app, row, col, numberInCell)
                app.moves.pop(-1) # we don't need to account for the delete move here
                                  # as in this move, we first delete the existing number and set the selected number
                                  # so we'll combine the two moves into one by setting a `deleteThenSet` counter
                deleteThenSet = True
            checkLegality(app, row, col, app.selectedNumber)
            app.state.board[row][col] = app.selectedNumber
            app.undoneMoves = []
            if deleteThenSet:
                # already a number in cell, so we need to
                # delete the number first then set the selected number in it
                app.moves.append(('delete then set', (row, col), (numberInCell, app.selectedNumber)))
                # note that the last element is a set, containing two numbers before and after setting
            else:
                # set number in an empty cell, no need to delete the existing number
                app.moves.append(('set', (row, col), app.selectedNumber))
            app.selectedNumber = '0'
            updateAllLegals(app)
            updateHighlightedTuples(app)
      
def deleteNumber(app, row, col, numberInCell):
    app.moves.append(('delete', (row, col), numberInCell))
    app.undoneMoves = []
    app.state.board[row][col] = '0'
    cellRegions = app.state.getCellRegions(row, col)
    if ((row, col)) in app.legalityViolationPositions:
        app.legalityViolationPositions.remove((row, col))
    for (row, col) in cellRegions:
        if str(app.state.board[row][col]) == str(numberInCell):
            if ((row, col)) in app.legalityViolationPositions:
                app.legalityViolationPositions.remove((row, col))
        allLegalsInCell = app.state.legals[row][col]
        app.state.unban(row, col, allLegalsInCell, numberInCell)
    updateHighlightedTuples(app)

def checkLegality(app, row, col, number):
    if int(number) in app.state.legals[row][col]:
        pass
    else:
        app.legalityViolationPositions.append((row, col))
        cellRegions = app.state.getCellRegions(row, col)
        for (r, c) in cellRegions:
            if str(app.state.board[r][c]) == str(number):
                app.legalityViolationPositions.append((r, c))

def updateAllLegals(app):
    for row in range(app.state.rows):
        for col in range(app.state.cols):
            app.state.ban(row, col)

def pressButtonLeftside(app, mouseX, mouseY):
    if not (mouseX > 450 or mouseY < 107 or mouseY >= 486):
        for i in range(5):
            if 0 <= mouseX <= 450 and 107+77*i <= mouseY <= 178+77*i:
                if i == 0: # new game button
                    reset(app)
                    setActiveScreen('startSudoku')
                elif i == 1:  # auto candidate mode
                    app.autoCandidate = not app.autoCandidate
                elif i == 2: # delete button
                    if app.selectedCell != (None, None):
                        row, col = app.selectedCell
                        if app.state.originalBoard[row][col] == '0':
                            numberInCell = app.state.board[row][col]
                            deleteNumber(app, row, col, numberInCell)
                elif i == 3: # show hint 1
                    app.showSingle = not app.showSingle
                    if isSingleOnBoard(app):
                        app.noSinglesMessage = False
                        app.hint1cancelMessage = False
                    if not isSingleOnBoard(app):
                        app.noSinglesMessage = True
                    if app.noSinglesMessage:
                        app.hint1cancelMessage = True
                elif i == 4: # show hint 2
                    if not app.showSolution:
                        app.showHint2 = not app.showHint2
                        app.autoCandidate = True
                    else:
                        app.showHint2 = False
                                    
def pressButtonDownSide(app, mouseX, mouseY):
    if not app.hint1cancelMessage:
        if 565 <= mouseX <= 565+58 and 777 <= mouseY <= 777+58:
            undo(app)
        if 655 <= mouseX <= 655+58 and 777 <= mouseY <= 777+58:
            redo(app)
        if 745 <= mouseX <= 745+58 and 777 <= mouseY <= 777+58:
            showSolution(app)
            app.showSingle = False
            app.showObviousTuples = False
            app.showHint2 = False
    if 1000 <= mouseX <= 1000+80 and 775 <= mouseY <= 775+60: # set hint 1
        setSingle(app)
        app.showSingle = False
        if app.noSinglesMessage and app.hint1cancelMessage:
            app.hint1cancelMessage = False
    if 1100 <= mouseX <= 1100+80 and 775 <= mouseY <= 775+60: # ban some legals (hint 2)
        applyRule2(app)
        app.showHint2 = False

def showSolution(app):
    if not app.showSolution:
        app.tempBoard = copy.deepcopy(app.state.board)
        app.tempLgtVltPositions = copy.deepcopy(app.legalityViolationPositions)
        if app.state.solution == None:
            # app.state.solution = solveSuDoku(app, app.state.originalBoard)
            app.state.board = app.state.solution
        else:
            app.state.board = app.state.solution
        app.legalityViolationPositions = []
        app.showSolution = True
    else:
        app.showSolution = False
        app.state.board = app.tempBoard
        app.legalityViolationPositions = app.tempLgtVltPositions



'''
onKey Events:
'''

def play_onKeyPress(app, key):
    # use keyboard to put number and select cell:
    if app.selectedCell != (None, None):
        row, col = app.selectedCell
        if key in ('1', '2', '3', '4', '5', '6', '7', '8', '9'):
            if app.state.originalBoard[row][col] == '0':
                app.selectedNumber = int(key)
                putNumber(app)
        elif key == 'backspace':
            if app.state.originalBoard[row][col] == '0':
                numberInCell = app.state.board[row][col]
                deleteNumber(app, row, col, numberInCell)
        elif key == 'up': row -= 1
        elif key == 'down': row += 1
        elif key == 'left': col -= 1
        elif key == 'right': col += 1
        if 0 <= row <= 8 and 0 <= col <= 8:
            app.selectedCell = row, col
  
    if key == 'a': # highlight all singletons
        app.showAllSingles = not app.showAllSingles

    elif key == 's': # set all singletons
        if app.showAllSingles:
            setAllSingles(app)
            app.showAllSingles = False
    
    elif key == 'q':
        if not app.showSolution:
            app.showHint2 = not app.showHint2
            app.autoCandidate = True
        else:
            app.showHint2 = False
    
    elif key == 'w':
        applyRule2(app)
        app.showHint2 = False

    elif key == 'u':
        if not app.hint1cancelMessage: undo(app)
  
    elif key == 'r':
        if not app.hint1cancelMessage: redo(app)
    
    # for my own testing purposes, please ignore. 
    # elif key == 'h':
    #     app.showObviousTuples = not app.showObviousTuples

    # elif key == 'e':
    #     updateLegalsForObviousTuples(app)
    
    elif key == 'space':
        app.autoCandidate = not app.autoCandidate

    updateHighlightedSingles(app)
    updateHighlightedTuples(app)
    getHint2(app)

########################################
# First Level for Hint 1
# highlight the obvious singles on board
########################################

def getSinglePosition(app):
    for row in range(app.rows):
        for col in range(app.cols):
            if (len(app.state.legals[row][col]) == 1 and 
                app.state.board[row][col] == '0'):
                    return (row, col)

def isSingleOnBoard(app):
    return getSinglePosition(app) != None

def singlePosition(app):
    if app.showSingle:
        if isSingleOnBoard(app):
            return getSinglePosition(app)

########################################
# Second Level for Hint 1
# set the obvious singles on board
########################################

def setSingle(app):
    if app.showSingle:
        if isSingleOnBoard(app):
            app.noSinglesMessage = False
            row, col = singlePosition(app)
            for number in app.state.legals[row][col]:
                numberInCell = number
            app.state.board[row][col] = numberInCell
            app.moves.append(('set', (row, col), numberInCell))
            app.showSingle = not app.showSingle
        else:
            app.showSingle = False
            app.noSinglesMessage = True

########################################
# Hint 2
# From: https://www.cs.cmu.edu/~112-3/notes/tp-sudoku-hints.html
########################################

    # First level:
    # highlight the cells

def getHint2(app):
    app.noLegalsToRemoveMessage = False
    app.targets = []
    app.values = []
    app.regions = []
    if app.showHint2:
        for region in app.state.getAllRegions():
            for N in range(2, 6):
                getValues(region, N)
    if app.targets != []:
        app.highlightedTarget = app.targets[0]
        app.highlightedValue = app.values[0]
        app.highlightedRegion = app.regions[0]

def getValues(region, N):
    for positions in itertools.combinations(region, N):
        legalsSet = set()
        targets = set()
        for position in positions:
            row, col = position
            if app.state.board[row][col] == '0':
                if N == 2:
                    if len(app.state.legals[row][col]) == N:
                        for value in app.state.legals[row][col]:
                            legalsSet.add(value)
                            targets.add((row, col))
                else:
                    if N-1 <= len(app.state.legals[row][col]) <= N:
                        for value in app.state.legals[row][col]:
                            legalsSet.add(value)
                            targets.add((row, col))
        if len(legalsSet) == len(targets) == N:
            if hasLegalsToRemove(app, region, targets,legalsSet):
                app.noLegalsToRemoveMessage = False
                if legalsSet not in app.removedTargets:
                    app.values.append(legalsSet)
                    app.targets.append(targets)
                    app.regions.append(region)
            else:
                if app.targets == []:
                    app.noLegalsToRemoveMessage = True
                    app.highlightedTarget = None
                    app.highlightedValue = None
                    app.highlightedRegion = None
        
def hasLegalsToRemove(app, region, targets,legalsSet):
    for (row, col) in region:
        if (row, col) not in targets:
            for number in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                if (number in legalsSet and 
                    number in app.state.legals[row][col]):
                        return True
    return False

    # Second level:
    # ban some of the legal values on board after we found the obvious tuples

def applyRule2(app):
    if app.showHint2:
        if app.highlightedRegion != None:
            for (row, col) in app.highlightedRegion:
                if (row, col) not in app.highlightedTarget:
                    for number in (1, 2, 3, 4, 5, 6, 7, 8, 9):
                        if (number in app.highlightedValue and 
                            number in app.state.legals[row][col] and
                            number != app.state.solution[row][col]):
                                app.state.legals[row][col].remove(number)
                        else:
                            app.noLegalsToRemoveMessage = True
            app.showHint2 = False
            getHint2(app)
            if app.targets != []:
                app.removedTargets.append(app.targets.pop(0))
                app.values.pop(0)
                app.regions.pop(0)
            else:
                app.noLegalsToRemoveMessage = True

#########################################
# Extra Feature: highlight all singletons
#########################################

def updateHighlightedSingles(app):
    app.highlightedSingles = []
    if app.showAllSingles:
        showSinglesPositions(app)
        if app.highlightedSingles == []:
            app.showAllSingles = False

def showSinglesPositions(app):
    for row in range(app.rows):
        for col in range(app.cols):
            if (len(app.state.legals[row][col]) == 1 and 
                app.state.board[row][col] == '0' and
                set([app.state.solution[row][col]]) == app.state.legals[row][col]):
                    app.highlightedSingles.append((row, col))

#########################################
# Extra Feature: set all singletons
#########################################

def setAllSingles(app):
    if app.showAllSingles:
        numberList = []
        if app.highlightedSingles != [None]:
            for (row, col) in app.highlightedSingles:
                onlyLegal = app.state.legals[row][col]
                for number in onlyLegal:
                    app.state.board[row][col] = number
                    numberList.append(number)
        app.moves.append(('set all', app.highlightedSingles, numberList))
        app.highlightedSingles = []
        app.showAllSingles = not app.showAllSingles

########################################
# Hint 2 (my own version)
# This is written for the convenience of testing, 
# so please ignore this chunk of code when you are viewing. 
########################################

def updateHighlightedTuples(app):
    app.highlightedTuples = []
    app.bannedPos = []
    app.bannedNum = dict()
    if app.showObviousTuples:
        showObviousPairsPositions(app, app.highlightedTuples)
        showObviousTriplesPositions(app, app.highlightedTuples)
      
def showObviousPairsPositions(app, result):
    for i in range(9):
        rowRegion = app.state.getRowRegion(i)
        colRegion = app.state.getColRegion(i)
        blockRegion = app.state.getBlockRegion(i)
        for region in (rowRegion, colRegion, blockRegion):
            for n in (2, 3, 4, 5):
                findObviousPairsInRegion(app, region, result, n)

def findObviousPairsInRegion(app, region, result, n):
    seenPositions = []
    seenLegals = []
    pairsList = []
    for (row, col) in region:
        legalsInCell = app.state.legals[row][col]
        if (app.state.board[row][col] == '0' and
            len(legalsInCell) == n):
                if legalsInCell in seenLegals and seenLegals.count(legalsInCell) == n-1:
                    index = seenLegals.index(legalsInCell)
                    result.append(seenPositions[index])
                    result.append((row, col))
                    pairsList.append(legalsInCell)
                else:
                    seenPositions.append((row, col))
                    seenLegals.append(legalsInCell)
    for (row, col) in region:
        if (app.state.board[row][col] == '0' and
            (row, col) not in result):
                legalsInCell = app.state.legals[row][col]
                for legal in legalsInCell:
                    for pairs in pairsList:
                        if legal in pairs:
                            if ((row, col), legal) not in app.bannedLegals:
                                app.bannedLegals.append(((row, col), legal))
                            getBannedPosAndNum(app)

def getBannedPosAndNum(app):
    for (position, number) in app.bannedLegals:
        app.bannedPos.append(position)
        row, col = position
        if (row, col) not in app.bannedNum:
            l = [number]
            app.bannedNum[(row, col)] = set(l)
        else:
            app.bannedNum[(row, col)].add(number)

def pairsInLegals(app, pairs, row, col):
    for value in pairs:
        if value in app.state.legals[row][col]:
            return True
    return False

def showObviousTriplesPositions(app, result):
    pass

def updateLegalsForObviousTuples(app):
    if app.showObviousTuples:
        for (row, col) in app.bannedPos:
            for number in app.bannedNum[(row, col)]:
                if int(number) in app.state.legals[row][col]:
                    app.state.legals[row][col].remove(number)
        app.showObviousTuples = False

########################################
# Undo and Redo
########################################

def undo(app):
    app.showSingle = False
    if app.moves != []:
        move, position, number = app.moves[-1]
        if move == 'set':
            row, col = position
            delNumber(app, row, col, number)
        elif move == 'delete':
            row, col = position
            setNumber(app, row, col, number)
        elif move == 'delete then set':
            row, col = position
            numberBefore, numberAfter = number # in this case, `number` is a set that
                                                # contain two numbers before and after setting
            delNumber(app, row, col, numberAfter)
            setNumber(app, row, col, numberBefore)
        elif move == 'set all':
            for (row, col) in position:
                app.state.board[row][col] = '0'
                updateHighlightedTuples(app)
        app.undoneMoves.append(app.moves.pop())
  
def delNumber(app, row, col, number): # similar to deleteNumber(app, row, col, numberInCell)
    app.state.board[row][col] = '0'
    cellRegions = app.state.getCellRegions(row, col)
    if ((row, col)) in app.legalityViolationPositions:
        app.legalityViolationPositions.remove((row, col))
    for (row, col) in cellRegions:
        if str(app.state.board[row][col]) == str(number):
            if ((row, col)) in app.legalityViolationPositions:
                app.legalityViolationPositions.remove((row, col))
        allLegalsInCell = app.state.legals[row][col]
        app.state.unban(row, col, allLegalsInCell, number)

def setNumber(app, row, col, number): # similar to putNumber(app)
    if app.state.originalBoard[row][col] == '0':
        checkLegality(app, row, col, number)
        app.state.board[row][col] = number
        updateAllLegals(app)

def redo(app):
    if app.undoneMoves != []:
        move, position, number = app.undoneMoves[-1]
        if move == 'set':
            row, col = position
            setNumber(app, row, col, number)
        elif move == 'delete':
            row, col = position
            delNumber(app, row, col, number)
        elif move == 'delete then set':
            row, col = position
            numberBefore, numberAfter = number # in this case, `number` is a set that
                                                # contain two numbers before and after setting
            setNumber(app, row, col, numberBefore)
        elif move == 'set all':
            for index in range(len(position)):
                row, col = position[index]
                numberInCell = number[index]
                app.state.board[row][col] = numberInCell
                updateHighlightedTuples(app)
        app.moves.append(app.undoneMoves.pop())

########################################
# Backtracker
########################################

def solveSuDoku(app, board):
    solutionBoard = copy.deepcopy(board)
    solutionLegals = getBoardLegals(app, board)
    return solve(app, solutionBoard, solutionLegals)

def getBoardLegals(app, board):
    legals = app.state.initializeAllLegals()
    for row in range(app.rows):
        for col in range(app.cols):
            if board[row][col] != '0':
                legals[row][col] = set()
            else:
                legals[row][col] = banLegals(app, row, col)
    return legals

def banLegals(app, row, col):
    allLegalsInCell = set((1, 2, 3, 4, 5, 6, 7, 8, 9))
    cellRegions = app.state.getCellRegions(row, col)
    allLegalsInCell = app.state.removeNumbersInCellRegions(cellRegions, allLegalsInCell)
    return allLegalsInCell

def solve(app, board, legals):
    if isFull(board):
        return board
    else:
        row, col = findLeastLegalsPosition(app, board)
        for number in legals[row][col]:
            board[row][col] = number
            tempLegals = copy.deepcopy(legals)
            updateLegalValues(app, row, col, board, legals)
            solution = solve(app, board, legals)
            if solution != None:
                return solution
            board[row][col] = '0'
            legals = tempLegals
        return None

def updateLegalValues(app, row, col, board, legals):
    cellRegions = app.state.getCellRegions(row, col)
    for (row, col) in cellRegions:
        legals[row][col] = findPositionLegals(app, row, col, board)

def findPositionLegals(app, row, col, board):
    L = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    allLegalsInCell = set(L)
    cellRegions = app.state.getCellRegions(row, col)
    for newRow, newCol in cellRegions:
        number = int(board[newRow][newCol])
        if number in allLegalsInCell:
            allLegalsInCell.remove(number)
    return allLegalsInCell

def findLeastLegalsPosition(app, board):
    leastCount = 10
    leastRow, leastCol = None, None
    for row in range(app.rows):
        for col in range(app.cols):
            if board[row][col] == '0':
                currCount = len(app.state.legals[row][col])
                if currCount < leastCount:
                    leastCount = currCount
                    leastRow, leastCol = row, col
    return leastRow, leastCol

def isFull(board):
    rows, cols = len(board), len(board[0])
    for row in range(rows):
        for col in range(cols):
            if board[row][col] == '0':
                return False
    return True

def isGameOver(app):
    if app.legalityViolationPositions != []:
        return False
    for row in app.state.board:
        for value in row:
            if value == '0':
                return False
    return True

# def main():
#     runApp()

# main()