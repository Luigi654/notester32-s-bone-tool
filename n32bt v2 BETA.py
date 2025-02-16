bl_info = {
    "name": "notester32's Bone Tool - BETA",
    "author": "notester32 & AI Assistant",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "category": "Rigging",
    "description": "Advanced bone alignment and manipulation tools",
}

import bpy
from mathutils import Vector

# ==============================================
# MAIN OPERATOR (WITH HEAD->HEAD AND TAIL->TAIL)
# ==============================================

class BONE_OT_SmartAlign(bpy.types.Operator):
    """Smart bone alignment with active controls"""
    bl_idname = "bone.smart_align"
    bl_label = "Smart Aligner"
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[
            ('A_TO_B', "First → Second", "Selection order"),
            ('B_TO_A', "Second → First", "Reverse order"),
            ('ACTIVE', "Active → Others", "Based on active bone"),
        ],
        default='A_TO_B'
    )

    mode: bpy.props.EnumProperty(
        name="Type",
        items=[
            ('HEAD_TAIL', "Head → Tail", "Align target's head to source's tail"),
            ('TAIL_HEAD', "Tail → Head", "Align target's tail to source's head"),
            ('HEAD_HEAD', "Head → Head", "Align target's head to source's head"),
            ('TAIL_TAIL', "Tail → Tail", "Align target's tail to source's tail"),
            ('FULL', "Full Alignment", "Align both ends"),
        ],
        default='HEAD_TAIL'
    )

    reconnect: bpy.props.BoolProperty(
        name="Reconnect Bones",
        description="Automatically reconnect bones after alignment",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (
            context.object and 
            context.object.type == 'ARMATURE' and 
            context.mode == 'EDIT_ARMATURE'
        )

    def execute(self, context):
        selected_bones = context.selected_editable_bones
        active_bone = context.active_bone

        # Determine source and target
        if self.direction == 'A_TO_B':
            if len(selected_bones) < 2:
                self.report({'ERROR'}, "Select at least 2 bones for this mode")
                return {'CANCELLED'}
            source, target = selected_bones[0], selected_bones[1]
        elif self.direction == 'B_TO_A':
            if len(selected_bones) < 2:
                self.report({'ERROR'}, "Select at least 2 bones for this mode")
                return {'CANCELLED'}
            source, target = selected_bones[1], selected_bones[0]
        elif self.direction == 'ACTIVE':
            if not active_bone or len(selected_bones) < 2:
                self.report({'ERROR'}, "Select 1 active bone + at least 1 target")
                return {'CANCELLED'}
            source = active_bone
            targets = [b for b in selected_bones if b != source]
        else:
            return {'CANCELLED'}

        # Apply transformation
        if self.direction == 'ACTIVE':
            for t in targets:
                self.apply_alignment(source, t)
        else:
            self.apply_alignment(source, target)

        return {'FINISHED'}

    def apply_alignment(self, source, target):
        if self.mode == 'HEAD_TAIL':
            target.head = source.tail
        elif self.mode == 'TAIL_HEAD':
            target.tail = source.head
        elif self.mode == 'HEAD_HEAD':
            target.head = source.head
        elif self.mode == 'TAIL_TAIL':
            target.tail = source.tail
        elif self.mode == 'FULL':
            delta = source.tail - source.head
            target.head = source.tail
            target.tail = source.tail + delta

        # Reconnect bones if enabled
        if self.reconnect:
            target.use_connect = True

# ==============================================
# APPLY ALL BONES OPERATOR (WITH HEAD->HEAD AND TAIL->TAIL)
# ==============================================

class BONE_OT_ApplyAllBones(bpy.types.Operator):
    """Apply alignment to all bones in the armature"""
    bl_idname = "bone.apply_all_bones"
    bl_label = "Apply All Bones"
    bl_options = {'REGISTER', 'UNDO'}

    apply_all_mode: bpy.props.EnumProperty(
        name="Apply Mode",
        items=[
            ('FIRST', "First", "Start alignment from the root bone"),
            ('LAST', "Last", "Start alignment from the last bone in the chain"),
        ],
        default='FIRST'
    )

    apply_all_align_mode: bpy.props.EnumProperty(
        name="Alignment Mode",
        items=[
            ('HEAD_TAIL', "Head → Tail", "Align head to tail"),
            ('TAIL_HEAD', "Tail → Head", "Align tail to head"),
            ('HEAD_HEAD', "Head → Head", "Align head to head"),
            ('TAIL_TAIL', "Tail → Tail", "Align tail to tail"),
            ('FULL', "Full Alignment", "Align both ends"),
        ],
        default='HEAD_TAIL'
    )

    apply_all_reconnect: bpy.props.BoolProperty(
        name="Reconnect Bones",
        description="Automatically reconnect bones after alignment",
        default=False
    )

    apply_all_ignore_children: bpy.props.BoolProperty(
        name="Ignore Extra Children",
        description="If a bone has more than 2 children, align only the first child",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (
            context.object and 
            context.object.type == 'ARMATURE' and 
            context.mode == 'EDIT_ARMATURE'
        )

    def execute(self, context):
        armature = context.object.data
        bones = armature.edit_bones

        # Find root bones (bones without parents)
        root_bones = [b for b in bones if not b.parent]

        if not root_bones:
            self.report({'ERROR'}, "No root bones found in the armature")
            return {'CANCELLED'}

        # Apply alignment to all bones
        for root in root_bones:
            self.apply_recursive(root, self.apply_all_mode == 'LAST')

        return {'FINISHED'}

    def apply_recursive(self, bone, reverse=False):
        children = bone.children

        # Skip bones with more than 2 children (unless ignore_children is enabled)
        if len(children) > 2 and not self.apply_all_ignore_children:
            return

        # Apply alignment to children
        for child in children:
            if reverse:
                # Align from last bone
                self.apply_recursive(child, reverse)
                self.apply_alignment(bone, child)
            else:
                # Align from root bone
                self.apply_alignment(bone, child)
                self.apply_recursive(child, reverse)

        # If ignore_children is enabled, align only the first child
        if self.apply_all_ignore_children and len(children) > 2:
            self.apply_alignment(bone, children[0])

    def apply_alignment(self, source, target):
        if self.apply_all_align_mode == 'HEAD_TAIL':
            target.head = source.tail
        elif self.apply_all_align_mode == 'TAIL_HEAD':
            target.tail = source.head
        elif self.apply_all_align_mode == 'HEAD_HEAD':
            target.head = source.head
        elif self.apply_all_align_mode == 'TAIL_TAIL':
            target.tail = source.tail
        elif self.apply_all_align_mode == 'FULL':
            delta = source.tail - source.head
            target.head = source.tail
            target.tail = source.tail + delta

        # Reconnect bones if enabled
        if self.apply_all_reconnect:
            target.use_connect = True

# ==============================================
# APPLY FROM BONE OPERATOR (WITH HEAD->HEAD AND TAIL->TAIL)
# ==============================================

class BONE_OT_ApplyFromBone(bpy.types.Operator):
    """Apply alignment to all child bones starting from the selected bone"""
    bl_idname = "bone.apply_from_bone"
    bl_label = "Apply From Bone"
    bl_options = {'REGISTER', 'UNDO'}

    apply_from_mode: bpy.props.EnumProperty(
        name="Apply Mode",
        items=[
            ('FIRST', "First Bone", "Start alignment from the selected bone"),
            ('LAST', "Last Bone", "Start alignment from the last bone in the chain"),
        ],
        default='FIRST'
    )

    apply_from_align_mode: bpy.props.EnumProperty(
        name="Alignment Mode",
        items=[
            ('HEAD_TAIL', "Head → Tail", "Align head to tail"),
            ('TAIL_HEAD', "Tail → Head", "Align tail to head"),
            ('HEAD_HEAD', "Head → Head", "Align head to head"),
            ('TAIL_TAIL', "Tail → Tail", "Align tail to tail"),
            ('FULL', "Full Alignment", "Align both ends"),
        ],
        default='HEAD_TAIL'
    )

    apply_from_reconnect: bpy.props.BoolProperty(
        name="Reconnect Bones",
        description="Automatically reconnect bones after alignment",
        default=False
    )

    apply_from_ignore_children: bpy.props.BoolProperty(
        name="Ignore Extra Children",
        description="If a bone has more than 2 children, align only the first child",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (
            context.object and 
            context.object.type == 'ARMATURE' and 
            context.mode == 'EDIT_ARMATURE' and 
            len(context.selected_editable_bones) == 1
        )

    def execute(self, context):
        selected_bones = context.selected_editable_bones

        if len(selected_bones) != 1:
            self.report({'ERROR'}, "Select exactly 1 bone to start alignment")
            return {'CANCELLED'}

        start_bone = selected_bones[0]
        self.apply_recursive(start_bone, self.apply_from_mode == 'LAST')

        return {'FINISHED'}

    def apply_recursive(self, bone, reverse=False):
        children = bone.children

        # Skip bones with more than 2 children (unless ignore_children is enabled)
        if len(children) > 2 and not self.apply_from_ignore_children:
            return

        # Apply alignment to children
        for child in children:
            if reverse:
                # Align from last bone
                self.apply_recursive(child, reverse)
                self.apply_alignment(bone, child)
            else:
                # Align from root bone
                self.apply_alignment(bone, child)
                self.apply_recursive(child, reverse)

        # If ignore_children is enabled, align only the first child
        if self.apply_from_ignore_children and len(children) > 2:
            self.apply_alignment(bone, children[0])

    def apply_alignment(self, source, target):
        if self.apply_from_align_mode == 'HEAD_TAIL':
            target.head = source.tail
        elif self.apply_from_align_mode == 'TAIL_HEAD':
            target.tail = source.head
        elif self.apply_from_align_mode == 'HEAD_HEAD':
            target.head = source.head
        elif self.apply_from_align_mode == 'TAIL_TAIL':
            target.tail = source.tail
        elif self.apply_from_align_mode == 'FULL':
            delta = source.tail - source.head
            target.head = source.tail
            target.tail = source.tail + delta

        # Reconnect bones if enabled
        if self.apply_from_reconnect:
            target.use_connect = True

# ==============================================
# FIXED UI PANEL (WITH ALL MODES)
# ==============================================

class VIEW3D_PT_BoneAlignmentPanel(bpy.types.Panel):
    bl_label = "Bone Alignment Master"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigging"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Main settings
        box = layout.box()
        box.label(text="Main Settings", icon='TOOL_SETTINGS')
        
        row = box.row()
        row.prop(wm, "bone_align_direction", expand=True)
        
        box.separator()
        box.prop(wm, "bone_align_mode", text="Mode")
        box.prop(wm, "bone_align_reconnect", text="Reconnect Bones")

        # Execution button
        box.separator()
        box.operator("bone.smart_align", text="Run Alignment", icon='ARROW_LEFTRIGHT')

        # Apply All Bones section
        box = layout.box()
        box.label(text="Apply All Bones", icon='MOD_ARMATURE')
        
        box.prop(wm, "apply_all_mode", text="Apply Mode")
        box.prop(wm, "apply_all_align_mode", text="Alignment Mode")
        box.prop(wm, "apply_all_reconnect", text="Reconnect Bones")
        box.prop(wm, "apply_all_ignore_children", text="Ignore Extra Children")

        box.separator()
        box.operator("bone.apply_all_bones", text="Apply to All Bones", icon='BONE_DATA')

        # Apply From Bone section
        box = layout.box()
        box.label(text="Apply From Bone", icon='BONE_DATA')
        
        box.prop(wm, "apply_from_mode", text="Apply Mode")
        box.prop(wm, "apply_from_align_mode", text="Alignment Mode")
        box.prop(wm, "apply_from_reconnect", text="Reconnect Bones")
        box.prop(wm, "apply_from_ignore_children", text="Ignore Extra Children")

        box.separator()
        box.operator("bone.apply_from_bone", text="Apply From Selected Bone", icon='BONE_DATA')

# ==============================================
# GLOBAL PROPERTIES AND REGISTRATION
# ==============================================

classes = (
    BONE_OT_SmartAlign,
    BONE_OT_ApplyAllBones,
    BONE_OT_ApplyFromBone,
    VIEW3D_PT_BoneAlignmentPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Properties in window_manager for persistence
    bpy.types.WindowManager.bone_align_direction = bpy.props.EnumProperty(
        name="Direction",
        items=[
            ('A_TO_B', "First → Second", ""),
            ('B_TO_A', "Second → First", ""),
            ('ACTIVE', "Active → Others", ""),
        ],
        default='A_TO_B'
    )
    
    bpy.types.WindowManager.bone_align_mode = bpy.props.EnumProperty(
        name="Mode",
        items=[
            ('HEAD_TAIL', "Head → Tail", ""),
            ('TAIL_HEAD', "Tail → Head", ""),
            ('HEAD_HEAD', "Head → Head", ""),
            ('TAIL_TAIL', "Tail → Tail", ""),
            ('FULL', "Full Alignment", ""),
        ],
        default='HEAD_TAIL'
    )

    bpy.types.WindowManager.bone_align_reconnect = bpy.props.BoolProperty(
        name="Reconnect Bones",
        description="Automatically reconnect bones after alignment",
        default=False
    )

    bpy.types.WindowManager.apply_all_mode = bpy.props.EnumProperty(
        name="Apply Mode",
        items=[
            ('FIRST', "First", "Start alignment from the root bone"),
            ('LAST', "Last", "Start alignment from the last bone in the chain"),
        ],
        default='FIRST'
    )

    bpy.types.WindowManager.apply_all_align_mode = bpy.props.EnumProperty(
        name="Alignment Mode",
        items=[
            ('HEAD_TAIL', "Head → Tail", ""),
            ('TAIL_HEAD', "Tail → Head", ""),
            ('HEAD_HEAD', "Head → Head", ""),
            ('TAIL_TAIL', "Tail → Tail", ""),
            ('FULL', "Full Alignment", ""),
        ],
        default='HEAD_TAIL'
    )

    bpy.types.WindowManager.apply_all_reconnect = bpy.props.BoolProperty(
        name="Reconnect Bones",
        description="Automatically reconnect bones after alignment",
        default=False
    )

    bpy.types.WindowManager.apply_all_ignore_children = bpy.props.BoolProperty(
        name="Ignore Extra Children",
        description="If a bone has more than 2 children, align only the first child",
        default=False
    )

    bpy.types.WindowManager.apply_from_mode = bpy.props.EnumProperty(
        name="Apply Mode",
        items=[
            ('FIRST', "First Bone", "Start alignment from the selected bone"),
            ('LAST', "Last Bone", "Start alignment from the last bone in the chain"),
        ],
        default='FIRST'
    )

    bpy.types.WindowManager.apply_from_align_mode = bpy.props.EnumProperty(
        name="Alignment Mode",
        items=[
            ('HEAD_TAIL', "Head → Tail", ""),
            ('TAIL_HEAD', "Tail → Head", ""),
            ('HEAD_HEAD', "Head → Head", ""),
            ('TAIL_TAIL', "Tail → Tail", ""),
            ('FULL', "Full Alignment", ""),
        ],
        default='HEAD_TAIL'
    )

    bpy.types.WindowManager.apply_from_reconnect = bpy.props.BoolProperty(
        name="Reconnect Bones",
        description="Automatically reconnect bones after alignment",
        default=False
    )

    bpy.types.WindowManager.apply_from_ignore_children = bpy.props.BoolProperty(
        name="Ignore Extra Children",
        description="If a bone has more than 2 children, align only the first child",
        default=False
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.WindowManager.bone_align_direction
    del bpy.types.WindowManager.bone_align_mode
    del bpy.types.WindowManager.bone_align_reconnect
    del bpy.types.WindowManager.apply_all_mode
    del bpy.types.WindowManager.apply_all_align_mode
    del bpy.types.WindowManager.apply_all_reconnect
    del bpy.types.WindowManager.apply_all_ignore_children
    del bpy.types.WindowManager.apply_from_mode
    del bpy.types.WindowManager.apply_from_align_mode
    del bpy.types.WindowManager.apply_from_reconnect
    del bpy.types.WindowManager.apply_from_ignore_children

if __name__ == "__main__":
    register()