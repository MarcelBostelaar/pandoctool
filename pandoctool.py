import time

import os
from os.path import isfile, join, isdir
import traceback

allowedOutputs = ["html", "pdf", "docx"]
pollTime = 1
commandString = 'pandoc -s --toc --toc-depth=2 {original} -o "{output}"'
clearTheScreen = False


def clearScreen():
    if clearTheScreen:
        os.system("cls")  # clears screen
    else:
        pass


class Menu:
    def __init__(self):
        self.actions = {}
        self.choices = []

    def addChoice(self, name, f):
        self.actions[name] = f
        self.choices.append(name)

    def dialog(self, prePrint, error=False):
        clearScreen()
        print(prePrint)
        self.printOptions()
        if error:
            print("Wrong input, please write a number that is in the list")
        choice = input("Please choose an option\n")
        try:
            val = int(choice)
            self.actions[self.choices[val]]()
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.dialog(prePrint, True)

    def printOptions(self):
        for i in range(len(self.choices)):
            print(str(i) + ". " + self.choices[i])


def getHash(path):
    f = open(path, "rb")
    all = f.read()
    f.close()
    return hash(all)


def getManyHash(paths):
    return sum([getHash(x) for x in paths])


def command(fileToWatch, outputLocation):
    fixedInputs = " ".join(['"' + x + '"' for x in fileToWatch])
    os.system(commandString.format(original=fixedInputs, output=outputLocation))


def isMD(path):
    if not os.path.isfile(path):
        print("Not a path")
        return False
    return path[-3:] == ".md"


def isBookDef(path):
    if not os.path.isfile(path):
        return False
    return path[-8:] == ".bookdef"


def getCommand(mdFiles, outputFile):
    files = " ".join(mdFiles)
    return f'pandoc -s --toc "{files}" -o "{outputFile}"'


def buildAndVerifyCommand(inputFile, outputType):
    if isBookDef(inputFile):
        f = open(inputFile)
        lines = f.read().replace("\n", "\r").split("\r")
        f.close()
        origin = os.path.dirname(inputFile)
        lines = [os.path.join(origin, x) for x in lines if x != ""]
        for x in lines:
            if not isMD(x):
                raise Exception(f"Specified file is not an md file: {x}")
        input = lines
    elif isMD(inputFile):
        input = [inputFile]
    else:
        raise Exception("Input not a valid type")
    if outputType not in allowedOutputs:
        raise Exception("Invalid output type")
    return input, ".".join(inputFile.split(".")[:-1]) + "." + outputType


def defFileWatch(whattowatch: str, outputtype: str):
    defFileHash = getHash(whattowatch)
    inputs, outputFile = buildAndVerifyCommand(whattowatch, outputtype)
    command(inputs, outputFile)
    print("Updated!" + str(time.ctime()))
    oldHash = getManyHash(inputs)
    while True:
        if getHash(whattowatch) != defFileHash:
            inputs, outputFile = buildAndVerifyCommand(whattowatch, outputtype)

        newHash = getManyHash(inputs)
        if oldHash != newHash:
            command(inputs, outputFile)
            oldHash = getManyHash(inputs)
            print("Updated! - " + str(time.ctime()))
        time.sleep(pollTime)


def simpleWatch(whattowatch: str, outputtype: str):
    inputs, outputFile = buildAndVerifyCommand(whattowatch, outputtype)
    oldHash = getManyHash(inputs)
    command(inputs, outputFile)
    print("Updated!" + str(time.ctime()))
    while True:
        newHash = getManyHash(inputs)
        if oldHash != newHash:
            command(inputs, outputFile)
            oldHash = getManyHash(inputs)
            print("Updated! - " + str(time.ctime()))
        time.sleep(pollTime)


def getFiles(folder):
    items = [join(folder, f) for f in os.listdir(folder)]
    onlyfiles = [f for f in items if isBookDef(f) or isMD(f)]
    return onlyfiles


def getFolders(folder):
    items = [join(folder, f) for f in os.listdir(folder)]
    onlyFolders = [f for f in items if isdir(f)]
    return onlyFolders


def goUp(fromFolder, chosenAction, cancel, preprint):
    newFolder = join(fromFolder, "..")
    folderSelection(newFolder, chosenAction, cancel, preprint)


def folderSelection(folder, chosenAction, cancel, preprint):
    folder = os.path.normpath(folder)
    currentFolderText = "\nCurrent folder: "
    folders = getFolders(folder)
    items = getFiles(folder)
    folders.sort()
    items.sort()
    x = Menu()
    if len(folder) <= 3:
        x.addChoice("*Select drive", lambda: selectDrive(chosenAction, cancel, preprint))
    else:
        x.addChoice("*Folder up", lambda: goUp(folder, chosenAction, cancel, preprint))

    for i in folders:
        x.addChoice(os.path.split(i)[-1] + "\\", lambda i=i: folderSelection(i, chosenAction, cancel, preprint))

    for i in items:
        x.addChoice(os.path.split(i)[-1], lambda i=i: chosenAction(i))

    x.addChoice("*Cancel", cancel)
    x.dialog(preprint + currentFolderText + folder)


def selectFolder(action, message, cancelAction):
    currPath = os.path.dirname(os.path.realpath(__file__))
    folderSelection(currPath, action, cancelAction, message)


def combinator(simple, bookdef):
    def internal(file):
        if isBookDef(file):
            bookdef(file)
        else:
            simple(file)
    return internal


def selectDrive(chosenAction, cancel, preprint):
    drives = [ chr(x) + ":\\" for x in range(65,91) if os.path.exists(chr(x) + ":") ]
    print(drives)
    x = Menu()
    for i in drives:
        x.addChoice(i, lambda i=i: folderSelection(i, chosenAction, cancel, preprint))
    x.addChoice("*Cancel", cancel)
    x.dialog(preprint)


def buildChoice(filename, outputType):
    inputs, outputFile = buildAndVerifyCommand(filename, outputType)
    return command(inputs, outputFile)


def WatchBuildSelector(outputType):
    menu = Menu()
    menu.addChoice("Watch", lambda: selectFolder(
            combinator(
                lambda filename: simpleWatch(filename, outputType), 
                lambda filename: defFileWatch(filename, outputType)
                ), 
            "Please select a file to watch", 
            lambda: WatchBuildSelector(outputType)
            ))

    menu.addChoice("Build", lambda: selectFolder(
        lambda filename: buildChoice(filename, outputType), 
        "Please select a file to build", 
        lambda: WatchBuildSelector(outputType)
        ))
    menu.addChoice("Back", main)
    menu.dialog("Output type: " + outputType + "\nPlease choose a mode.")


def main():
    menu = Menu()
    menu.addChoice("HTML", lambda: WatchBuildSelector("html"))
    menu.addChoice("DOCX", lambda: WatchBuildSelector("docx"))
    menu.addChoice("*Exit", exit)
    menu.dialog("Please choose an output target")


if __name__ == "__main__":
    main()