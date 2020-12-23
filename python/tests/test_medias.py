from brayns import Client
from braynsmediamaker import MovieMaker

brayns = Client('localhost:5000')
mm = MovieMaker(brayns)

control_points = [
    {
        'apertureRadius': 4.224657298716223e-290,
        'direction': [0.0, 0.0, -1.0],
        'focusDistance': 0.0,
        'origin': [0.5, 0.5, 1.5],
        'up': [0.0, 1.0, 0.0]
    },
    {
        'apertureRadius': 0.0,
        'direction': [-0.4823790279394327, -0.35103051457124496, -0.8025509648888691],
        'focusDistance': 0.0,
        'origin': [2.020997896788385, 1.606840561979088, 3.0305377285488593],
        'up': [-0.1993924108090585, 0.9361435664152715, -0.2896167978053891]
    }
]

mm.build_camera_path(
    control_points=control_points, nb_steps_between_control_points=50,
    smoothing_size=50)
print(mm.get_nb_frames())

mm.set_current_frame(10)
mm.create_movie(path='/tmp', size=[512, 512], samples_per_pixel=16, start_frame=10, end_frame=20, exportIntermediateFrames=False)

mm.set_current_frame(20)
mm.create_snapshot(path='/tmp/test_20.png', size=[512, 512], samples_per_pixel=16, exportIntermediateFrames=True)

mm.set_current_frame(30)
mm.create_snapshot(path='/tmp/test_30.png', size=[512, 512], samples_per_pixel=16, exportIntermediateFrames=False)