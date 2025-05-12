import numpy as np
import moderngl as mgl
import glm
from geometry import *
from objects import *

class Engine:
    def __init__(self, renderer):
        self.renderer = renderer

        self.window = self.renderer.window
        self.ctx = self.renderer.ctx
        
        self._init_shaders()

        self.objects = [] # to cleanup

        self.checkboard = CheckerboardPlane(
            self.ctx, self.programs['checkerboard'], width = 100.0, depth = 100.0
        )
        self.objects.append(self.checkboard)

    def update(self):
        # 1 frame update
        pass

    def render(self):
        view_mat = self.renderer.camera.get_view_matrix()
        proj_mat = self.renderer.camera.get_projection_matrix()
        view_pos = self.renderer.camera.position

        for shader in self.programs.values():
            shader['view'].write(view_mat)
            shader['projection'].write(proj_mat)
            shader['view_pos'].write(view_pos)
        
        self.checkboard.render()
    
    def cleanup(self):
        for shader in self.programs.values():
            shader.release()

        for obj in self.objects:
            obj.cleanup()
        

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
    
    