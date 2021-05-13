import os
import sys
import json
import time
import random
import sqlite3 as sql
import string
import pygame
import tabulate

pygame.init() # initialising the pygame module 
basedir = os.path.join(os.path.abspath(__file__))

class Button:
    def __init__(self, colour=(0, 0, 0), tColour=(255, 255, 255), func=None, geo=[0, 0, 0, 0], text="", params=[], fontSize=15, hasReturn=False, hasFunc=False): # Geo = {x, y, w, h}
        self.text = text # Text to be displayed
        self.geo = geo # Position of the button
        self.colour = colour # Button Colour
        self.tColour = tColour # Text Colour
        self.font = pygame.font.SysFont("Arial", fontSize)
        self.params = params
        self.hasReturn = hasReturn
        self.hasFunc = hasFunc
        if func:
            self.func = func
            self.hasFunc = True # Setting the function of the button
    
    def setParams(self, newParams):
        self.params = newParams # re-set paramaters of a function

    def getParams(self): # get params of button func
        return self.params

    def getHasReturn(self): # get whether func has return or not
        return self.hasReturn

    def getHasFunc(self): # get whether there is a func or not
        return self.hasFunc

    def setText(self, newText): # changing displayed text
        self.text = newText
 
    def updateTextColour(self, newColour): # updating the colour of the text
        self.tColour = newColour

    def updateColour(self, newColour): # updating the background colour of the button
        self.colour = newColour

    def draw(self): 
        pygame.draw.rect(window, self.colour, self.geo) # draw the box
        drawnText = self.font.render(self.text, True, self.tColour) # draw the text
        window.blit(drawnText, pygame.math.Vector2(self.geo[0] + 5, self.geo[1] + 5)) # draw to screen
    
    def callFunc(self, mouse):
        if self.geo[0] < mouse[0] < self.geo[0] + self.geo[2] and self.geo[1] < mouse[1] < self.geo[1] + self.geo[3]: # Checking if the mouse is within the boundaries
            self.func(*self.params) # call the function that was passed in

    def getFunc(self, mouse):
        if self.geo[0] < mouse[0] < self.geo[0] + self.geo[2] and self.geo[1] < mouse[1] < self.geo[1] + self.geo[3]: # Checking if the mouse is within the boundaries
            return self.func

class GridCell:
    def __init__(self, colour=(255, 255, 255), tColour=(0, 0, 0), geo=[0, 0, 0, 0], char='', gridPos=(0, 0)):
        self.colour = colour # the colour of the background (default is white)
        self.tColour = tColour # the colour of the text
        self.geo = geo # XYWH
        self.text = char # the character that will be drawn
        self.font = pygame.font.SysFont("Arial", 30) # the font for the characters in the cell
        self.gridPos = gridPos
        self.finalColour = (0, 255, 0)
        self.isFinished = False
    
    def draw(self): 
        pygame.draw.rect(window, self.colour if not self.isFinished else self.finalColour, self.geo)
        drawnText = self.font.render(self.text, True, self.tColour)
        window.blit(drawnText, pygame.math.Vector2(self.geo[0] + 5, self.geo[1] + 5)) # drawing the characters to the screen at the same position as the background + 5 to center them a bit more

    def update(self, colour):
        self.colour = colour # update the colour of the cell

    def setFinished(self):
        self.isFinished = True # lock the cells colour
    
    def setFinalColour(self, newColour):
        self.finalColour = newColour

    def onClick(self, mouse, colour=(0, 255, 0)):
        if self.geo[0] < mouse[0] < self.geo[0] + self.geo[2] and self.geo[1] < mouse[1] < self.geo[1] + self.geo[3]:
            self.colour = colour    
            return self.gridPos # return the grid position when clicked
        else: return None 

    def getGridPos(self):
        return self.gridPos # return the grid pos

class InputBox:
    def __init__(self, geo=[0, 0, 0, 0], colour=(255, 255, 255), tColour=(0, 0, 0), borderColour=(0, 0, 0), borderThickness=3, placeholderText=None):
        self.geo = geo # dimensions (x, y, w, h)
        self.colour = colour # colour of the box
        self.tColour = tColour # colour of the text
        self.borderColour = borderColour # colour of the border
        self.borderThickness = borderThickness # thickness of the border surrounding the box
        self.font = pygame.font.SysFont("Arial", 20) # font of the text displayed
        if placeholderText: self.placeholderText = placeholderText # placeholder text if there is any
        self.focused = False # state of the box
        self.text = '' # the users text

    def getFocused(self):
        return self.focused # gets box state

    def unfocus(self):
        self.focused = False # unfocus the window

    def getText(self):
        return self.text # return the users text

    def draw(self):
        pygame.draw.rect(window, self.borderColour, [
            self.geo[0] - self.borderThickness,
            self.geo[1] - self.borderThickness,
            self.geo[2] + self.borderThickness * 2,
            self.geo[3] + self.borderThickness * 2,
        ]) # drawing input box border
        pygame.draw.rect(window, self.colour, self.geo) # drawing input box

        if not self.focused and len(self.text) == 0: # deciding whether or not to display placeholder text
            placeholderConditions = True
        else:
            placeholderConditions = False

        drawnText = self.font.render(self.text if not placeholderConditions else self.placeholderText, True, self.tColour) # writing the text
        window.blit(drawnText, pygame.math.Vector2(self.geo[0], self.geo[1])) # writing to screen
    
    def focus(self, mouse, inputBoxes):
        if self.geo[0] < mouse[0] < self.geo[0] + self.geo[2] and self.geo[1] < mouse[1] < self.geo[1] + self.geo[3]: # if the user clicks inside the input box
            for ipb in inputBoxes:
                if ipb.getFocused():
                    ipb.unfocus() # unfocusing all other input boxes
            self.focused = not self.focused # toggling the focus of the current box

    def writeToText(self, char):
        if self.focused: # if the current box is focused
            if char == '\x1B': # if user clicks "Escape" exit focus
                self.focused = False
                return

            if char == '\x08': # if user clicks backspace
                if len(self.text) > 0: # if length of text is greater than 0
                    self.text = self.text[:-1] # remove last character from text string
                return

            self.text += char # add character to text string
            return

def mainMenu(COLOUR_SCHEME): # Main Menu Loop
    mButtons = []
    pygame.display.set_caption("Main Menu") # Settings the title of the game window
    mButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=themeChoice, geo=[
        int(WIDTH / 2 - 50), int(HEIGHT / 2 - 25), 100, 50], text="Play Menu", params=[COLOUR_SCHEME])) # adding a play button
    mButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=leaderboardMenu, geo=[
        int(WIDTH / 2 - 50), int(HEIGHT / 2 + 25), 100, 50], text="Leaderboard", params=[COLOUR_SCHEME])) # Adding a leaderboard button
    mButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=settingsMenu, geo=[
        int(WIDTH / 2 - 50), int(HEIGHT / 2 + 75), 100, 50], text="Settings Menu", params=[COLOUR_SCHEME])) # adding a settings button

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # allowing the user to quit the window
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for button in mButtons:
                    if button.getHasFunc():
                        button.callFunc(mouse)
        
        window.fill(COLOURS[COLOUR_SCHEME[0]['background']]) # refreshing the screen
        for x in mButtons:
            x.draw() # drawing the buttons to screen

        pygame.display.flip() # refreshing the display
        clock.tick(FPS)

def playMenu(grid, words, wordCoords, cleanWords, themeName, COLOUR_SCHEME): # Game Menu Loop
    # cleanWords is so that I can display the words the user is to find, as they are flipped backwards on generation.
    startTime = time.time()
    pButtons = []
    pygame.display.set_caption("Play Menu") # Changing the caption of the window
    pButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=mainMenu, geo=[WIDTH - 100, 0, 100, 50], text="Main Menu", params=[COLOUR_SCHEME])) # Adding a button to fall back to the main menu
    pButtons.append(timeDisp := Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[WIDTH - 100, 50, 100, 50], text="Time: "))

    # declaring variables

    words = sorted(words, key=len, reverse=True)
    cleanWords = sorted(cleanWords, key=len, reverse=True)

    gridSize = len(grid)
    screenCenter = ( WIDTH / 2, HEIGHT / 2 ) # getting the very middle of the screen
    cellSize = (
        (screenCenter[0] / gridSize) / 1.2,
        (screenCenter[1] / gridSize) * 1.75
    ) # generating the size of the cells
    numSelected = 0
    cleanWordsCopy = cleanWords
    selected = [[], []]
    completedWordCoords = []
    wordDisplay = []
    foundWords = []

    cells = [] # creating an array for cell objects
    for x in range(0, gridSize): # creating it the same size as the original grid
        cells.append([]) 
        for y in range(0, gridSize): 
            cells[x].append(GridCell(
                colour=COLOURS[COLOUR_SCHEME[0]['background']],
                tColour=COLOURS[COLOUR_SCHEME[0]['text']],
                geo=[50 + cellSize[0] * (x), 50 + cellSize[1] * (y), cellSize[0]+5, cellSize[1]-4], 
                char=grid[x][y],
                gridPos=[x, y]
            )) # adding GridCell objects to another grid array
 
    for i in range(-2, 3):
        wordDisplay.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[(screenCenter[0] + (WIDTH / 4)) - 50, screenCenter[1] - (100 * i), 100, 50], text=cleanWords[i+2], fontSize=30))

    while True: # Beginning a loop for the game
        for event in pygame.event.get(): # getting everything that is happening
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in pButtons:
                    if button.getHasFunc():
                        button.callFunc(pygame.mouse.get_pos()) # Calling the functions associated with buttons

                for row in cells: # for every row in the cells array
                    for cell in row:  # for every item in each row
                        cellPos = cell.onClick(pygame.mouse.get_pos(), colour=COLOURS[random.choice([x for x in COLOURS.keys() if x[:6] == "PASTEL"])]) # returns None or a position in the grid

                        if cellPos != None: # If it returns a position
                            if numSelected == 0: # if the current number selected is 0
                                selected[0] = cellPos # setting the first item in "Selected" to the current position
                                numSelected += 1 # incremeting the num selected
                            
                            elif numSelected == 1: # if there is one item selected already
                                if cellPos != selected[0]: # if that item isnt the first item
                                    selected[1] = cellPos
                                    numSelected += 1
                            
                            else: # if there are already 2 selected
                                for row in cells: 
                                    for cell in row:
                                        cell.update(COLOURS[COLOUR_SCHEME[0]['background']]) # resetting the grid to white
                                numSelected = 0 # resetting the number selected
                                selected = [[], []] # restting the items selected

        for idx, coord in enumerate(wordCoords): # checking through every word coordinate
            wordColour = random.choice([x for x in COLOURS.keys() if x[:6] == "PASTEL"])
            if coord == selected or coord == [selected[1], selected[0]]: # if the coordinates selected are equal to word coordinate
                startingPosition, endingPosition = coord[0], coord[1] # setting starting and ending position
                currentPos = startingPosition # setting current position
                while currentPos != endingPosition: # checking through every cell
                    curCell = cells[currentPos[0]][currentPos[1]] # getting current cell
                    curCell.update(colour=COLOURS[wordColour]) # updating cell
                    curCell.setFinalColour(COLOURS[wordColour])
                    curCell.setFinished() # locking the cell colour
                    currentPos[0 if coord[0][0] != coord[1][0] else 1] += 1 # incrementing horizontal / vertical depening on coordinates

                endCell = cells[endingPosition[0]][endingPosition[1]] # setting the final cell (as it isnt included in the while loop)
                endCell.update(colour=COLOURS[wordColour])
                endCell.setFinalColour(COLOURS[wordColour])
                endCell.setFinished() 

                numSelected = 0 # resetting number selected 
                selected = [[], []] # resetting selected coordinates
                completedWordCoords.append(coord) # adding word to found words
                foundWords.append(cleanWords[idx])
                cleanWordsCopy.pop(idx)
                wordCoords.pop(idx) # removing word from lists
                wordDisplay.pop(idx)

        if wordDisplay == []: # if there are no words left
            finishTime = time.time() # getting current time
            totalTime = finishTime - startTime # getting total time
            return finishMenu(COLOUR_SCHEME, totalTime, themeName) # sending user to finish menu

        curTime = time.time() # getting time
        nowTime = curTime - startTime # calculating time taken
        curMins = int(nowTime // 60)
        curSecs = int(nowTime % 60) # parsing to mins / secs
        timeDisp.setText(f"Time: {curMins}:{curSecs:02d}") # displaying current time taken

        window.fill(COLOURS[COLOUR_SCHEME[0]['background']]) # clearing the screen
        for x in pButtons: x.draw() # redrawing buttons
        for x in wordDisplay: x.draw() # drawing words

        for row in cells: 
            for cell in row: cell.draw() # drawing the cells to the screen

        # Draw Outline
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(50, 50), pygame.math.Vector2(screenCenter[0] - 50, 50), 3) # Top
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(50, HEIGHT - 50), pygame.math.Vector2(screenCenter[0] - 50, HEIGHT - 50), 3) # Bottom
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(50, 50), pygame.math.Vector2(50, HEIGHT - 50), 3) # Left
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(screenCenter[0] - 50, 50), pygame.math.Vector2(screenCenter[0] - 50, HEIGHT - 50), 3) # Right
         
        # Draw columns
        for i in range(0, gridSize):
            pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], 
                pygame.math.Vector2(50 + cellSize[0] * (i), 50),
                pygame.math.Vector2(50 + cellSize[0] * (i), HEIGHT - 50), 3
            )

        # Draw rows
        for i in range(0, gridSize):
            pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']],
                pygame.math.Vector2(50, 50 + cellSize[1] * (i)),
                pygame.math.Vector2(screenCenter[0] - 50, 50 + cellSize[1] * (i)), 3
            )


        pygame.display.flip()
        clock.tick(FPS)

def settingsMenu(COLOUR_SCHEME): # Settings Menu Loop
    sButtons = [] 
    pygame.display.set_caption("Settings Menu") # Changing the caption of the window
    sButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=mainMenu, geo=[WIDTH-100, 0, 100, 50], text="Main Menu", params=[COLOUR_SCHEME])) # Adding a button to fall back to the main menu
    sButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=changeColourTheme, geo=[50, 100, 110, 50], text="Change Theme", params=[COLOUR_SCHEME], hasReturn=True))


    while True: # Beginning a loop for the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit() # Quitting the window
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for button in sButtons:
                    if not button.getHasReturn():
                        button.setParams([COLOUR_SCHEME])
                        if button.getHasFunc():
                            button.callFunc(mouse) # Calling button functions
                    else:
                        if button.getHasFunc():
                            COLOUR_SCHEME = [button.getFunc(mouse)(*button.getParams())] # getting the new colour scheme            

        window.fill(COLOURS[COLOUR_SCHEME[0]['background']])
        for x in sButtons: x.draw(); x.updateColour(COLOURS[COLOUR_SCHEME[0]['buttons']]); x.updateTextColour(COLOURS[COLOUR_SCHEME[0]['text']]) # updaing buttons to new colour scheme
        
        
        pygame.display.flip()
        clock.tick(FPS)

def leaderboardMenu(COLOUR_SCHEME): # Leaderboard Menu Loop
    lButtons = []
    titleButtons = []
    lButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=mainMenu, geo=[0, 0, 100, 50], text="Main Menu", params=[COLOUR_SCHEME])) # fallback button for main menu
    lButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttonsVar2']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=wipeDB, geo=[WIDTH/2 - 75, HEIGHT-50, 150, 50], text="Clear Database", params=[COLOUR_SCHEME]))

    titleButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[225, 110, 100, 50], text="User Name")) # column name
    titleButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[590, 110, 100, 50], text="Theme Name")) # column name
    titleButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[990, 110, 100, 50], text="Time Taken")) # column name

    pygame.display.set_caption("Leaderboard")

    conn = sql.connect('components/database.db') # connecting to the database
    cursor = conn.cursor()

    data = cursor.execute("SELECT * FROM Players ORDER BY time ASC").fetchall() # getting all data from database

    conn.commit()
    conn.close()

    for idx, item in enumerate(data):
        if idx < 8:
            titleButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[105, 160+(60*idx), 100, 50], text=item[1]))
            titleButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[435, 160+(60*idx), 100, 50], text=item[2]))
            titleButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[(WIDTH-430)+5, 160+(60*idx), 100, 50], text=item[3])) # writing the rows in

    while True: # Beginning a loop for the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit() # Quitting the window
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for button in lButtons:
                    if button.getHasFunc():
                        button.callFunc(mouse) # Calling button functions
        
        window.fill(COLOURS[COLOUR_SCHEME[0]['background']])
        for x in lButtons: x.draw()
        for x in titleButtons: x.draw() # drawing all titles

        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(100, 100), pygame.math.Vector2(WIDTH-100, 100), 3) # top line for box
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(100, HEIGHT-100), pygame.math.Vector2(WIDTH-100, HEIGHT-100), 3) # bottom line for box
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(100, 100), pygame.math.Vector2(100, HEIGHT-100), 3) # left line for box
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(WIDTH-100, 100), pygame.math.Vector2(WIDTH-100, HEIGHT-100), 3) # right line for box

        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(430, 100), pygame.math.Vector2(430, HEIGHT-100), 3) # left hand divider
        pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(WIDTH-430, 100), pygame.math.Vector2(WIDTH-430, HEIGHT-100), 3) # right hand divider

        for i in range(8):
            pygame.draw.line(window, COLOURS[COLOUR_SCHEME[0]['lines']], pygame.math.Vector2(100, 150+(60*i)), pygame.math.Vector2(WIDTH-100, 150+(60*i)), 3) # center dividers

        pygame.display.flip()
        clock.tick(FPS)

def finishMenu(COLOUR_SCHEME, timeTaken, themeName): # Finish Menu Loop
    fButtons = []
    inputBoxes = []
    pygame.display.set_caption("Main Menu") # Settings the title of the game window

    timeMins = int(timeTaken // 60)
    timeSecs = int(timeTaken % 60) # parsing time into displayable format

    # creating buttons and boxes to display at the end

    fButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=mainMenu, geo=[WIDTH - 100, 0, 100, 50], text="Main Menu", params=[COLOUR_SCHEME])) # Adding a button to fall back to the main menu
    fButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['background']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[WIDTH / 4 - 315, HEIGHT / 4 + 75, WIDTH, HEIGHT / 3], text="Congratulations!", fontSize=175))
    fButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['text']], tColour=COLOURS[COLOUR_SCHEME[0]['background']], geo=[(WIDTH / 2) + 100, (HEIGHT / 2) + 200, 200, 75], text=f"Time: {timeMins}m:{timeSecs:02d}s", fontSize=20))
    fButtons.append(submitBtn := Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], geo=[(WIDTH / 2) - 50, HEIGHT - 50, 100, 50], text="Submit", fontSize=20, func=addToDatabase, params=[]))
    inputBoxes.append(nameBox := InputBox(geo=[(WIDTH / 2) - 300, (HEIGHT / 2) + 200, 200, 75], placeholderText="Enter Name", borderColour=COLOURS[COLOUR_SCHEME[0]['background']], borderThickness=0, colour=COLOURS[COLOUR_SCHEME[0]['text']], tColour=COLOURS[COLOUR_SCHEME[0]['background']])) # title input

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # allowing the user to quit the window
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for button in fButtons: 
                    if button.getHasFunc():
                        button.callFunc(mouse)
                for inputBox in inputBoxes: inputBox.focus(mouse, inputBoxes) # focusing input box
            if event.type == pygame.KEYDOWN:
                for inputBox in inputBoxes: inputBox.writeToText(event.unicode) # adding text to button

        username = nameBox.getText() # getting username
        submitBtn.setParams([username, f"{timeMins}:{timeSecs:02d}", themeName, COLOUR_SCHEME]) # setting paramaters
        
        window.fill(COLOURS[COLOUR_SCHEME[0]['background']]) # refreshing the screen
        for x in fButtons: x.draw() # drawing the buttons to screen
        for x in inputBoxes: x.draw()

        pygame.display.flip() # refreshing the display
        clock.tick(FPS)

def newTheme(COLOUR_SCHEME): # input for new theme menu thingy
    mButtons = [] # list for buttons on the screen
    inputBoxes = [] # list for input boxes on the screen
    themeTitle, themeBody = '', '' # declaring the theme title and body variables
    mButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=mainMenu, geo=[0, 0, 100, 50], text="Main Menu", params=[COLOUR_SCHEME])) # fallback button for main menu
    mButtons.append(submitButton := Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=submitTheme, geo=[WIDTH-100, HEIGHT-50, 100, 50], text="Submit Theme", params=[themeTitle, themeBody, COLOUR_SCHEME])) # adding a submit button

    inputBoxes.append(titleBox := InputBox(geo=[WIDTH / 2 - ((WIDTH / 1.5) / 2), 50, 200, 50], placeholderText="Title")) # title input
    inputBoxes.append(bodyBox := InputBox(geo=[WIDTH / 2 - ((WIDTH / 1.5) / 2), HEIGHT / 2 - ((HEIGHT / 1.5) / 2), WIDTH / 1.5, HEIGHT / 1.5], placeholderText="Please enter at least 5 words here, seperated by commas, no spaces in words")) # theme body input

    pygame.display.set_caption("New Theme Creation") # setting the game name to "New Theme Creation"

    while True: # creating a loop to display the buttons
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit() # Quitting the window
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for button in mButtons: 
                    if button.getHasFunc(): button.callFunc(mouse) # Calling button functions
                for inputBox in inputBoxes: inputBox.focus(mouse, inputBoxes)
            if event.type == pygame.KEYDOWN:
                for inputBox in inputBoxes: inputBox.writeToText(event.unicode) 
        
        window.fill(COLOURS[COLOUR_SCHEME[0]['background']]) # blanking the screen

        themeTitle = titleBox.getText() # re-setting the title to the current text
        themeBody = bodyBox.getText() # re-setting the body to the current text
        submitButton.setParams([themeTitle, themeBody, COLOUR_SCHEME]) # setting the parameters of the submission button

        for x in mButtons: x.draw() # Drawing the buttons
        for x in inputBoxes: x.draw() # drawing input boxes

        pygame.display.flip()
        clock.tick(FPS)

def themeChoice(COLOUR_SCHEME): # Theme Choice Menu Loop
    themeButtons = []
    themeButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=mainMenu, geo=[0, 0, 100, 50], text="Main Menu", params=[COLOUR_SCHEME])) # fallback button for main menu
    themeButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttons']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=newTheme, geo=[100, 0, 100, 50], text="New Theme", params=[COLOUR_SCHEME])) # new theme create menu button

    pygame.display.set_caption("Theme Selection") 

    with open('components/themes.json', 'r') as f: # loading themes file 
        themes = json.load(f)
    
    themeList = [] # creating a list to store the theme titles

    for x in themes.keys(): themeList.append(x) # appending theme names to a list
    themeNames = [x for x in themes.keys()]

    themeCounter = 0
    for idx, theme in enumerate(themeList):
        if themeCounter >= 13: # if there are more than 13 themes in the current column
            themeCounter = 0 # reset themeCounter
        themeButtons.append(Button(colour=COLOURS[COLOUR_SCHEME[0]['buttonsVar2']], tColour=COLOURS[COLOUR_SCHEME[0]['text']], func=wordsearchGen, geo=[(idx//13)*100, (themeCounter+1)*50, 100, 50], text=theme, params=[theme, themeNames[idx], COLOUR_SCHEME])) # creating buttons with theme names
        themeCounter += 1
        # here i am using counters and ifs to write the theme buttons across the screen so they dont go off

    while True: # creating a loop to display the buttons
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit() # Quitting the window
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for button in themeButtons:
                    if button.getHasFunc():
                        button.callFunc(mouse) # Calling button functions
        
        window.fill(COLOURS[COLOUR_SCHEME[0]['background']])
        for x in themeButtons: x.draw() # Drawing the buttons

        pygame.display.flip()   
        clock.tick(FPS)

def wordsearchGen(theme, themeName, COLOUR_SCHEME): # This generates the words for the grid, and the size of the grid
    with open("components/themes.json","r") as f:
        themes = json.load(f)
        data = themes[theme] # Assigning data to be the list of words within the theme.
    
    words = []
    wordsDisplay = []
    grid = []
    wordLocations = []
    cleanWordList = []
    gridSize = 0 # declaring variables for later use

    for _ in range(5): # Picking 5 random words
        wordIdx = random.randint(0, len(data)-1) # Getting a random index for a word
        backward = random.randint(0, 2) # Generating whether the word will be forwards or backwards
        cleanWordList.append(data[wordIdx])
        if backward <= 1:
            words.append(data[wordIdx]) # Appending the word index to the word list
        else:
            words.append(data[wordIdx][::-1]) # Appending the word index to the word list (backwards)

        wordsDisplay.append(data[wordIdx])
        data.pop(wordIdx) # Removing the word from the available list
    
    for idx, item in enumerate(words):
        words[idx] = item.upper() # setting the words to be capitalised
        gridSize = len(item) if len(item) > gridSize else gridSize # Changing the gridsize to the length of the longest word
    
    gridSize += 3 # increasing the size by 1
    
    for x in range(gridSize):
        grid.append([])
        for y in range(gridSize):
            grid[x].append(None) # generating the grid based on the size

    sWords = sorted(words, key=len, reverse=True) # sorting the words into length order

    for word in sWords:
        grid, singleWordLocation = searchGen(grid, word, sWords) # generating grid and word locations
        wordLocations.append(singleWordLocation) # adding word locations to list

    grid = fillGrid(grid) # filling the gaps in the grid

    return playMenu(grid, sWords, wordLocations, cleanWordList, themeName, COLOUR_SCHEME) # returning the grid, wordpositions, and a list of unchanged words to the playMenu function

def searchGen(grid, word, words, runs=0): # generating the wordsearch
    curRun = runs # getting the current runs
    wordLocation = [[], []]
    if curRun <= 100: # preventing program from recursing too much
        direction = random.choice([['vertical', 0],['horizontal', 1]]) # vertical, horizontal

        curRun += 1
        randomSpot = [
            # if the direction is horizontal generate random for size of grid for y,
            random.randint(0, len(grid) - 1) if direction[1] == 1 else random.randint(0, len(grid) - len(word) - 1),
            # if the direction is vertical generate random for size of grid for x,
            random.randint(0, len(grid) - 1) if direction[1] == 0 else random.randint(0, len(grid) - len(word) - 1),
        ]

        if direction[1] == 0: # vertical
            for idx, char in enumerate(word): # index of char in word and the char itself
                if grid[randomSpot[0] + idx][randomSpot[1]] != None: # if the spot isnt empty
                    return searchGen(grid, word, words, runs=curRun) # re-run the function
            for idx, char in enumerate(word): # writing the word to grid
                grid[randomSpot[0] + idx][randomSpot[1]] = char # setting grid spots
            wordLocation[0] = randomSpot # first char location = random spot
            wordLocation[1] = [randomSpot[0] + len(word)-1, randomSpot[1]] # last char location = random spot + length of word          
            
        elif direction[1] == 1: # horizontal
            for idx, char in enumerate(word):
                if grid[randomSpot[0]][randomSpot[1] + idx] != None:
                    return searchGen(grid, word, words, runs=curRun)
            for idx, char in enumerate(word):
                grid[randomSpot[0]][randomSpot[1] + idx] = char
            wordLocation[0] = randomSpot
            wordLocation[1] = [randomSpot[0], randomSpot[1] + len(word)-1] # same as above ^

    elif curRun > 100:
        gridSize = len(grid) - 1
        grid = []

        for x in range(gridSize):
            grid.append([])
            for y in range(gridSize): # resetting the grid
                grid[x].append(None)
        
        for word in words:
            grid = searchGen(grid, word, words) # restarting the function from plain if there are over 100 attempts
    
    return grid, wordLocation # return the wordLocation and the grid

def fillGrid(grid): # filling the grid with random letters after
    for idx, row in enumerate(grid): 
        for index, item in enumerate(row):
            if item == None:
                grid[idx][index] = string.ascii_uppercase[random.randint(0, len(string.ascii_uppercase) - 1)] # filling the grid with random characters
    
    return grid # returning the grid

def submitTheme(title, body, COLOUR_SCHEME):
    with open ('components/themes.json', 'r') as f:
        themes = json.load(f) # loading current themes from file
    
    body = body.replace(' ', '') # removing whitespace
    themes[title] = body.split(',') # splitting on commas

    with open ('components/themes.json', 'w') as f: 
        f.write(json.dumps(themes, indent=4)) # writing the new themes back to file

    return mainMenu(COLOUR_SCHEME)

def changeColourTheme(COLOUR_SCHEME):
    with open("components/settings.json", "r") as f:
        settings = json.load(f)
    SELECTED_THEME = settings['ColourTheme']

    with open("components/colourTheme.json", "r") as f:
        themes = json.load(f)

    themeNames = [x for x in themes.keys()]
    
    for idx, name in enumerate(themeNames): 
        if SELECTED_THEME == name:
            SELECTED_THEME = themeNames[idx+1 if idx+1 < len(themeNames) else 0] # changed theme changing function to improve flexibility
            break

    with open('components/settings.json', 'r') as f: 
        settings = json.load(f)

    settings['ColourTheme'] = SELECTED_THEME
    COLOUR_SCHEME = colThemes[SELECTED_THEME.lower()]

    with open('components/settings.json', 'w') as f:
        f.write(json.dumps(settings, indent=4)) # writing the new settings back to file

    return COLOUR_SCHEME
            
def addToDatabase(username, timeTaken, themeName, COLOUR_SCHEME):
    conn = sql.connect("components/database.db") # opening database
    cursor = conn.cursor() # creating a cursor to interact with the database

    cursor.execute("CREATE TABLE IF NOT EXISTS Players ( id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(20), themeName VARCHAR(40), time INTEGER ) ")
    # ^ creating a table if it isnt there with the values (username, themename, and time)

    cursor.execute(f"INSERT INTO Players(username, themeName, time) VALUES (?, ?, ?)", (username, themeName, timeTaken))
    # ^ inserting the current users information into the database

    conn.commit() # commiting the data
    conn.close() # closing the connection

    return mainMenu(COLOUR_SCHEME) # sending the user to the main menu

def wipeDB(COLOUR_SCHEME):
    conn = sql.connect('components/database.db') # connecting to the database 
    cursor = conn.cursor() # creating a cursor to interact with the data
    cursor.execute("DROP TABLE Players") # dropping the player table to wipe it clean
    cursor.execute("CREATE TABLE IF NOT EXISTS Players ( id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(20), themeName VARCHAR(40), time INTEGER ) ") # re-creating the player table
    conn.commit() # commiting changes
    conn.close() # closing the connection

    return leaderboardMenu(COLOUR_SCHEME) # refreshing the screen

if __name__ == "__main__":
    with open("components/settings.json", "r") as f:
        settings = json.load(f)
    SELECTED_THEME = settings['ColourTheme'] # loading the colour theme
    
    with open("components/colourTheme.json", "r") as f:
        colThemes = json.load(f)

    COLOUR_THEME = [colThemes[SELECTED_THEME.lower()]]
    
    COLOURS = {
        "WHITE": (255, 255, 255),
        "BLACK": (0, 0, 0),
        "BLUE": (0, 100, 255),
        "DARK_BLUE": (0, 0, 120),
        "GREEN": (0, 255, 0),
        "DARK_GREEN": (0, 120, 0),
        "RED": (255, 50, 50),
        "DARK_RED": (120, 0, 0),
        "YELLOW": (255, 255, 0),
        "DARK_GRAY": (25, 25, 25),
        "PASTEL_RED": (255, 173, 173),
        "PASTEL_ORANGE": (255, 214, 165),
        "PASTEL_YELLOW": (253, 255, 182),
        "PASTEL_GREEN": (202, 255, 191),
        "PASTEL_BLUE": (155, 246, 255), 
        "PASTEL_PURPLE": (189, 178, 255),
        "PASTEL_PINK": (255, 198, 255)
    } # declaring colours

    WIDTH, HEIGHT = 1280, 720
    FPS = 60
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    mainMenu(COLOUR_THEME)
