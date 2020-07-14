import shutil
import os
import re
import json

target_path = r"D:\TF2 Stuff\ModelPreview\tf2 assets\AllMaterials-Source VMT"
logfilename = r"vmtcoloursoutput"

param1 = "___$color2"
param2 = "$colortint_base"

num_regex = "([^_, ,\D][0-9]{1,3})"

logOutput = ""
jsonOutput = {}

def LogToFile():
    global logOutput
    files = os.listdir(target_path)
    printed_tag = False
    for file in files:
        printed_tag = False
        print("Checking " + file)
        filehandle = open(target_path + "\\" + file, mode='r')
        file_text = filehandle.readlines()

        for line in file_text:
            if param1 in line or param2 in line:
                if "255 255 255" not in line and "{" in line and "}" in line and "resultVar" not in line and "srcVar" not in line:
                    printed_tag = TryTag(printed_tag, file)
                    logOutput += line
                    hex = GetHexColour(line)
                    logOutput += f"RGB Hex: {hex}\n"
                    AddToJSON(os.path.basename(file), hex)
        
        if printed_tag:
            logOutput += "\n"

        filehandle.close()

    if(logOutput != ""):
        WriteFile()
    if(jsonOutput != {}):
        WriteJSON()
    print("Done!")

def GetHexColour(line):
    toreturn = ""
    result = re.findall(num_regex, line)
    for r in result:
        toreturn += hex(int(r)).replace("0x", "")

    return toreturn

def WriteFile():
    print("Writing file")
    logfile = open(f"{os.path.dirname(__file__)}\\{logfilename}.txt", "w+")
    logfile.write(logOutput)
    logfile.close()

def TryTag(printed_tag, file):
    global logOutput
    if not printed_tag:
        logOutput += os.path.basename(file) + "\n"
        return True
    else:
        return False

def AddToJSON(vmt, colour):
    vmt = vmt.replace(".vmt", "")
    jsonOutput[vmt] = colour;

def WriteJSON():
    print("Writing json file")
    jsonfile = open(f"{os.path.dirname(__file__)}\\{logfilename}.json", "w+")
    jsonfile.write(json.dumps(jsonOutput))
    jsonfile.close()

if __name__ == "__main__":
    LogToFile()