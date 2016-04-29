odoo.define('mail_channel_remote.composer', function (require) {
"use strict";


var chat_manager = require('mail.chat_manager');
var core = require('web.core');
var data = require('web.data');
var session = require('web.session');
var Model = require('web.Model');
var Widget = require('web.Widget');
var ChatComposer = require('mail.composer');

var LocationComposer = ChatComposer.BasicComposer.include({
    events: _.defaults({
        "click .o_composer_button_location": "send_location",
    }, ChatComposer.BasicComposer.prototype.events),
    send_location:function(){
        var self = this;
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position){
                var latitude = position.coords.latitude
                var longitude = position.coords.longitude
                var map = ("https://maps.googleapis.com/maps/api/staticmap?center=" + latitude + "," + longitude + "&markers=" + latitude + "," + longitude + "&zoom=15&size=500x200&sensor=false");
                var href = ("https://maps.google.com/maps?q=" + latitude + "," + longitude);
                var value = "<a target='_new' href=" + href + "><img src='" + map + "'/></a>"
                var data = ({
                    content: value,
                });
                self.trigger('post_message', data);
            });
        }
    },
});
});