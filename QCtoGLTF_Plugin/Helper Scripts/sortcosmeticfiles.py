import shutil
import os
import sys

here = os.path.dirname(__file__)

class SortingSet:
    targetFolder = ""
    matches = []

    def __init__(self, targetFolder, matches):
        self.targetFolder = targetFolder
        self.matches = matches

sortingSets = [
    SortingSet("_SourceMDL", [".vtx", ".mdl", ".vtx", ".vvd"]),
    SortingSet("_SourceVMT", [".vmt"]),
    SortingSet("_SourceVTF", [".vtf"]),
]

def SortFiles(toSearch):
    for file in os.listdir(toSearch):
        fullpath = os.path.join(toSearch, file)

        if(os.path.isfile(fullpath)):
            MoveFile(fullpath)
        elif(os.path.isdir(fullpath) and "backpack" not in fullpath):
            print(f"Searching subdir '{file}'")
            SortFiles(fullpath)

def MoveFile(path):
    for sortingSet in sortingSets:
        for match in sortingSet.matches:
            if match in path:
                basename = os.path.basename(path)
                newPath = os.path.join(here, sortingSet.targetFolder, basename)
                print(f"Moving {basename} to {newPath}")
                shutil.move(path, newPath)
                return

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        patharg = sys.argv[1].replace(".", "").replace("\\", "").replace("\"", "") #Fix powershell bullshit
        arg = os.path.join(here, patharg)
        if arg != here and here in arg:
            print(f"Starting search in '{arg}'")
            SortFiles(arg)
        else:
            print(f"Error, tried to run in bad dir: {arg} .")
    else:
        print("Error, no folder specified.")
        exit(1)
