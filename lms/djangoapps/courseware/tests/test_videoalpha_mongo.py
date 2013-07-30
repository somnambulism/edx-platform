# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""

from . import BaseTestXmodule
from .test_videoalpha_xml import SOURCE_XML
from django.conf import settings
from xmodule.videoalpha_module import _create_youtube_string


class TestVideo(BaseTestXmodule):
    """Integration tests: web client + mongo."""

    CATEGORY = "videoalpha"
    DATA = SOURCE_XML
    MODEL_DATA = {
        'data': DATA
    }

    def test_handle_ajax_dispatch(self):
        responses = {
            user.username: self.clients[user.username].post(
                self.get_url('whatever'),
                {},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            for user in self.users
        }

        self.assertEqual(
            set([
                response.status_code
                for _, response in responses.items()
                ]).pop(),
            404)

    def test_videoalpha_constructor(self):
        """Make sure that all parameters extracted correclty from xml"""

        sources = {
            'main': '.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            'mp4': '.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            'webm': '.../mit-3091x/M-3091X-FA12-L21-3_100.webm',
            'ogv': '.../mit-3091x/M-3091X-FA12-L21-3_100.ogv'
        }

        # `get_html` return only context, cause we
        # overwrite `system.render_template`
        context = self.item_module.get_html()
        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/c4x/MITx/999/asset/subs_',
            'show_captions': True,
            'display_name': 'A Name',
            'end': 3610.0,
            'id': self.item_module.location.html_id(),
            'sources': sources,
            'start': 3603.0,
            'sub': 'a_sub_file.srt.sjson',
            'track': '',
            'youtube_streams': _create_youtube_string(self.item_module),
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }
        self.assertDictEqual(context, expected_context)


class TestVideoNonYouTube(TestVideo):
    """Integration tests: web client + mongo."""

    DATA = """
        <videoalpha show_captions="true"
        display_name="A Name"
        sub="a_sub_file.srt.sjson"
        start_time="01:00:03" end_time="01:00:10"
        >
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.mp4"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.webm"/>
            <source src=".../mit-3091x/M-3091X-FA12-L21-3_100.ogv"/>
        </videoalpha>
    """
    MODEL_DATA = {
        'data': DATA
    }

    def test_videoalpha_constructor(self):
        """Make sure that if the 'youtube' attribute is omitted in XML, then
            the template generates an empty string for the YouTube streams.
        """
        sources = {
            u'main': u'.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            u'mp4': u'.../mit-3091x/M-3091X-FA12-L21-3_100.mp4',
            u'webm': u'.../mit-3091x/M-3091X-FA12-L21-3_100.webm',
            u'ogv': u'.../mit-3091x/M-3091X-FA12-L21-3_100.ogv'
        }

        # `get_html` return only context, cause we
        # overwrite `system.render_template`
        context = self.item_module.get_html()
        expected_context = {
            'data_dir': getattr(self, 'data_dir', None),
            'caption_asset_path': '/c4x/MITx/999/asset/subs_',
            'show_captions': True,
            'display_name': 'A Name',
            'end': 3610.0,
            'id': self.item_module.location.html_id(),
            'sources': sources,
            'start': 3603.0,
            'sub': 'a_sub_file.srt.sjson',
            'track': '',
            'youtube_streams': '',
            'autoplay': settings.MITX_FEATURES.get('AUTOPLAY_VIDEOS', True)
        }
        self.assertDictEqual(context, expected_context)
