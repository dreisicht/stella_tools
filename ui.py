import bpy
from bpy.props import PointerProperty, IntProperty, FloatProperty, BoolProperty

class MONC_Properties(bpy.types.PropertyGroup):
    target_face_count: bpy.props.IntProperty(name="Target Face Count", default=150)

    start_frame: IntProperty(name="Start Frame", default=1)
    end_frame: IntProperty(name="End Frame", default=180)
    lift_off_frame: IntProperty(name="Lift Off Frame", default=82)
    random_offset: IntProperty(name="Random Offset", default=10)
    scale_influence: FloatProperty(name="Scale Influence", default=1.0)
    adjust_future_frames: BoolProperty(name="Adjust Future Frames", default=True)

    decay_frames: IntProperty(name="Decay Frames", default=100)
    max_iterations: IntProperty(name="Max Iterations", default=10)
    adjustment_distance: FloatProperty(name="Adjustment Distance", default=0.05)
    
    source_animation_objects: PointerProperty(
        name="Keyed Objects",
        type=bpy.types.Collection
    )
    collision_objects: PointerProperty(
        name="Destination Objects",
        type=bpy.types.Collection
    )

class MONC(bpy.types.Panel):
    bl_label = "Many Objects, No Collision"
    bl_idname = "PT_MONC"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        my_tool = scene.my_tool

        box = layout.box()
        box.label(text="Collision Objects")
        box.prop(my_tool, "target_face_count")
        box.operator("wm.objects_to_convex_hull", icon="MOD_ARRAY")
        
        # Collection selectors
        # layout.prop_search(my_tool, "source_animation_objects", bpy.data, "collections")
        layout.prop_search(my_tool, "collision_objects", bpy.data, "collections")

        box = layout.box()

        box.label(text="Animation Propagation")

        box.prop(my_tool, "lift_off_frame")
        box.prop(my_tool, "random_offset")
        box.prop(my_tool, "scale_influence")
        
        box.operator("wm.propagate_animation", icon="MOD_ARRAY")
        
        box = layout.box()
        
        box.label(text="Collision Resolution")
        
        row = box.row(align=True)
        row.prop(my_tool, "start_frame")
        row.prop(my_tool, "end_frame")

        box.prop(my_tool, "decay_frames")
        box.prop(my_tool, "max_iterations")
        box.prop(my_tool, "adjustment_distance")
    
        box.prop(my_tool, "adjust_future_frames")
    
        box.operator("wm.resolve_collisions_anim", icon="SELECT_INTERSECT")