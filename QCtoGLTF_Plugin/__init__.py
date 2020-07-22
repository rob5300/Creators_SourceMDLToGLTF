bl_info = {
    "name": "QC Convert",
    "category": "Import",
    "blender": (2, 80, 0),
    "author": "Robert Straub (robertstraub.co.uk)",
    "version": (0, 0, 1),
    "location": "File > Import",
    "description": "",
}

import bpy
import os
import re
import json
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from datetime import datetime

imagesPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source VTF\PNG"
images = None
vmtsPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source VMT"
vmts = None
outputPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\Output"
qcPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source MDL\QC"

classNames = ["demo", "engineer", "heavy", "medic", "pyro", "scout", "sniper", "soldier", "spy"]

data = {}

currentQCdata = {}

param1 = "___$color2"
param2 = "$colortint_base"
blendParam = "$blendtintcoloroverbase"
blendEnabledParam = "$blendtintbybasealpha"

blendtintbybasealpha = ""
blendtintcoloroverbase = ""
colortint_base = ""

num_regex = "([^_, ,\D][0-9]{1,3})"
blendtintcolour_regex = r'"([0-9.]+)\"'

def ReadQC(context, filePath):
    global currentQCdata
    global data
    print("Reading QC " + filePath)

    #Manage sorting multi class cosmetics into their specific folders
    baseQCName = os.path.splitext(os.path.basename(filePath))[0]
    exportPath = ""
    for x in range(0, len(classNames)):
        newName = baseQCName.replace("_" + classNames[x], "")
        if(newName != baseQCName):
            candidateFolder = os.path.join(outputPath, classNames[x])
            if(not os.path.exists(candidateFolder)):
                os.mkdir(candidateFolder)

            exportPath = os.path.join(outputPath, classNames[x], newName + ".glb")
            break

    if(exportPath == ""):
        # If the planned export path exists already just skip this model.
        exportPath = os.path.join(outputPath, baseQCName + ".glb")

    if(os.path.exists(exportPath)):
        return

    bpy.ops.import_scene.smd(filepath = filePath)

    bpy.ops.object.select_all(action="DESELECT")

    for ob in bpy.context.scene.objects:
        if(("lod" in ob.name and "lod_1" not in ob.name) or ("VTA" in ob.name)):
            ob.select_set(True)
            bpy.ops.object.delete()

        elif("skeleton" in ob.name):
            currentQCdata["skeleton"] = ob.name

    currentQCdata["materials"] = {}
    for ob in bpy.context.scene.objects:
        for mat_slot in ob.material_slots:
            if(mat_slot.material != None):
                matImage = FindImageWithName(mat_slot.material.name, "color")

                #Texture not found, we need to search the vmt for its real name
                if(matImage == None):
                    matImage = GetMainTextureNameFromVMT(mat_slot.material.name)

                if(matImage != ""):
                    if(not matImage.endswith(".png") and not matImage.endswith(".jpg")):
                        matImage += ".png"

                    SetupMaterial(mat_slot.material, os.path.join(imagesPath, matImage))

    bpy.ops.export_scene.gltf(export_format='GLB', export_image_format='JPEG', export_animations=False, filepath=exportPath)
    
    data[baseQCName] = currentQCdata
    currentQCdata = {}

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    return

def FindImageWithName(name, suffix):
    global images #Stupid
    if(images == None):
        images = os.listdir(imagesPath)

    for file in images:
        fname = os.path.splitext(os.path.basename(file))[0]
        if(fname == name or fname == f"{name}_{suffix}"):
            return os.path.join(imagesPath, file)

    return None

def FindVMTWithName(name):
    global vmts #Stupid
    if(vmts == None):
        vmts = os.listdir(vmtsPath)
    
    if("{name}.vmt" in vmts):
        return os.path.join(vmtsPath, "{name}.vmt")
    elif("{name}_color.vmt" in vmts):
        return os.path.join(vmtsPath, "{name}_color.vmt")

    return ""

def GetMainTextureNameFromVMT(vmtName):
    joinedPath = os.path.join(vmtsPath, vmtName + ".vmt")
    if(os.path.exists(joinedPath)):
        vmt = open(os.path.join(vmtsPath, vmtName + ".vmt"), mode="r")
        vmt_text = vmt.readlines()

        for line in vmt_text:
            if("$basetexture" in line):
                splitLine = line.split('"')
                for i in range(0, len(splitLine)):
                    if("/" in splitLine[i]):
                        pathSplit = splitLine[i].split("/")
                        return pathSplit[len(pathSplit) - 1]
    else:
        return ""
        
def SetupMaterial(material, mainTex):
    material.use_nodes = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    principled = nodes["Principled BSDF"]

    #Good all round roughness for most things.
    principled.inputs["Roughness"].default_value = 0.8

    #Base texture node
    tex_node = nodes.new(type="ShaderNodeTexImage")
    if(mainTex != None):
        tex_node.image = getCyclesImage(mainTex)
        links.new(tex_node.outputs["Color"], principled.inputs[0])

    #Find vmt for this material. If there is a color in this, output it and also try to produce a mask image for this materials main texture.
    GetVMTInfo(os.path.join(vmtsPath, material.name + ".vmt"))
    currentQCdata["materials"][material.name] = {}
    thisMaterialData = currentQCdata["materials"][material.name]

    if(blendtintbybasealpha != None and (float(blendtintbybasealpha) == 1.0 or float(blendtintbybasealpha) == 1)):
        #We have a material that should require a mask. Lets make one
        thisMaterialData["colourMask"] = f"{material.name}_mask"
        thisMaterialData["additive"] = (blendtintcoloroverbase != None and float(blendtintcoloroverbase) > 0)
        thisMaterialData["colourtint_base"] = colortint_base
        CreateMaskTexture(getCyclesImage(mainTex), f"{material.name}_mask")

def CreateMaskTexture(image, name):
    targetPath = os.path.join(outputPath, "Masks")

    if(not os.path.exists(targetPath)):
        os.mkdir(targetPath)

    # Don't make a mask when it exists already.
    targetPath = os.path.join(targetPath, name + ".png")
    if(not os.path.exists(targetPath)):
        mask = bpy.data.images.new(image.name + "_ColourMask", image.size[0], image.size[1], alpha=True, is_data=True)
        channels = mask.channels

        i = channels - 1
        maskpixels = list(mask.pixels)
        imagepixels = image.pixels[:]
        for i in range(channels - 1, len(maskpixels), channels):
            alpha = imagepixels[i]

            for x in range(i - (channels - 1), i):
                maskpixels[x] = alpha

            maskpixels[i] = 1


        mask.pixels[:] = maskpixels
        mask.update()
        mask.save_render(targetPath)

class ConvertQCs(Operator):
    """Import fbx props using a .vmf"""
    bl_idname = "qc_convert.import_qc"
    bl_label = "Convert QC"
    
    def execute(self, context):
        subdirs = os.listdir(qcPath)

        for p in subdirs:
            FindQCs(os.path.join(qcPath, p), context)

        now = datetime.now()

        dt_string = now.strftime("%d-%m-%Y_%H-%M")
        dataPath = os.path.join(outputPath, f"data_{dt_string}.json")

        jsonfile = open(dataPath, "w+")
        jsonfile.write(json.dumps(data))
        jsonfile.close()
        return {'FINISHED'}

def FindQCs(path, context):
    if(os.path.isdir(path)):
        subdirs = os.listdir(path)
        for f in subdirs:
            FindQCs(os.path.join(path,f), context)
    elif(path.endswith(".qc")):
        ReadQC(context, path)

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ConvertQCs.bl_idname, text="Convert QCs")

def register():
    bpy.utils.register_class(ConvertQCs)
    bpy.types.TOPBAR_MT_file.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ConvertQCs)
    bpy.types.TOPBAR_MT_file.remove(menu_func_import)

def getCyclesImage(imgpath):
    """Avoid reloading an image that has already been loaded"""
    for img in bpy.data.images:
        if os.path.abspath(img.filepath) == os.path.abspath(imgpath):
            return img
    return bpy.data.images.load(imgpath)

def GetVMTInfo(vmt_path):
    filehandle = open(vmt_path, mode='r')
    file_text = filehandle.readlines()

    global blendtintcoloroverbase
    blendtintcoloroverbase = None

    global blendtintbybasealpha
    blendtintbybasealpha = None

    global colortint_base
    colortint_base = None

    for line in file_text:
        if param1 in line or param2 in line:
            if "255 255 255" not in line and "{" in line and "}" in line and "resultVar" not in line and "srcVar" not in line:
                colortint_base = GetHexColour(line)
        elif blendParam in line:
            result = re.findall(blendtintcolour_regex, line)
            if(result != None and len(result) > 0):
                blendtintcoloroverbase = result[0].replace('"', "")
        elif blendEnabledParam in line:
            result_b = re.findall(blendtintcolour_regex, line)
            if(result_b != None and len(result_b) > 0):
                blendtintbybasealpha = result_b[0].replace('"', "")

def GetHexColour(line):
    toreturn = ""
    result = re.findall(num_regex, line)
    for r in result:
        toreturn += hex(int(r)).replace("0x", "")

    return toreturn

if __name__ == "__main__":
    register()