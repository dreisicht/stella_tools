import bpy
import bmesh

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
