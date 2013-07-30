# -*- coding: utf-8 -*-
"""Test for VideoAlpha Xmodule functional logic.
These tests data readed from xml, not from mongo.

We have a ModuleStoreTestCase class defined in
common/lib/xmodule/xmodule/modulestore/tests/django_utils.py.
You can search for usages of this in the cms and lms tests for examples.
You use this so that it will do things like point the modulestore
setting to mongo, flush the contentstore before and after, load the
templates, etc.
You can then use the CourseFactory and XModuleItemFactory as defined in
common/lib/xmodule/xmodule/modulestore/tests/factories.py to create the
course, section, subsection, unit, etc.
"""

import json
import unittest

from django.conf import settings

from xmodule.videoalpha_module import VideoAlphaDescriptor, VideoAlphaModule, _create_youtube_string
from xmodule.modulestore import Location
from xmodule.tests import get_test_system


SOURCE_XML = """
    <videoalpha show_captions="true"
    display_name="A Name"
    youtube="0.75:jNCf2gIqpeE,1.0:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg"
    sub="a_sub_file.srt.sjson"
    start_time="01:00:03" end_time="01:00:10"
    >
        <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
        <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
        <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
    </videoalpha>
"""


class VideoAlphaFactory(object):
    """A helper class to create videoalpha modules with various parameters
    for testing.
    """

    # tag that uses youtube videos
    sample_problem_xml_youtube = SOURCE_XML

    @staticmethod
    def create():
        """Method return VideoAlpha Xmodule instance."""
        location = Location(["i4x", "edX", "videoalpha", "default",
                             "SampleProblem1"])
        model_data = {'data': VideoAlphaFactory.sample_problem_xml_youtube}

        system = get_test_system()
        system.render_template = lambda template, context: context

        descriptor = VideoAlphaDescriptor(system, model_data)

        VideoAlphaModule.location = location
        module = descriptor.xmodule(system)

        return module


class VideoAlphaModuleUnitTest(unittest.TestCase):
    """Unit tests for VideoAlpha Xmodule."""

    def test_videoalpha_get_html(self):
        """Make sure that all parameters extracted correclty from xml"""
        module = VideoAlphaFactory.create()

        sources = {
            'main': '.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            'mp4': '.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            'webm': '.../mit-3091x/M-3091X-FA12-L21-3_100.webm',
            'ogv': '.../mit-3091x/M-3091X-FA12-L21-3_100.ogv'
        }

        # `get_html` return only context, cause we
        # overwrite `system.render_template`
        context = module.get_html()
        expected_context = {
            'caption_asset_path': '/static/subs/',
            'sub': 'a_sub_file.srt.sjson',
            'data_dir': getattr(self, 'data_dir', None),
            'display_name': 'A Name',
            'end': 3610.0,
            'start': 3603.0,
            'id': module.location.html_id(),
            'show_captions': True,
            'sources': sources,
            'youtube_streams': _create_youtube_string(module),
            'track': '',
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }
        self.assertDictEqual(context, expected_context)

    def test_videoalpha_instance_state(self):
        module = VideoAlphaFactory.create()

        self.assertDictEqual(
            json.loads(module.get_instance_state()),
            {'position': 0})
