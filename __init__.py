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
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

imagesPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source VTF\PNG"
images = None
vmtsPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\All Source VMT"
vmts = None
outputPath = r"D:\TF2 Stuff\ModelPreview\tf2 assets\Output"

logfilename = r"vmtcoloursoutput"

param1 = "___$color2"
param2 = "$colortint_base"

num_regex = "([^_, ,\D][0-9]{1,3})"
            
def ReadQC(context, filepath):
    bpy.ops.import_scene.smd(filepath = filepath)

    bpy.ops.object.select_all(action="DESELECT")

    for ob in bpy.context.scene.objects:
         if(("lod" in ob.name and "lod_1" not in ob.name) or ("VTA" in ob.name)):
            ob.select_set(True)
            bpy.ops.object.delete()

    for ob in bpy.context.scene.objects:
        for mat_slot in ob.material_slots:
            if(mat_slot.material != None):
                matImage = FindImageWithName(mat_slot.material.name, "color")

                #Texture not found, we need to search the vmt for its real name
                if(matImage == None):
                    matImage = GetMainTextureNameFromVMT(mat_slot.material.name)

                SetupMaterial(mat_slot.material, FindImageWithName(matImage, "color"))

    #bpy.ops.export_scene.gltf()
    
    return {'FINISHED'}

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
        CreateMaskTexture(getCyclesImage(mainTex), os.path.join(outputPath, "{material.name}_mask"))

def CreateMaskTexture(image, destination):
    mask = image.copy()
    mask.name = image.name + "_ColourMask"
    channels = image.channels
    size = image.size[0]*image.size[1]

    i = channels - 1
    while(i < size):
        alpha = image.pixels[i]

        for x in range(i - channels - 1, channels - 1):
            mask.pixels[x] = alpha

        i = i + channels

    mask.save_render(destination)

class ImportSomeData(Operator, ImportHelper):
    """Import fbx props using a .vmf"""
    bl_idname = "qc_convert.import_qc"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Convert QC"

    # ImportHelper mixin class uses this
    filename_ext = ".qc"

    filter_glob: StringProperty(
        default="*.qc",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return ReadQC(context, self.filepath)

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Convert QC")

def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

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