import numpy as np
import moderngl as mgl
import glm
import bvh_utils
from camera import Camera, CameraMode
from geometry import *
from objects import *

class Engine:
    def __init__(self, renderer):
        self.renderer = renderer

        self.window = self.renderer.window
        self.camera = self.renderer.camera
        self.ctx = self.renderer.ctx

        self.ui = None
        
        self._init_shaders()

        self.checkboard = CheckerboardPlane(
            self.ctx, self.programs['checkerboard'], width = 100.0, depth = 100.0
        )

        self.skeleton_color = (0.1, 0.1, 0.9)

        self.is_playing = False

        self.frame_time = None
        self.curr_frame = 0
        self.num_frames = 1
        self.skeletons = None

        self.bvh_parents = None
        self.bvh_positions = None
        self.bvh_rotations = None
        self.bvh_order = None

        self._init_bvh()

    def update(self):
        if self.is_playing:
            self.curr_frame = (self.curr_frame + 1) % self.num_frames

            self._update_skeletons(self.bvh_parents, self.bvh_positions[self.curr_frame], self.bvh_rotations[self.curr_frame], self.bvh_order)
            
            if self.camera.mode == CameraMode.ORBIT:
                self.camera.set_target(self.bvh_positions[self.curr_frame][0])

    def render(self):
        view_mat = self.renderer.camera.get_view_matrix()
        proj_mat = self.renderer.camera.get_projection_matrix()
        view_pos = self.renderer.camera.position

        for shader in self.programs.values():
            shader['view'].write(view_mat)
            shader['projection'].write(proj_mat)
            shader['view_pos'].write(view_pos)
        
        self.checkboard.render()

        if self.skeletons:
            for skeleton in self.skeletons:
                skeleton.render()
    
    def cleanup(self):
        for shader in self.programs.values():
            shader.release()

        self.checkboard.cleanup()

        if self.skeletons:
            for skeleton in self.skeletons:
                skeleton.cleanup()
    
    def _change_speed(self, speed):
        self.renderer.set_frame_time(self.frame_time / speed)
        
    def _init_bvh(self, filename = 'test.bvh'):
        if self.skeletons:
            for skeleton in self.skeletons:
                skeleton.cleanup()
        
        self.skeletons = []
        
        bvh_data = bvh_utils.load(filename)
        # cm -> m
        self.bvh_parents = bvh_data['parents']
        self.bvh_positions = bvh_data['positions'] / 100.0
        self.bvh_rotations = bvh_data['rotations']
        self.bvh_order = bvh_data['order']

        self.frame_time = bvh_data['frame_time']
        self.renderer.set_frame_time(self.frame_time)
        self.num_frames = bvh_data['positions'].shape[0]
        self.curr_frame = 0

        self.is_playing = False

        self._change_speed(1.0)

        self._init_skeletons(self.bvh_parents, self.bvh_positions[0], self.bvh_rotations[0], self.bvh_order)

        if self.camera.mode == CameraMode.ORBIT:
            self.camera.set_target(self.bvh_positions[0][0])
    
    def _init_skeletons(self, parents, positions, rotations, order):
        global_positions = []
        global_rotations = []
        for i, parent in enumerate(parents):
            if parent == -1:
                global_positions.append(glm.vec3(positions[i]))
                global_rotations.append(self._quat_from_euler(rotations[i], order))
            else:
                par_pos = global_positions[parent]
                par_quat = global_rotations[parent]
                pos = par_pos + par_quat * glm.vec3(positions[i])
                quat = par_quat * self._quat_from_euler(rotations[i], order)
                global_positions.append(pos)
                global_rotations.append(quat)

                origin = (par_pos + pos) / 2
                x_axis = glm.normalize(pos - par_pos)
                z_axis = glm.normalize(glm.cross(x_axis, par_quat * glm.vec3(0, 1.0, 0)))
                y_axis = glm.normalize(glm.cross(z_axis, x_axis))
                model = glm.mat4(glm.vec4(x_axis, 0), glm.vec4(y_axis, 0), glm.vec4(z_axis, 0), glm.vec4(origin, 1.0))
                
                vertices, colors, normals, indices = create_cuboid(glm.length(pos - par_pos), 0.08, 0.08, self.skeleton_color)
                skeleton = PhongObject(self.ctx, self.programs['phong'], vertices, colors, normals, indices)
                skeleton.update(model)
                self.skeletons.append(skeleton)

    def _update_skeletons(self, parents, positions, rotations, order):
        global_positions = []
        global_rotations = []
        for i, parent in enumerate(parents):
            if parent == -1:
                global_positions.append(glm.vec3(positions[i]))
                global_rotations.append(self._quat_from_euler(rotations[i], order))
            else:
                par_pos = global_positions[parent]
                par_quat = global_rotations[parent]
                pos = par_pos + par_quat * glm.vec3(positions[i])
                quat = par_quat * self._quat_from_euler(rotations[i], order)
                global_positions.append(pos)
                global_rotations.append(quat)

                origin = (par_pos + pos) / 2
                x_axis = glm.normalize(pos - par_pos)
                z_axis = glm.normalize(glm.cross(x_axis, par_quat * glm.vec3(0, 1.0, 0)))
                y_axis = glm.normalize(glm.cross(z_axis, x_axis))
                model = glm.mat4(glm.vec4(x_axis, 0), glm.vec4(y_axis, 0), glm.vec4(z_axis, 0), glm.vec4(origin, 1.0))
                
                self.skeletons[i - 1].update(model)

    def _quat_from_euler(self, angles, order):
        rad_angles = [glm.radians(angle) for angle in angles]
        
        axis_map = {
            'x': glm.vec3(1.0, 0.0, 0.0),
            'y': glm.vec3(0.0, 1.0, 0.0),
            'z': glm.vec3(0.0, 0.0, 1.0)
        }

        q = glm.quat()

        for i, axis in enumerate(order):
            axis_quat = glm.angleAxis(rad_angles[i], axis_map[axis])
            q = q * axis_quat

        return q
            

    def _read_glsl_file(self, shader_path):
        with open(shader_path, 'r') as shader_file:
            shader_code = shader_file.read()
            return shader_code

    def _init_shaders(self):
        self.programs = {
            'checkerboard': self.ctx.program(
                self._read_glsl_file('./shader/checkerboard_vert_shader.glsl'),
                self._read_glsl_file('./shader/checkerboard_frag_shader.glsl')
            ),
            'phong': self.ctx.program(
                self._read_glsl_file('./shader/phong_vert_shader.glsl'),
                self._read_glsl_file('./shader/phong_frag_shader.glsl')
            )
        }

        # # 광원 설정
        # for shader in self.programs.values():
        #     shader['light_pos'].write(glm.vec3(0.0, 10.0, 0.0))
        #     shader['light_color'].write(glm.vec3(1.0, 1.0, 1.0))

        # # 재질 속성 변경
        # self.programs['phong']['ambient_strength'].value = 0.1
        # self.programs['phong']['specular_strength'].value = 0.3
        # self.programs['phong']['shininess'].value = 16.0
    
    