'''
MIT License

Copyright (C) 2025 odonata

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import bpy
from bpy.props import *
from bpy.app.handlers import persistent
from bpy.types import PropertyGroup, DATA_PT_bone_collections, Armature, Panel, Context, Bone, Pose, Header
from mathutils import *

bl_info = {
    "name": "Keying Bone Collection",
    "description": "Single Line Explanation",
    "author": "odonata",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D",
    "wiki_url": "https://odonata.xyz/",
    "category": "Animation" }
    

class BONECOLLECTION_GP_Keying(PropertyGroup):
    enabled: BoolProperty(name="Keying", default=False)
    
class SCENE_GP_Keying(bpy.types.PropertyGroup):
    autopin: BoolProperty(name="Auto Pin", description="選択ボーンコレクションを自動でピン", default=True)
    

    
operator_length = 0
@persistent
def add_key_handler(scene):
    global operator_length
    context = bpy.context
    tool_settings = context.tool_settings
    if not hasattr(context, "object") : return
    ob = context.object
    wm = context.window_manager
    operators = wm.operators

    if not ob or ob.mode != 'POSE' or not ob.animation_data or not ob.animation_data.action or not tool_settings.use_keyframe_insert_auto: return

    pose:Pose = ob.pose
    data:Armature = ob.data
    action = ob.animation_data.action

    selected_bones = [b for b in data.bones if b.select]
    keying_collections = [c for c in data.collections if c.keying_bone_collection.enabled]
    selected_collections = []
    for b in selected_bones :
        for col in b.collections:
            if col not in selected_collections and col.keying_bone_collection.enabled:
                selected_collections.append(col)

    if scene.keying_bone_collection.autopin :
        for col in keying_collections:
            if col.name not in action.groups: continue
            group = action.groups[col.name]
            group.use_pin = col in selected_collections

    if not len(operators) or len(operators) == operator_length : return
    last_op = operators[len(operators)-1]
    
    check_ops = [
        'TRANSFORM_OT_',
        'POSE_OT_',
        'ACTION_OT_',
        'ANIM_OT_',
    ]
    checked = False
    for check_op in check_ops:
       if last_op.bl_idname.startswith(check_op):
           checked = True
           break
    if not checked: return

    fcurves = action.fcurves
    frame_current = scene.frame_current

    insert_keys = ['location', 'rotation_euler', 'scale']
    for collection in selected_collections:
        col_bones = collection.bones
        for bone in col_bones :
            for f in fcurves:
                if not f.data_path.startswith('pose.bones["%s"]' % bone.name): continue
                for keyframe in f.keyframe_points:
                    if keyframe.co.x == frame_current :
                        for b in col_bones :
                            pb = pose.bones[b.name]
                            for insert_key in insert_keys:
                                pb.keyframe_insert(insert_key)
                        break
                break
    
    for fcurve in action.fcurves:
        
        if not fcurve.data_path.startswith('pose.bones["'): continue
        
        bone_name = fcurve.data_path[len('pose.bones["'):]
        bone_name = bone_name[:bone_name.index('"')]
        bone = data.bones.get(bone_name, None)
        if not bone: continue

        keying_collections = [col for col in bone.collections if col.keying_bone_collection.enabled]
        if len(keying_collections) != 1: continue

        col = keying_collections[0]
        group = action.groups.get(col.name) or action.groups.new(col.name)
        if fcurve.group != group:
            fcurve.group = group

    print("keying!", last_op.bl_idname)
    operator_length = len(operators)

def _bonecol_draw(self:Panel, context:Context):
    layout = self.layout
    arm = context.armature
    active_bcoll = arm.collections.active
    if not active_bcoll: return
    layout.prop(active_bcoll.keying_bone_collection, "enabled", icon="FCURVE")

def _dopesheet_draw(self:Header, context:Context):
    layout = self.layout
    layout.prop(context.scene.keying_bone_collection, "autopin")

def register():
    bpy.utils.register_class(BONECOLLECTION_GP_Keying)
    bpy.utils.register_class(SCENE_GP_Keying)
    bpy.app.handlers.depsgraph_update_post.append(add_key_handler)
    bpy.types.BoneCollection.keying_bone_collection = PointerProperty(type = BONECOLLECTION_GP_Keying)
    bpy.types.Scene.keying_bone_collection = PointerProperty(type = SCENE_GP_Keying)
    bpy.types.DOPESHEET_HT_header.append(_dopesheet_draw)
    DATA_PT_bone_collections.prepend(_bonecol_draw)

def unregister():
    bpy.utils.unregister_class(BONECOLLECTION_GP_Keying)
    bpy.utils.unregister_class(SCENE_GP_Keying)
    bpy.app.handlers.depsgraph_update_post.remove(add_key_handler)
    bpy.types.DOPESHEET_HT_header.remove(_dopesheet_draw)
    DATA_PT_bone_collections.remove(_bonecol_draw)
    del bpy.types.BoneCollection.keying_bone_collection
    del bpy.types.Scene.keying_bone_collection

if __name__ == '__main__':
    register()