import bpy
from bpy.types import Operator
from .propagate_anim import propagate_animation
from .resolve_collision import resolve_collisions_anim
from .convex_decimate import backup_and_convex_hull

class Objects_To_Convex_Hull(Operator):
    bl_idname = "wm.objects_to_convex_hull"
    bl_label = "Objects To Convex Hull"
    bl_description = "Converts selected objects to convex hulls"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_face_count = context.scene.my_tool.target_face_count

        #get objects from collision collection
        objects = context.scene.my_tool.collision_objects.all_objects
        
        backup_and_convex_hull(objects, target_face_count)
        return {'FINISHED'}

# Define the operators
class PropagateAnimationOperator(Operator):
    bl_idname = "wm.propagate_animation"
    bl_label = "Propagate Animation"

    def execute(self, context):
        props = context.scene.my_tool
        # Assuming propagate_animation function is defined elsewhere

        collision_objects = props.collision_objects.all_objects
        #animation objects are collision objects with animation data with an action
        source_animation_objects = [obj for obj in collision_objects if obj.animation_data and obj.animation_data.action]

        propagate_animation(source_animation_objects, collision_objects, lift_off_frame=props.lift_off_frame, random_offset=props.random_offset, scale_influence=props.scale_influence)
        return {'FINISHED'}

class ResolveCollisionsAnimOperator(Operator):
    bl_idname = "wm.resolve_collisions_anim"
    bl_label = "Resolve Collisions Animation"

    def execute(self, context):
        props = context.scene.my_tool
        # Assuming resolve_collisions_anim function is defined elsewhere
        resolve_collisions_anim(props.collision_objects, props.start_frame, props.end_frame, adjust_future_frames=props.adjust_future_frames, max_iterations=props.max_iterations, decay_frames=props.decay_frames, adjustment_distance=props.adjustment_distance)
        return {'FINISHED'}