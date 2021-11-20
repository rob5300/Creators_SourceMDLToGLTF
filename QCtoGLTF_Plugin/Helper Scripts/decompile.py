import shutil
import os
import sys

here = os.path.dirname(__file__)
mdlSource = os.path.join(here, "_SourceMDL")
qcTarget = os.path.join(mdlSource, "QC")
vtfSource = os.path.join(here, "_SourceVTF\\*.vtf")
pngTarget = os.path.join(here, "_SourceVTF\\PNG")

def DecompileMDL():
    print("Decompiling all MDL files...")
    # Decompile all models
    for file in os.listdir(mdlSource):
        if "mdl" in file:
            os.system(f".\CrowbarCommandLineDecomp.exe -p \"{os.path.join(mdlSource, file)}\" -o \"{os.path.join(qcTarget, file)}\"")

    print("Moving results out of subfolders")
    # Move the decompiled models out of their folders
    for file in os.listdir(qcTarget):
        fullpath = os.path.join(qcTarget, file)
        if ".mdl" in file and os.path.isdir(fullpath):

            for innerFile in os.listdir(fullpath):

                fullpath2 = os.path.join(fullpath, innerFile)
                # Move out sub files only, not folders.
                if os.path.isfile(fullpath2):

                    newPath = os.path.join(qcTarget, innerFile)
                    print(f"Moving {innerFile}")

                    if os.path.exists(newPath):
                        os.remove(newPath)

                    shutil.move(fullpath2, newPath)

def ConvertVTF():
    print("Convert all vtf files to png")
    if not os.path.exists(pngTarget):
        os.mkdir(pngTarget)

    # Finally, use vtfcmd to convert all vtf -> png
    vtfcmdcmd = f".\\vtflib\\vtfcmd.exe -folder \"{vtfSource}\" -output \"{pngTarget}\" -exportformat \"png\""
    print(vtfcmdcmd)
    os.system(vtfcmdcmd)

# Do all decompile steps, or some specified one.
if len(sys.argv) > 1:
    if "mdl" in sys.argv:
        DecompileMDL()
    if "vtf" in sys.argv:
        ConvertVTF()

else:
    DecompileMDL()
    ConvertVTF()

print("DONE")

