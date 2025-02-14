bl_info = {
    "name": "notester32's Bone Tool",
    "description": "Tool for adjusting bones in Blender 3",
    "author": "notester32",
    "version": (1, 8),
    "blender": (3, 6, 0),
    "category": "Rigging",
}

import bpy

class AdjustBonesOperator(bpy.types.Operator):
    """Adjusts the head or tail of the selected bones"""
    bl_idname = "armature.adjust_bones"
    bl_label = "Apply Adjustment"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT':
            selected_bones = bpy.context.selected_editable_bones

            if len(selected_bones) != 2:
                self.report({'WARNING'}, "You must select exactly 2 bones.")
                return {'CANCELLED'}

            first_bone, target_bone = selected_bones
            self.apply_adjustment(first_bone, target_bone, context)

            return {'FINISHED'}

        self.report({'WARNING'}, "You must be in Edit Mode with an armature selected.")
        return {'CANCELLED'}

    def apply_adjustment(self, first_bone, target_bone, context):
        mode = context.scene.adjust_bones_mode
        reconnect = context.scene.adjust_bones_reconnect

        if mode == "head_to_tail":
            target_bone.head = first_bone.tail
        elif mode == "tail_to_head":
            target_bone.tail = first_bone.head
        elif mode == "head_to_head":
            target_bone.head = first_bone.head
        elif mode == "tail_to_tail":
            target_bone.tail = first_bone.tail

        if reconnect:
            target_bone.use_connect = True
        else:
            target_bone.use_connect = False

class ApplyAllBonesOperator(bpy.types.Operator):
    """Applies the adjustment to all bones in the armature"""
    bl_idname = "armature.apply_all_bones"
    bl_label = "Apply to All Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT':
            armature = obj.data

            for bone in armature.edit_bones:
                children = bone.children
                if len(children) == 1:  # Only apply to bones with exactly one direct child
                    self.apply_adjustment(bone, children[0], context)

            return {'FINISHED'}

        self.report({'WARNING'}, "You must be in Edit Mode with an armature selected.")
        return {'CANCELLED'}

    def apply_adjustment(self, first_bone, target_bone, context):
        mode = context.scene.adjust_bones_mode
        reconnect = context.scene.adjust_bones_reconnect

        if mode == "head_to_tail":
            target_bone.head = first_bone.tail
        elif mode == "tail_to_head":
            target_bone.tail = first_bone.head
        elif mode == "head_to_head":
            target_bone.head = first_bone.head
        elif mode == "tail_to_tail":
            target_bone.tail = first_bone.tail

        if reconnect:
            target_bone.use_connect = True
        else:
            target_bone.use_connect = False

class ApplyAllBonesFromBoneOperator(bpy.types.Operator):
    """Applies adjustments to all descendant bones from the selected bone"""
    bl_idname = "armature.apply_all_bones_from_bone"
    bl_label = "Apply From Selected Bone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.object
        if obj and obj.type == 'ARMATURE' and obj.mode == 'EDIT':
            selected_bones = bpy.context.selected_editable_bones

            if len(selected_bones) != 1:
                self.report({'WARNING'}, "Select exactly one bone as the starting point.")
                return {'CANCELLED'}

            root_bone = selected_bones[0]
            self.apply_recursive(root_bone, context)

            return {'FINISHED'}

        self.report({'WARNING'}, "You must be in Edit Mode with an armature selected.")
        return {'CANCELLED'}

    def apply_recursive(self, bone, context):
        for child in bone.children:
            self.apply_adjustment(bone, child, context)
            self.apply_recursive(child, context)  # Apply recursively

    def apply_adjustment(self, first_bone, target_bone, context):
        mode = context.scene.adjust_bones_mode
        reconnect = context.scene.adjust_bones_reconnect

        if mode == "head_to_tail":
            target_bone.head = first_bone.tail
        elif mode == "tail_to_head":
            target_bone.tail = first_bone.head
        elif mode == "head_to_head":
            target_bone.head = first_bone.head
        elif mode == "tail_to_tail":
            target_bone.tail = first_bone.tail

        if reconnect:
            target_bone.use_connect = True
        else:
            target_bone.use_connect = False

class BoneToolPanel(bpy.types.Panel):
    bl_label = "notester32's Bone Tool"
    bl_idname = "VIEW3D_PT_bone_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bone Tools"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select 2 bones and apply adjustments:")

        layout.prop(context.scene, "adjust_bones_mode", text="Mode")
        layout.prop(context.scene, "adjust_bones_reconnect", text="Reconnect")
        
        layout.operator("armature.adjust_bones", text="Apply Adjustment")
        layout.separator()
        layout.operator("armature.apply_all_bones", text="Apply to All Bones")
        layout.operator("armature.apply_all_bones_from_bone", text="Apply From Selected Bone")

def register():
    bpy.utils.register_class(AdjustBonesOperator)
    bpy.utils.register_class(ApplyAllBonesOperator)
    bpy.utils.register_class(ApplyAllBonesFromBoneOperator)
    bpy.utils.register_class(BoneToolPanel)
    bpy.types.Scene.adjust_bones_mode = bpy.props.EnumProperty(
        name="Adjustment Mode",
        description="Choose which part of the bone to move",
        items=[
            ("head_to_tail", "Head → Tail", "Move the head of the Target Bone to the tail of the First Bone"),
            ("tail_to_head", "Tail → Head", "Move the tail of the Target Bone to the head of the First Bone"),
            ("head_to_head", "Head → Head", "Move the head of the Target Bone to the head of the First Bone"),
            ("tail_to_tail", "Tail → Tail", "Move the tail of the Target Bone to the tail of the First Bone"),
        ],
        default="head_to_tail"
    )
    bpy.types.Scene.adjust_bones_reconnect = bpy.props.BoolProperty(
        name="Reconnect",
        description="Reconnect the bone after adjustment",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(AdjustBonesOperator)
    bpy.utils.unregister_class(ApplyAllBonesOperator)
    bpy.utils.unregister_class(ApplyAllBonesFromBoneOperator)
    bpy.utils.unregister_class(BoneToolPanel)
    del bpy.types.Scene.adjust_bones_mode
    del bpy.types.Scene.adjust_bones_reconnect

if __name__ == "__main__":
    register()
