# disable missing docstring
# pylint: disable=C0111

from lettuce import world, step


@step('I see the correct settings and default values$')
def i_see_the_correct_settings_and_values(step):
    world.verify_all_setting_entries([['Default Speed', 'OEoXaMPEzfM', False],
                                      ['Display Name', 'Video Title', False],
                                      ['Download Track', '', False],
                                      ['Download Video', '', False],
                                      ['Show Captions', 'True', False],
                                      ['Speed: .75x', '', False],
                                      ['Speed: 1.25x', '', False],
                                      ['Speed: 1.5x', '', False]])


@step('I have set "show captions" to (.*)')
def set_show_captions(step, setting):
    world.css_click('a.edit-button')
    world.browser.select('Show Captions', setting)
    world.css_click('a.save-button')


@step('I see the correct videoalpha settings and default values$')
def correct_videoalpha_settings(_step):
    world.verify_all_setting_entries([['Display Name', 'Video Alpha', False],
                                      ['Download Track', '', False],
                                      ['Download Video', '', False],
                                      ['HTML5 Subtitles', '', False],
                                      ['Show Captions', 'True', False],
                                      ['Video Sources', '', False],
                                      ['Youtube ID', 'OEoXaMPEzfM', False],
                                      ['Youtube ID for .75x speed', '', False],
                                      ['Youtube ID for 1.25x speed', '', False],
                                      ['Youtube ID for 1.5x speed', '', False]])
