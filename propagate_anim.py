import bpy
import random

def get_bounding_box_size(obj):
    return max(obj.dimensions)

def scale_and_offset_fcurve(fcurve, scale_factor, offset_value, lift_off_frame, x_offset):
    for keyframe in fcurve.keyframe_points:
        # Adjust x-coordinates relative to the lift_off_frame
        keyframe.co.x = (keyframe.co.x - lift_off_frame) * scale_factor + lift_off_frame
        keyframe.handle_left.x = (keyframe.handle_left.x - lift_off_frame) * scale_factor + lift_off_frame
        keyframe.handle_right.x = (keyframe.handle_right.x - lift_off_frame) * scale_factor + lift_off_frame

        # Offset y-coordinates
        keyframe.co.y += offset_value
        keyframe.handle_left.y += offset_value
        keyframe.handle_right.y += offset_value
        
        keyframe.co.x += x_offset
        keyframe.handle_left.x += x_offset
        keyframe.handle_right.x += x_offset

def apply_animation(src_action, dst_action, dst_world_matrix, scale_factor, lift_off_frame, random_offset):
    x_offset = random.randint(0, random_offset)
    
    for fcurve in src_action.fcurves:
        data_path = fcurve.data_path
        array_index = fcurve.array_index
        
        # Calculate theoretical fcurve value from world transform matrix
        # This part needs specific implementation based on the fcurve type
        if "location" in data_path:
            theoretical_value = dst_world_matrix.to_translation()[array_index]
        elif "rotation_euler" in data_path:
            theoretical_value = dst_world_matrix.to_euler()[array_index]
        elif "scale" in data_path:
            theoretical_value = dst_world_matrix.to_scale()[array_index]
        else:
            continue

        # Get value at current frame of fcurve
        current_frame = bpy.context.scene.frame_current
        current_value = fcurve.evaluate(current_frame)

        # Calculate difference and use as offset value
        offset_value = theoretical_value - current_value
        dst_fcurve = dst_action.fcurves.find(data_path, index=array_index)

        scale_and_offset_fcurve(dst_fcurve, scale_factor, offset_value, lift_off_frame, x_offset)

def propagate_animation(source_animation_objects, collision_objects, lift_off_frame=0, random_offset=0, scale_influence=1.0):
    for obj in collision_objects:
        source_obj = random.choice(source_animation_objects)
        active_size = get_bounding_box_size(source_obj)
        active_action = source_obj.animation_data.action
        
        if obj == source_obj:
            continue
        
        obj_world_matrix = obj.matrix_world.copy()
        new_action = active_action.copy()

        target_size = get_bounding_box_size(obj)
        base_scale_factor = target_size / active_size if active_size > 0 else 1
        # Adjust scale_factor based on scale_influence
        scale_factor = 1 + (base_scale_factor - 1) * scale_influence

        apply_animation(active_action, new_action, obj_world_matrix, scale_factor, lift_off_frame, random_offset)
        
        obj.animation_data.action = new_action