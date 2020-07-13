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

imagesPath = "D:\\TF2 Stuff\\ModelPreview\\tf2 assets\\All Source VTF\\PNG"
            
def ReadFile(context, filepath):

    bpy.ops.import_scene.smd(filepath = filepath)

    bpy.ops.object.select_all(action="DESELECT")

    for ob in bpy.context.scene.objects:
         if("lod" in ob.name and "lod_1" not in ob.name):
            ob.select_set(True)
            bpy.ops.object.delete()

    for ob in bpy.context.scene.objects:
        for mat_slot in ob.material_slots:
            if(mat_slot.material != None):
                SetupMaterial(mat_slot.material, FindImageWithName(ob.active_material.name, "color"))

    bpy.ops.export_scene.gltf()
    
    return {'FINISHED'}

def FindImageWithName(name, suffix):
    files = os.listdir(imagesPath)

    for file in files:
        fname = os.path.splitext(os.path.basename(file))[0]
        if(fname == name or fname == "{name}_{suffix}"):
            return os.path.join(imagesPath, file)

    return None

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

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ImportSomeData(Operator, ImportHelper):
    """Import fbx props using a .vmf"""
    bl_idname = "import_vmf.import_props"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Convert QC"

    # ImportHelper mixin class uses this
    filename_ext = ".qc"

    filter_glob: StringProperty(
        default="*.qc",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return ReadFile(context, self.filepath)


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


if __name__ == "__main__":
    register()