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

imagesPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source VTF\PNG"
images = None
vmtsPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source VMT"
vmts = None
outputPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\Output"
qcPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source MDL\QC"

logfilename = r"cosmeticdata.json"
data = {}

param1 = "___$color2"
param2 = "$colortint_base"

num_regex = "([^_, ,\D][0-9]{1,3})"
            
def ReadQC(filePath):
    bpy.ops.import_scene.smd(filepath = filePath)

    bpy.ops.object.select_all(action="DESELECT")

    for ob in bpy.context.scene.objects:
        if(("lod" in ob.name and "lod_1" not in ob.name) or ("VTA" in ob.name)):
            ob.select_set(True)
            bpy.ops.object.delete()

        elif("skeleton" in ob.name):
            data[os.path.basename(filePath)] = ob.name

    for ob in bpy.context.scene.objects:
        for mat_slot in ob.material_slots:
            if(mat_slot.material != None):
                matImage = FindImageWithName(mat_slot.material.name, "color")

                #Texture not found, we need to search the vmt for its real name
                if(matImage == None):
                    matImage = GetMainTextureNameFromVMT(mat_slot.material.name)

                SetupMaterial(mat_slot.material, os.path.join(imagesPath, matImage + ".png"))

    bpy.ops.export_scene.gltf(export_format='GLB', export_image_format='JPEG', export_animations=False, filepath=os.path.join(outputPath, os.path.splitext(os.path.basename(filePath))[0] + ".glb"))
    bpy.ops.wm.read_homefile(use_empty=True)
    return

def FindImageWithName(name, suffix):
    global images #Stupid
    if(images == None):
        images = os.listdir(imagesPath)

    for file in images:
        fname = os.path.splitext(os.path.basename(file))[0]
        if(fname == name or fname == "{name}_{suffix}"):
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
    vmt = open(os.path.join(vmtsPath, vmtName + ".vmt"), mode="r")
    vmt_text = vmt.readlines()

    for line in vmt_text:
        if("$basetexture" in line):
            splitLine = line.split('"')
            for i in range(0, len(splitLine)):
                if("/" in splitLine[i]):
                    pathSplit = splitLine[i].split("/")
                    return pathSplit[len(pathSplit) - 1]
        
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
    color = GetHexFromVMT(os.path.join(vmtsPath, material.name + ".vmt"))
    if(color != ""):
        #We have a material that should require a mask. Lets make one
        CreateMaskTexture(getCyclesImage(mainTex), os.path.join(outputPath, f"{material.name}_mask"))

def CreateMaskTexture(image, destination):
    mask = image.copy()
    mask.name = image.name + "_ColourMask"
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
    mask.save_render(destination + ".png")

class ConvertQCs(Operator):
    """Import fbx props using a .vmf"""
    bl_idname = "qc_convert.import_qc"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Convert QCs"

    def execute(self, context):
        subdirs = os.listdir(qcPath)

        for p in subdirs:
            FindQCs(os.path.join(qcPath, p))

        jsonfile = open(f"{outputPath}/data.json", "w+")
        jsonfile.write(json.dumps(data))
        jsonfile.close()
        return {'FINISHED'}

def FindQCs(path):
    if(os.path.isdir(path)):
        subdirs = os.listdir(path)
        for f in subdirs:
            FindQCs(os.path.join(path,f))
    elif(path.endswith(".qc")):
        ReadQC(path)

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

def GetHexFromVMT(vmt_path):
    filehandle = open(vmt_path, mode='r')
    file_text = filehandle.readlines()

    for line in file_text:
        if param1 in line or param2 in line:
            if "255 255 255" not in line and "{" in line and "}" in line and "resultVar" not in line and "srcVar" not in line:
                hex = GetHexColour(line)

def GetHexColour(line):
    toreturn = ""
    result = re.findall(num_regex, line)
    for r in result:
        toreturn += hex(int(r)).replace("0x", "")

    return toreturn

if __name__ == "__main__":
    register()