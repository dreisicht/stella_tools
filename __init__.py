import bpy
import bmesh
import random

def bmesh_copy_from_object(obj, transform=True, triangulate=True):
    assert(obj.type == 'MESH')

    me = obj.data
    if obj.mode == 'EDIT':
        bm_orig = bmesh.from_edit_mesh(me)
        bm = bm_orig.copy()
    else:
        bm = bmesh.new()
        bm.from_mesh(me)

    if transform:
        bm.transform(obj.matrix_world)
    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm

def bmesh_check_intersect_objects(obj, obj2):
    assert(obj != obj2)

    bm = bmesh_copy_from_object(obj, transform=True, triangulate=True)
    bm2 = bmesh_copy_from_object(obj2, transform=True, triangulate=True)

    if len(bm.edges) > len(bm2.edges):
        bm2, bm = bm, bm2

    me_tmp = bpy.data.meshes.new(name="~temp~")
    bm2.to_mesh(me_tmp)
    bm2.free()
    obj_tmp = bpy.data.objects.new(name=me_tmp.name, object_data=me_tmp)
    bpy.context.collection.objects.link(obj_tmp)
    ray_cast = obj_tmp.ray_cast

    intersect = False
    EPS_NORMAL = 0.000001
    EPS_CENTER = 0.01

    for ed in bm.edges:
        v1, v2 = ed.verts
        co_1 = v1.co.copy()
        co_2 = v2.co.copy()
        co_mid = (co_1 + co_2) * 0.5
        no_mid = (v1.normal + v2.normal).normalized() * EPS_NORMAL
        co_1 = co_1.lerp(co_mid, EPS_CENTER) + no_mid
        co_2 = co_2.lerp(co_mid, EPS_CENTER) + no_mid

        success, co, no, index = ray_cast(co_1, (co_2 - co_1).normalized(), distance = ed.calc_length())
        if index != -1:
            intersect = True
            break

    bpy.context.collection.objects.unlink(obj_tmp)
    bpy.data.objects.remove(obj_tmp)
    bpy.data.meshes.remove(me_tmp)
    bm.free()

    return intersect

def resolve_collisions(collection, max_iterations=20):
    iterations = 0
    while iterations < max_iterations:
        has_collision = False

        for obj1 in collection.all_objects:
            if obj1.type != 'MESH':
                continue

            for obj2 in collection.all_objects:
                if obj2.type != 'MESH' or obj1 == obj2:
                    continue

                if bmesh_check_intersect_objects(obj1, obj2):
                    print(f"Collision detected between {obj1.name} and {obj2.name}")
                    direction = (obj1.location - obj2.location).normalized()
                    obj1.location += direction * 0.1
                    has_collision = True

        if not has_collision:
            break

        iterations += 1

    print(f"Collision resolution completed in {iterations} iterations.")

def apply_delta_to_future_keyframes(obj, frame, delta, end_frame, decay_frames=100):
    if not obj.animation_data or not obj.animation_data.action:
        return

    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == 'location':
            for keyframe in fcurve.keyframe_points:
                if keyframe.co[0] > frame:
                    # Calculate decay factor based on distance from collision frame
                    frame_diff = keyframe.co[0] - frame
                    decay_factor = max(1.0 - frame_diff / decay_frames, 0)
                    # Apply decayed delta to the corresponding axis
                    keyframe.co[1] += delta[fcurve.array_index] * decay_factor
                    if keyframe.co[0] >= end_frame:
                        break  # Stop adjusting if we reach the end frame


def resolve_collisions_anim(collection, start_frame, end_frame, adjust_future_frames=False, max_iterations=5, decay_frames=100, adjustment_distance=0.1):
    for frame in range(start_frame, end_frame + 1):
        bpy.context.scene.frame_set(frame)
        iterations = 0

        while iterations < max_iterations:
            has_collision = False

            for obj1 in collection.all_objects[:]:
                if obj1.type != 'MESH':
                    continue

                for obj2 in collection.all_objects[:]:
                    if obj2.type != 'MESH' or obj1 == obj2:
                        continue

                    if bmesh_check_intersect_objects(obj1, obj2):
                        print(f"Collision detected between {obj1.name} and {obj2.name} at frame {frame}")

                        original_location = obj1.location.copy()

                        direction = (obj1.location - obj2.location).normalized()
                        obj1.location += direction * adjustment_distance
                        obj1.keyframe_insert(data_path="location", frame=frame)

                        for fcurve in obj1.animation_data.action.fcurves:
                            if fcurve.data_path == 'location':
                                for keyframe in fcurve.keyframe_points:
                                    if keyframe.co[0] == frame:
                                        keyframe.handle_left_type = 'VECTOR'
                                        keyframe.handle_right_type = 'VECTOR'
                                        break

                        if adjust_future_frames:
                            delta = obj1.location - original_location
                            apply_delta_to_future_keyframes(obj1, frame, delta, end_frame, decay_frames=decay_frames)

                        has_collision = True

            if not has_collision:
                break

            iterations += 1

    print(f"Collision resolution animation completed.") 

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

def propagate_animation(source_animation_coll, collision_coll, lift_off_frame=0, random_offset=0, scale_influence=1.0):
    for obj in collision_coll.all_objects:
        source_obj = random.choice(source_animation_coll.all_objects)
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

# Define the property group
class MONC_Properties(bpy.types.PropertyGroup):
    start_frame: bpy.props.IntProperty(name="Start Frame", default=1)
    end_frame: bpy.props.IntProperty(name="End Frame", default=180)
    lift_off_frame: bpy.props.IntProperty(name="Lift Off Frame", default=82)
    random_offset: bpy.props.IntProperty(name="Random Offset", default=10)
    scale_influence: bpy.props.FloatProperty(name="Scale Influence", default=1.0)
    adjust_future_frames: bpy.props.BoolProperty(name="Adjust Future Frames", default=True)

    decay_frames: bpy.props.IntProperty(name="Decay Frames", default=100)
    max_iterations: bpy.props.IntProperty(name="Max Iterations", default=10)
    adjustment_distance: bpy.props.FloatProperty(name="Adjustment Distance", default=0.05)
    
    source_animation_objects: bpy.props.PointerProperty(
        name="Keyed Objects",
        type=bpy.types.Collection
    )
    collision_objects: bpy.props.PointerProperty(
        name="Destination Objects",
        type=bpy.types.Collection
    )
    
# Define the operators
class PropagateAnimationOperator(bpy.types.Operator):
    bl_idname = "wm.propagate_animation"
    bl_label = "Propagate Animation"

    def execute(self, context):
        props = context.scene.my_tool
        # Assuming propagate_animation function is defined elsewhere
        propagate_animation(props.source_animation_objects, props.collision_objects, lift_off_frame=props.lift_off_frame, random_offset=props.random_offset, scale_influence=props.scale_influence)
        return {'FINISHED'}

class ResolveCollisionsAnimOperator(bpy.types.Operator):
    bl_idname = "wm.resolve_collisions_anim"
    bl_label = "Resolve Collisions Animation"

    def execute(self, context):
        props = context.scene.my_tool
        # Assuming resolve_collisions_anim function is defined elsewhere
        resolve_collisions_anim(props.collision_objects, props.start_frame, props.end_frame, adjust_future_frames=props.adjust_future_frames, max_iterations=props.max_iterations, decay_frames=props.decay_frames, adjustment_distance=props.adjustment_distance)
        return {'FINISHED'}

# Define the panel
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
        
        # Collection selectors
        layout.prop_search(my_tool, "source_animation_objects", bpy.data, "collections")
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

# Register classes
def register():
    bpy.utils.register_class(MONC_Properties)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MONC_Properties)
    bpy.utils.register_class(PropagateAnimationOperator)
    bpy.utils.register_class(ResolveCollisionsAnimOperator)
    bpy.utils.register_class(MONC)

def unregister():
    bpy.utils.unregister_class(MONC)
    bpy.utils.unregister_class(ResolveCollisionsAnimOperator)
    bpy.utils.unregister_class(PropagateAnimationOperator)
    bpy.utils.unregister_class(MONC_Properties)
    del bpy.types.Scene.my_tool

if __name__ == "__main__":
    register()