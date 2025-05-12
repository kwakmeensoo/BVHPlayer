from render import Renderer

if __name__ == '__main__':
    width = 1280
    height = 720

    renderer = Renderer(width, height, "BVH Player")

    renderer.run()