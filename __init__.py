#addon info
bl_info = {
    "name": "stella_tools",
    "author": "Jonas Dichelle",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Toolbar",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

import bpy
from .ops import PropagateAnimationOperator, ResolveCollisionsAnimOperator, Objects_To_Convex_Hull
from .ui import MONC_Properties, MONC

operator_classes = {
    MONC_Properties,
    PropagateAnimationOperator,
    ResolveCollisionsAnimOperator,
    MONC,
    Objects_To_Convex_Hull
}

# Register classes
def register():
    for cls in operator_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MONC_Properties)

def unregister():
    for cls in operator_classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()