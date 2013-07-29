(function (requirejs, require, define) {

// VideoVolumeControl module.
define(
'videoalpha/07_video_volume_control.js',
[],
function () {

    // VideoVolumeControl() function - what this module "exports".
    return function (state) {
        state.videoVolumeControl = {};

        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        state.videoVolumeControl.onChange = _.bind(onChange, state);
        state.videoVolumeControl.toggleMute = _.bind(toggleMute, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoVolumeControl.el = state.el.find('div.volume');

        state.videoVolumeControl.buttonEl = state.videoVolumeControl.el.find('a');
        state.videoVolumeControl.volumeSliderEl = state.videoVolumeControl.el.find('.volume-slider');

        state.videoControl.secondaryControlsEl.prepend(state.videoVolumeControl.el);

        // Figure out what the current volume is. If no information about volume level could be retrieved,
        // then we will use the default 100 level (full volume).
        state.videoVolumeControl.currentVolume = parseInt($.cookie('video_player_volume_level'), 10);
        if (!isFinite(state.videoVolumeControl.currentVolume)) {
            state.videoVolumeControl.currentVolume = 100;
        }

        // Set it up so that muting/unmuting works correctly.
        state.videoVolumeControl.previousVolume = 100;

        state.videoVolumeControl.slider = state.videoVolumeControl.volumeSliderEl.slider({
            orientation: 'vertical',
            range: 'min',
            min: 0,
            max: 100,
            value: state.videoVolumeControl.currentVolume,
            change: state.videoVolumeControl.onChange,
            slide: state.videoVolumeControl.onChange
        });

        state.videoVolumeControl.el.toggleClass('muted', state.videoVolumeControl.currentVolume === 0);
    }

    // function _bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function _bindHandlers(state) {
        state.videoVolumeControl.buttonEl.on('click', state.videoVolumeControl.toggleMute);

        state.videoVolumeControl.el.on('mouseenter', function() {
            $(this).addClass('open');
        });

        state.videoVolumeControl.el.on('mouseleave', function() {
            $(this).removeClass('open');
        });
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onChange(event, ui) {
        this.videoVolumeControl.currentVolume = ui.value;
        this.videoVolumeControl.el.toggleClass('muted', this.videoVolumeControl.currentVolume === 0);

        $.cookie('video_player_volume_level', ui.value, {
            expires: 3650,
            path: '/'
        });

        this.trigger('videoPlayer.onVolumeChange', ui.value);
    }

    function toggleMute(event) {
        event.preventDefault();

        if (this.videoVolumeControl.currentVolume > 0) {
            this.videoVolumeControl.previousVolume = this.videoVolumeControl.currentVolume;
            this.videoVolumeControl.slider.slider('option', 'value', 0);
        } else {
            this.videoVolumeControl.slider.slider('option', 'value', this.videoVolumeControl.previousVolume);
        }
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
