# -*- coding: utf-8 -*-
#pylint: disable=W0212
"""Test for Video Alpha Xmodule functional logic.
These test data read from  xml, not from mongo.

We have a ModuleStoreTestCase class defined in
common/lib/xmodule/xmodule/modulestore/tests/django_utils.py. You can
search for usages of this in the cms and lms tests for examples. You use
this so that it will do things like point the modulestore setting to mongo,
flush the contentstore before and after, load the templates, etc.
You can then use the CourseFactory and XModuleItemFactory as defined
in common/lib/xmodule/xmodule/modulestore/tests/factories.py to create
the course, section, subsection, unit, etc.
"""

from xmodule.modulestore import Location
from xmodule.videoalpha_module import VideoAlphaDescriptor, _create_youtube_string
from xmodule.video_module import VideoDescriptor
from . import LogicTest
from .test_import import DummySystem

from textwrap import dedent
import unittest


class VideoAlphaModuleTest(LogicTest):
    """Logic tests for VideoAlpha Xmodule."""
    descriptor_class = VideoAlphaDescriptor

    raw_model_data = {
        'data': '<videoalpha />'
    }

    def test_parse_time_empty(self):
        """Ensure parse_time returns correctly with None or empty string."""
        expected = ''
        self.assertEqual(VideoAlphaDescriptor._parse_time(None), expected)
        self.assertEqual(VideoAlphaDescriptor._parse_time(''), expected)

    def test_parse_time(self):
        """Ensure that times are parsed correctly into seconds."""
        expected = 247
        output = VideoAlphaDescriptor._parse_time('00:04:07')
        self.assertEqual(output, expected)

    def test_parse_youtube(self):
        """Test parsing old-style Youtube ID strings into a dict."""
        youtube_str = '0.75:jNCf2gIqpeE,1.00:ZwkTiUPN0mg,1.25:rsq9auxASqI,1.50:kMyNdzVHHgg'
        output = VideoAlphaDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': 'jNCf2gIqpeE',
                                  '1.00': 'ZwkTiUPN0mg',
                                  '1.25': 'rsq9auxASqI',
                                  '1.50': 'kMyNdzVHHgg'})

    def test_parse_youtube_one_video(self):
        """
        Ensure that all keys are present and missing speeds map to the
        empty string.
        """
        youtube_str = '0.75:jNCf2gIqpeE'
        output = VideoAlphaDescriptor._parse_youtube(youtube_str)
        self.assertEqual(output, {'0.75': 'jNCf2gIqpeE',
                                  '1.00': '',
                                  '1.25': '',
                                  '1.50': ''})

    def test_parse_youtube_key_format(self):
        """
        Make sure that inconsistent speed keys are parsed correctly.
        """
        youtube_str = '1.00:p2Q6BrNhdh8'
        youtube_str_hack = '1.0:p2Q6BrNhdh8'
        self.assertEqual(
            VideoAlphaDescriptor._parse_youtube(youtube_str),
            VideoAlphaDescriptor._parse_youtube(youtube_str_hack)
        )

    def test_parse_youtube_empty(self):
        """
        Some courses have empty youtube attributes, so we should handle
        that well.
        """
        self.assertEqual(
            VideoAlphaDescriptor._parse_youtube(''),
            {'0.75': '',
             '1.00': '',
             '1.25': '',
             '1.50': ''}
        )

    def test_create_youtube_string(self):
        """
        Test that Youtube ID strings are correctly created when writing
        back out to XML.
        """
        system = DummySystem(load_error_modules=True)
        location = Location(["i4x", "edX", "videoalpha", "default", "SampleProblem1"])
        model_data = {'location': location}
        descriptor = VideoAlphaDescriptor(system, model_data)
        descriptor.youtube_id_0_75 = 'izygArpw-Qo'
        descriptor.youtube_id_1_0 = 'p2Q6BrNhdh8'
        descriptor.youtube_id_1_25 = '1EeWXzPdhSA'
        descriptor.youtube_id_1_5 = 'rABDYkeK0x8'
        expected = "0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8"
        self.assertEqual(_create_youtube_string(descriptor), expected)

    def test_create_youtube_string_missing(self):
        """
        Test that Youtube IDs which aren't explicitly set aren't included
        in the output string.
        """
        system = DummySystem(load_error_modules=True)
        location = Location(["i4x", "edX", "videoalpha", "default", "SampleProblem1"])
        model_data = {'location': location}
        descriptor = VideoAlphaDescriptor(system, model_data)
        descriptor.youtube_id_0_75 = 'izygArpw-Qo'
        descriptor.youtube_id_1_0 = 'p2Q6BrNhdh8'
        descriptor.youtube_id_1_25 = '1EeWXzPdhSA'
        expected = "0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA"
        self.assertEqual(_create_youtube_string(descriptor), expected)


class VideoAlphaDescriptorImportTestCase(unittest.TestCase):
    """
    Make sure that VideoAlphaDescriptor can import an old XML-based video correctly.
    """

    def test_constructor(self):
        sample_xml = '''
            <videoalpha display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   start_time="00:00:01"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <source src="http://www.example.com/source.ogg"/>
              <track src="http://www.example.com/track"/>
            </videoalpha>
        '''
        location = Location(["i4x", "edX", "videoalpha", "default",
                             "SampleProblem1"])
        model_data = {'data': sample_xml,
                      'location': location}
        system = DummySystem(load_error_modules=True)
        descriptor = VideoAlphaDescriptor(system, model_data)
        self.assertEquals(descriptor.youtube_id_0_75, 'izygArpw-Qo')
        self.assertEquals(descriptor.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(descriptor.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(descriptor.youtube_id_1_5, 'rABDYkeK0x8')
        self.assertEquals(descriptor.show_captions, False)
        self.assertEquals(descriptor.start_time, 1.0)
        self.assertEquals(descriptor.end_time, 60)
        self.assertEquals(descriptor.track, 'http://www.example.com/track')
        self.assertEquals(descriptor.source, 'http://www.example.com/source.mp4')
        self.assertEquals(descriptor.html5_sources, ['http://www.example.com/source.mp4', 'http://www.example.com/source.ogg'])
        self.assertEquals(descriptor.data, '')

    def test_from_xml(self):
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <videoalpha display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   start_time="00:00:01"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </videoalpha>
        '''
        output = VideoAlphaDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, 'izygArpw-Qo')
        self.assertEquals(output.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(output.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(output.youtube_id_1_5, 'rABDYkeK0x8')
        self.assertEquals(output.show_captions, False)
        self.assertEquals(output.start_time, 1.0)
        self.assertEquals(output.end_time, 60)
        self.assertEquals(output.track, 'http://www.example.com/track')
        self.assertEquals(output.source, 'http://www.example.com/source.mp4')
        self.assertEquals(output.html5_sources, ['http://www.example.com/source.mp4'])
        self.assertEquals(output.data, '')

    def test_from_xml_missing_attributes(self):
        """
        Ensure that attributes have the right values if they aren't
        explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <videoalpha display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA"
                   show_captions="true">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </videoalpha>
        '''
        output = VideoAlphaDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, '')
        self.assertEquals(output.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(output.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(output.youtube_id_1_5, '')
        self.assertEquals(output.show_captions, True)
        self.assertEquals(output.start_time, 0.0)
        self.assertEquals(output.end_time, 0.0)
        self.assertEquals(output.track, 'http://www.example.com/track')
        self.assertEquals(output.source, 'http://www.example.com/source.mp4')
        self.assertEquals(output.html5_sources, ['http://www.example.com/source.mp4'])
        self.assertEquals(output.data, '')

    def test_from_xml_no_attributes(self):
        """
        Make sure settings are correct if none are explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '<videoalpha></videoalpha>'
        output = VideoAlphaDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, '')
        self.assertEquals(output.youtube_id_1_0, 'OEoXaMPEzfM')
        self.assertEquals(output.youtube_id_1_25, '')
        self.assertEquals(output.youtube_id_1_5, '')
        self.assertEquals(output.show_captions, True)
        self.assertEquals(output.start_time, 0.0)
        self.assertEquals(output.end_time, 0.0)
        self.assertEquals(output.track, '')
        self.assertEquals(output.source, '')
        self.assertEquals(output.html5_sources, [])
        self.assertEquals(output.data, '')

    def test_old_video_format(self):
        """
        Test backwards compatibility with VideoModule's XML format.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = """
            <videoalpha display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   from="00:00:01"
                   to="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </videoalpha>
        """
        output = VideoAlphaDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, 'izygArpw-Qo')
        self.assertEquals(output.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(output.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(output.youtube_id_1_5, 'rABDYkeK0x8')
        self.assertEquals(output.show_captions, False)
        self.assertEquals(output.start_time, 1.0)
        self.assertEquals(output.end_time, 60)
        self.assertEquals(output.track, 'http://www.example.com/track')
        self.assertEquals(output.source, 'http://www.example.com/source.mp4')
        self.assertEquals(output.html5_sources, ['http://www.example.com/source.mp4'])
        self.assertEquals(output.data, '')

    def test_old_video_data(self):
        module_system = DummySystem(load_error_modules=True)
        xml_data = """
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   from="00:00:01"
                   to="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        """
        video = VideoDescriptor.from_xml(xml_data, module_system)
        video_alpha = VideoAlphaDescriptor(module_system, video._model_data)
        self.assertEquals(video_alpha.youtube_id_0_75, 'izygArpw-Qo')
        self.assertEquals(video_alpha.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(video_alpha.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(video_alpha.youtube_id_1_5, 'rABDYkeK0x8')
        self.assertEquals(video_alpha.show_captions, False)
        self.assertEquals(video_alpha.start_time, 1.0)
        self.assertEquals(video_alpha.end_time, 60)
        self.assertEquals(video_alpha.track, 'http://www.example.com/track')
        self.assertEquals(video_alpha.source, 'http://www.example.com/source.mp4')
        self.assertEquals(video_alpha.html5_sources, ['http://www.example.com/source.mp4'])
        self.assertEquals(video_alpha.data, '')


class VideoAlphaExportTestCase(unittest.TestCase):
    """
    Make sure that VideoAlphaDescriptor can export itself to XML
    correctly.
    """

    def test_export_to_xml(self):
        """Test that we write the correct XML on export."""
        module_system = DummySystem(load_error_modules=True)
        location = Location(["i4x", "edX", "videoalpha", "default", "SampleProblem1"])
        desc = VideoAlphaDescriptor(module_system, {'location': location})

        desc.youtube_id_0_75 = 'izygArpw-Qo'
        desc.youtube_id_1_0 = 'p2Q6BrNhdh8'
        desc.youtube_id_1_25 = '1EeWXzPdhSA'
        desc.youtube_id_1_5 = 'rABDYkeK0x8'
        desc.show_captions = False
        desc.start_time = 1.0
        desc.end_time = 60
        desc.track = 'http://www.example.com/track'
        desc.html5_sources = ['http://www.example.com/source.mp4', 'http://www.example.com/source.ogg']

        xml = desc.export_to_xml(None)  # We don't use the `resource_fs` parameter
        expected = dedent('''\
         <videoalpha display_name="Video Alpha" start_time="0:00:01" youtube="0.75:izygArpw-Qo,1.00:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8" show_captions="false" end_time="0:01:00">
           <source src="http://www.example.com/source.mp4"/>
           <source src="http://www.example.com/source.ogg"/>
           <track src="http://www.example.com/track"/>
         </videoalpha>
        ''')

        self.assertEquals(expected, xml)

    def test_export_to_xml_empty_parameters(self):
        """Test XML export with defaults."""
        module_system = DummySystem(load_error_modules=True)
        location = Location(["i4x", "edX", "videoalpha", "default", "SampleProblem1"])
        desc = VideoAlphaDescriptor(module_system, {'location': location})

        xml = desc.export_to_xml(None)
        expected = '<videoalpha display_name="Video Alpha" youtube="1.00:OEoXaMPEzfM" show_captions="true"/>\n'

        self.assertEquals(expected, xml)
