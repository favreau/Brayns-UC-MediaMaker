#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, EPFL/Blue Brain Project
# All rights reserved. Do not distribute without permission.
# Responsible Author: Cyrille Favreau <cyrille.favreau@epfl.ch>
#
# This file is part of Brayns-UC-MediaMaker
# <https://github.com/favreau/Brayns-UC-MediaMaker>
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3.0 as published
# by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# All rights reserved. Do not distribute without further notice.

"""Provides a class that ease the definition of smoothed camera paths"""

from brayns import Client
from IPython.display import display

class MovieMaker:
    """ Movie maker """

    PLUGIN_API_PREFIX = 'mm_'

    def __init__(self, brayns):
        assert isinstance(brayns, Client)
        self._client = brayns
        self._smoothed_key_frames = list()

    def build_camera_path(self, control_points, nb_steps_between_control_points, smoothing_size=1):
        """
        Build a camera path from control points

        @param control_points: List of control points
        @param nb_steps_between_control_points: Number of steps between two control points
        @param smoothing_size: Number of steps to be considered for the smoothing of the path
        """
        origins = list()
        directions = list()
        ups = list()
        aperture_radii = list()
        focus_distances = list()
        self._smoothed_key_frames.clear()

        for s in range(len(control_points) - 1):

            p0 = control_points[s]
            p1 = control_points[s + 1]

            for i in range(nb_steps_between_control_points):
                origin = [0, 0, 0]
                direction = [0, 0, 0]
                up = [0, 0, 0]

                t_origin = [0, 0, 0]
                t_direction = [0, 0, 0]
                t_up = [0, 0, 0]
                for k in range(3):
                    t_origin[k] = (p1['origin'][k] - p0['origin'][k]) / float(nb_steps_between_control_points)
                    t_direction[k] = (p1['direction'][k] - p0['direction'][k]) / float(nb_steps_between_control_points)
                    t_up[k] = (p1['up'][k] - p0['up'][k]) / float(nb_steps_between_control_points)

                    origin[k] = p0['origin'][k] + t_origin[k] * float(i)
                    direction[k] = p0['direction'][k] + t_direction[k] * float(i)
                    up[k] = p0['up'][k] + t_up[k] * float(i)

                t_aperture_radius = (p1['apertureRadius'] - p0['apertureRadius']) / float(
                    nb_steps_between_control_points)
                aperture_radius = p0['apertureRadius'] + t_aperture_radius * float(i)

                t_focus_distance = (p1['focusDistance'] - p0['focusDistance']) / float(nb_steps_between_control_points)
                focus_distance = p0['focusDistance'] + t_focus_distance * float(i)

                origins.append(origin)
                directions.append(direction)
                ups.append(up)
                aperture_radii.append(aperture_radius)
                focus_distances.append(focus_distance)

        nb_frames = len(origins)
        for i in range(nb_frames):
            o = [0, 0, 0]
            d = [0, 0, 0]
            u = [0, 0, 0]
            aperture_radius = 0.0
            focus_distance = 0.0
            for j in range(int(smoothing_size)):
                index = int(max(0, min(i + j - smoothing_size / 2, nb_frames - 1)))
                for k in range(3):
                    o[k] = o[k] + origins[index][k]
                    d[k] = d[k] + directions[index][k]
                    u[k] = u[k] + ups[index][k]
                aperture_radius = aperture_radius + aperture_radii[index]
                focus_distance = focus_distance + focus_distances[index]
            self._smoothed_key_frames.append([(o[0] / smoothing_size, o[1] / smoothing_size, o[2] / smoothing_size),
                                              (d[0] / smoothing_size, d[1] / smoothing_size, d[2] / smoothing_size),
                                              (u[0] / smoothing_size, u[1] / smoothing_size, u[2] / smoothing_size),
                                              aperture_radius / smoothing_size, focus_distance / smoothing_size])
        last = control_points[len(control_points) - 1]
        self._smoothed_key_frames.append(
            (last['origin'], last['direction'], last['up'], last['apertureRadius'], last['focusDistance']))

    def get_nb_frames(self):
        """
        Get the number of smoothed frames

        @return: The number of smoothed frames
        """
        return len(self._smoothed_key_frames)

    def get_key_frame(self, frame):
        """
        Get the smoothed camera information for the given frame

        @param int frame: Frame number
        @return: The smoothed camera information for the given frame
        """
        if frame < len(self._smoothed_key_frames):
            return self._smoothed_key_frames[frame]
        raise KeyError

    def set_camera(self, origin, direction, up):
        """
        Set the camera using origin, direction and up vectors

        @param list origin: Origin of the camera
        @param list direction: Direction in which the camera is looking
        @param list up: Up vector
        @return: Result of the request submission
        """
        params = dict()
        params['origin'] = origin
        params['direction'] = direction
        params['up'] = up
        return self._client.rockets_client.request(self.PLUGIN_API_PREFIX + 'set-odu-camera', params)

    def get_camera(self):
        """
        Get the origin, direction and up vector of the camera

        @return: A JSon representation of the origin, direction and up vectors
        """
        return self._client.rockets_client.request(self.PLUGIN_API_PREFIX + 'get-odu-camera')

    def export_frames(self, path, size, image_format='png',
                      animation_frames=list(), quality=100, samples_per_pixel=1, start_frame=0, end_frame=0,
                      interpupillary_distance=0.0, exportIntermediateFrames=False):
        """
        Exports frames to disk. Frames are named using a 6 digit representation of the frame number

        @param path: Folder into which frames are exported
        @param image_format: Image format (the ones supported par Brayns: PNG, JPEG, etc)
        @param quality: Quality of the exported image (Between 0 and 100)
        @param samples_per_pixel: Number of samples per pixels
        @param start_frame: Optional value if the rendering should start at a specific frame.
        @param end_frame: Optional value if the rendering should end at a specific frame.
        @param exportIntermediateFrames: Exports intermediate frames (for every sample per pixel)
        @param interpupillary_distance: Distance between pupils. Stereo mode is activated if different from zero
        This is used to resume the rendering of a previously canceled sequence)
        @return: Result of the request submission
        """

        nb_frames = self.get_nb_frames()
        if end_frame == 0:
            end_frame = nb_frames

        assert isinstance(size, list)
        assert len(size) == 2
        if len(animation_frames) != 0:
            assert len(animation_frames) == nb_frames
        assert start_frame <= end_frame
        assert end_frame <= nb_frames

        self._client.set_application_parameters(viewport=size)
        self._client.set_renderer(accumulation=True, samples_per_pixel=1, max_accum_frames=samples_per_pixel + 1,
                                  subsampling=1)

        camera_definitions = list()
        for i in range(self.get_nb_frames()):
            camera_definitions.append(self.get_key_frame(i))

        params = dict()
        params['path'] = path
        params['format'] = image_format
        params['quality'] = quality
        params['spp'] = samples_per_pixel
        params['startFrame'] = start_frame
        params['endFrame'] = end_frame
        params['exportIntermediateFrames'] = exportIntermediateFrames
        params['animationInformation'] = animation_frames
        values = list()
        for camera_definition in camera_definitions:
            # Origin
            for i in range(3):
                values.append(camera_definition[0][i])
            # Direction
            for i in range(3):
                values.append(camera_definition[1][i])
            # Up
            for i in range(3):
                values.append(camera_definition[2][i])
            # Aperture radius
            values.append(camera_definition[3])
            # Focus distance
            values.append(camera_definition[4])
            # Interpupillary distance
            values.append(interpupillary_distance)

        params['cameraInformation'] = values
        self._client.rockets_client.request(self.PLUGIN_API_PREFIX + 'export-frames-to-disk', params)

    def get_export_frames_progress(self):
        """
        Queries the progress of the last export of frames to disk request

        @return: Dictionary with the result: "frameNumber" with the number of
        the last written-to-disk frame, and "done", a boolean flag stating wether
        the exporting is finished or is still in progress
        """
        return self._client.rockets_client.request(self.PLUGIN_API_PREFIX + 'get-export-frames-progress')

    def cancel_frames_export(self):
        """
        Cancel the exports of frames to disk

        @return: Result of the request submission
        """
        params = dict()
        params['path'] = '/tmp'
        params['format'] = 'png'
        params['quality'] = 100
        params['spp'] = 1
        params['startFrame'] = 0
        params['endFrame'] = 0
        params['exportIntermediateFrames'] = False
        params['animationInformation'] = []
        params['cameraInformation'] = []
        return self._client.rockets_client.request(self.PLUGIN_API_PREFIX + 'export-frames-to-disk', params)

    def set_current_frame(self, frame, camera_params=None):
        assert frame >= 0
        assert frame < self.get_nb_frames()

        cam = self.get_key_frame(frame)

        origin = list(cam[0])
        direction = list(cam[1])
        up = list(cam[2])

        self.set_camera(origin=origin, direction=direction, up=up)
        self._client.set_animation_parameters(current=frame)

        if camera_params is not None:
            camera_params.aperture_radius = cam[3] 
            camera_params.focus_distance = cam[4]
            camera_params.enable_clipping_planes = False
            self._client.set_camera_params(camera_params)

    def display(self, camera_params=None):
        """
        Displays a widget giving access to the movie frames
        """
        from ipywidgets import IntSlider
        frame = IntSlider(description='frame', min=0, max=self.get_nb_frames()-1)
        
        def update_frame(args):
            frame.value = args['new']
            self.set_current_frame(frame.value)

        frame.observe(update_frame, 'value')
        display(frame)

    def create_snapshot(self, size, path, samples_per_pixel, exportIntermediateFrames=True):

        from ipywidgets import IntProgress
        import os
        import copy

        application_params = self._client.get_application_parameters()
        renderer_params = self._client.get_renderer()
        old_image_stream_fps = application_params['image_stream_fps']
        old_viewport_size = application_params['viewport']
        old_samples_per_pixel = renderer_params['samples_per_pixel']
        old_max_accum_frames = renderer_params['max_accum_frames']
        old_smoothed_key_frames = copy.deepcopy(self._smoothed_key_frames)

        self._client.set_renderer(samples_per_pixel=1, max_accum_frames=samples_per_pixel)
        self._client.set_application_parameters(viewport=size)
        self._client.set_application_parameters(image_stream_fps=0)

        control_points = [self.get_camera()]
        current_animation_frame = int(self._client.get_animation_parameters()['current'])
        animation_frames = [current_animation_frame]

        self.build_camera_path(control_points=control_points, nb_steps_between_control_points=1,
                                            smoothing_size=1)

        progress_widget = IntProgress(description='In progress...', min=0, max=100, value=0)
        display(progress_widget)

        base_dir = os.path.dirname(path)
        self.export_frames(
            path=base_dir, animation_frames=animation_frames, size=size,
            samples_per_pixel=samples_per_pixel, exportIntermediateFrames=exportIntermediateFrames)

        done = False
        while not done:
            import time
            time.sleep(1)
            progress = self.get_export_frames_progress()['progress']
            progress_widget.value = progress * 100
            done = self.get_export_frames_progress()['done']

        progress_widget.description = 'Done'
        progress_widget.value = 100
        frame_path = base_dir + '/00000.png'
        if os.path.exists(frame_path):
            os.rename(frame_path, path)

        self._client.set_application_parameters(image_stream_fps=old_image_stream_fps,
                                                viewport=old_viewport_size)
        self._client.set_renderer(samples_per_pixel=old_samples_per_pixel,
                                  max_accum_frames=old_max_accum_frames)
        self._smoothed_key_frames = copy.deepcopy(old_smoothed_key_frames)


    def create_movie(self, path, size, image_format='png', animation_frames=list(), 
                     quality=100, samples_per_pixel=1, start_frame=0, end_frame=0, interpupillary_distance=0.0, 
                     exportIntermediateFrames=True):

        from ipywidgets import IntProgress

        application_params = self._client.get_application_parameters()
        renderer_params = self._client.get_renderer()

        old_image_stream_fps = application_params['image_stream_fps']
        old_viewport_size = application_params['viewport']
        old_samples_per_pixel = renderer_params['samples_per_pixel']
        old_max_accum_frames = renderer_params['max_accum_frames']
        self._client.set_renderer(samples_per_pixel=1, max_accum_frames=samples_per_pixel)
        self._client.set_application_parameters(viewport=size)
        self._client.set_application_parameters(image_stream_fps=0)

        progress_widget = IntProgress(description='In progress...', min=0, max=100, value=0)
        display(progress_widget)

        self.export_frames(path=path, animation_frames=animation_frames, start_frame=start_frame,
            end_frame=end_frame, size=size, samples_per_pixel=samples_per_pixel, quality=quality, 
            interpupillary_distance=interpupillary_distance, exportIntermediateFrames=exportIntermediateFrames)

        done = False
        while not done:
            import time
            time.sleep(1)
            progress = self.get_export_frames_progress()['progress']
            progress_widget.value = progress * 100
            done = self.get_export_frames_progress()['done']

        self._client.set_application_parameters(image_stream_fps=old_image_stream_fps,
                                                viewport=old_viewport_size)
        self._client.set_renderer(samples_per_pixel=old_samples_per_pixel,
                                  max_accum_frames=old_max_accum_frames)

        progress_widget.description = 'Done'
        progress_widget.value = 100
