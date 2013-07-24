if (!CMS.Views['Settings']) CMS.Views.Settings = {};

CMS.Views.Settings.Advanced = CMS.Views.ValidatingView.extend({
    error_saving : "error_saving",
    successful_changes: "successful_changes",

    // Model class is CMS.Models.Settings.Advanced
    events : {
        'focus :input' : "focusInput",
        'blur :input' : "blurInput"
        // TODO enable/disable save based on validation (currently enabled whenever there are changes)
    },
    initialize : function() {
        this.template = _.template($("#advanced_entry-tpl").text());
        this.listenTo(this.model, 'invalid', this.handleValidationError);
        this.render();
    },
    render: function() {
        // catch potential outside call before template loaded
        if (!this.template) return this;

        var listEle$ = this.$el.find('.course-advanced-policy-list');
        listEle$.empty();

        // b/c we've deleted all old fields, clear the map and repopulate
        this.fieldToSelectorMap = {};
        this.selectorToField = {};

        // iterate through model and produce key : value editors for each property in model.get
        var self = this;
        _.each(_.sortBy(_.keys(this.model.attributes), _.identity),
            function(key) {
                var li = $(self.renderTemplate(key));
                listEle$.append(li);
                var editor_element = li.find("div.editor").get(0);
                self.attachJSONEditor(editor_element, self.model.get(key));
            });

        return this;
    },
    attachJSONEditor : function (element, obj) {
        var self = this;
        $(element).css({height: "10em", width: "25em"});
        var editor = ace.edit(element);
        editor.setTheme("ace/theme/chrome");
        editor.getSession().setMode("ace/mode/json");
        editor.setFontSize(20);
        editor.setOption("showGutter", false);
        value = JSON.stringify(obj, null, "  ");
        editor.setValue(value);
        editor.on("change", function(e) {
            if (editor.getValue() !== value) {
                var message = gettext("Your changes will not take effect until you save your progress. Take care with key and value formatting, as validation is not implemented.");
                self.showNotificationBar(message,
                                     _.bind(self.saveView, self),
                                     _.bind(self.revertView, self));
            }
        });
        editor.on("focus", function() {
            $(element).parent().children('label').addClass("is-focused");
        });
        editor.on("blur", function() {
            $(element).parent().children('label').removeClass("is-focused");
            var key = $(editor.container).closest('.field-group').children('.key').attr('id');
            var stringValue = $.trim(editor.getValue());
            // update ace to show the trimmed value.
            editor.setValue(stringValue);
            var JSONValue;
            try {
                JSONValue = JSON.parse(stringValue);
            } catch (e) {
                // If it didn't parse, try converting non-arrays/non-objects to a String.
                // But don't convert single-quote strings, which are most likely errors.
                var firstNonWhite = stringValue.substring(0, 1);
                if (firstNonWhite !== "{" && firstNonWhite !== "[" && firstNonWhite !== "'") {
                    try {
                        stringValue = '"'+stringValue +'"';
                        JSONValue = JSON.parse(stringValue);
                        mirror.setValue(stringValue);
                    } catch(quotedE) {
                        // TODO: validation error
                        // console.log("Error with JSON, even after converting to String.");
                        // console.log(quotedE);
                        JSONValue = undefined;
                    }
                }
            }
            if (JSONValue !== undefined) {
                self.model.set(key, JSONValue);
            }
        });
    },
    saveView : function() {
        // TODO one last verification scan:
        //    call validateKey on each to ensure proper format
        //    check for dupes
        var self = this;
        this.model.save({}, {
            success : function() {
                self.render();
                var title = gettext("Your policy changes have been saved.");
                var message = gettext("Please note that validation of your policy key and value pairs is not currently in place yet. If you are having difficulties, please review your policy pairs.");
                self.showSavedBar(title, message);
                analytics.track('Saved Advanced Settings', {
                    'course': course_location_analytics
                });
            },
            silent: true
        });
    },
    revertView: function() {
        var self = this;
        this.model.fetch({
            success: function() { self.render(); },
            reset: true
        });
    },
    renderTemplate: function (key, value) {
        var newKeyId = _.uniqueId('policy_key_'),
        newEle = this.template({ key : key, value : JSON.stringify(value, null, 4),
            keyUniqueId: newKeyId, valueUniqueId: _.uniqueId('policy_value_')});

        this.fieldToSelectorMap[key] = newKeyId;
        this.selectorToField[newKeyId] = key;
        return newEle;
    },
    focusInput : function(event) {
        $(event.target).prev().addClass("is-focused");
    },
    blurInput : function(event) {
        $(event.target).prev().removeClass("is-focused");
    }
});
