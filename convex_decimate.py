import bpy

def parent_set(child, parent):
    # Store the world space matrix
    original_matrix = child.matrix_world.copy()
    # Set parent
    child.parent = parent
    # Reset the child's transform to its original world space transform
    child.matrix_world = original_matrix

def copy_animation_data(original, copy):
    if original.animation_data:
        # Copy animation data block to the copy
        copy.animation_data_clear()
        copy.animation_data_create()
        copy.animation_data.action = original.animation_data.action
        original.animation_data_clear()

def create_backup_collection():
    backup_collection = bpy.data.collections.new("Backup Objects")
    bpy.context.scene.collection.children.link(backup_collection)
    backup_collection.hide_render = True
    backup_collection.hide_viewport = True
    for view_layer in bpy.context.scene.view_layers:
        view_layer.layer_collection.children[backup_collection.name].exclude = True
    return backup_collection

def duplicate_to_collection(obj, target_collection):
    new_obj = obj.copy()
    if obj.data:
        new_obj.data = obj.data.copy()
    target_collection.objects.link(new_obj)
    return new_obj

def decimate_to_face_count(obj, target_face_count):
    # Ensure the object is a mesh
    if obj.type != 'MESH':
        print("Selected object is not a mesh")
        return

    # Calculate and apply decimation
    current_face_count = len(obj.data.polygons)
    if current_face_count > target_face_count:
        decimate_ratio = target_face_count / current_face_count
        decimate_modifier = obj.modifiers.new(name="DecimateMod", type='DECIMATE')
        decimate_modifier.ratio = decimate_ratio

        # Apply the modifier
        context = bpy.context
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        mesh_from_eval = bpy.data.meshes.new_from_object(obj_eval)
        obj.modifiers.clear()
        obj.data = mesh_from_eval

def apply_convex_hull(obj):
    # Ensure we're dealing with a mesh object
    if obj.type != 'MESH':
        print("Selected object is not a mesh")
        return

    # Apply convex hull
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.convex_hull()
    bpy.ops.object.mode_set(mode='OBJECT')

def decimate_and_convex_hull(obj, target_face_count, iterations=2):
    for _ in range(iterations):
        decimate_to_face_count(obj, target_face_count)
    apply_convex_hull(obj)

def copy_object(obj, new_collection):
    # Create a new mesh data block, copying the original mesh
    new_mesh = obj.data.copy()
    new_mesh.name =  obj.data.name + "_convex_hull"

    # Create a new object linked to the new mesh
    new_obj = bpy.data.objects.new(obj.name + "_convex_hull", new_mesh)

    # Copy transformation
    new_obj.location = obj.location.copy()
    new_obj.rotation_euler = obj.rotation_euler.copy()
    new_obj.scale = obj.scale.copy()

    # Link new object to the collection
    new_collection.objects.link(new_obj)

    return new_obj

def backup_and_convex_hull(objects, target_face_count):
    # Create backup collection and copy originals
    backup_collection = create_backup_collection()
    for obj in objects:
        duplicate_to_collection(obj, backup_collection)
    # Create a new collection for modified objects
    new_collection = bpy.data.collections.new("Convex Hull Objects")
    bpy.context.scene.collection.children.link(new_collection)

    for original in objects:
        # Ensure the object is a mesh
        if original.type != 'MESH':
            continue
        # Copy the object
        copy = copy_object(original, new_collection)
        # Apply the process to the copy
        decimate_and_convex_hull(copy, target_face_count)
        # Copy animation data from the original to the copy
        copy_animation_data(original, copy)
        # Parent the original to the copy with world matrix adjustment
        parent_set(original, copy)
    