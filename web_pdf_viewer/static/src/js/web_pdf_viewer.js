openerp.web_pdf_viewer = function (openerp) {
    openerp.web.Session.include({
        get_file: function (options) {
            // need to detect when the file is done downloading (not used
            // yet, but we'll need it to fix the UI e.g. with a throbber
            // while dump is being generated), iframe load event only fires
            // when the iframe content loads, so we need to go smarter:
            // http://geekswithblogs.net/GruffCode/archive/2010/10/28/detecting-the-file-download-dialog-in-the-browser.aspx
            var timer, token = new Date().getTime(),
                cookie_name = 'fileToken',
                cookie_length = cookie_name.length,
                CHECK_INTERVAL = 1000,
                id = _.uniqueId('get_file_frame'),
                remove_form = false;
            var is_pdf = 0;
            var $form, $form_data = $('<div>');
            if (options.hasOwnProperty('data')) {
                if (options.data.hasOwnProperty('action')) {
                    if (JSON.parse(options.data.action).hasOwnProperty('report_type')) {
                    	
                        if (JSON.parse(options.data.action)['report_type'] == 'pdf') {
                            is_pdf = 1;
                            var complete = function () {
                                if (options.complete) {
                                    options.complete();
                                }
                            };
                            $('.oe_view_manager.oe_view_manager_current').children().hide();
                            var height_window = ($(window).height()) - 32;
                            var $target = $('<iframe style="top:100px;left:1px;z-index:500;width:100%;height:' + height_window + 'px;">')
                                .attr({
                                id: id,
                                name: id
                            })
                                .prependTo(".oe_view_manager.oe_view_manager_current")
                                .load(function () {
                                $('<a><div class="close_print"><div><div>X</div><i>Close</i></div></div></a>')
                                    .attr({
                                    id: 'close_print'
                                })
                                    .prependTo(".oe_view_manager.oe_view_manager_current");
                                $("#close_print").click(function () {
                                    clearTimeout(timer);
                                    $form_data.remove();
                                    $target.remove();
                                    if (remove_form && $form) {
                                        $form.remove();
                                    }
                                    $("#close_print").remove();
                                    $('.oe_view_manager.oe_view_manager_current').children().show();
                                });
                            });
                            if (options.form) {
                                $form = $(options.form);
                            } else {
                                remove_form = true;
                                $form = $('<form>', {
                                    action: options.url,
                                    method: 'GET'
                                }).appendTo(document.body);
                            }
                            _(_.extend({}, options.data || {}, {
                                session_id: this.session_id,
                                token: token
                            }))
                                .each(function (value, key) {
                                var $input = $form.find('[name=' + key + ']');
                                if (!$input.length) {
                                    $input = $('<input style="display:none;" name="' + key + '">')
                                        .appendTo($form_data);
                                }
                                $input.val(value)
                            });
                        }
                    }
                }
            }
            if (is_pdf == 0) {
                var complete = function () {
                    if (options.complete) {
                        options.complete();
                    }
                    clearTimeout(timer);
                    $form_data.remove();
                    $target.remove();
                    if (remove_form && $form) {
                        $form.remove();
                    }
                };
                var $target = $('<iframe style="display: none;">')
                    .attr({
                    id: id,
                    name: id
                })
                    .appendTo(document.body)
                    .load(function () {
                    try {
                        if (options.error) {
                            if (!this.contentDocument.body.childNodes[1]) {
                                options.error(this.contentDocument.body.childNodes);
                            } else {
                                options.error(JSON.parse(this.contentDocument.body.childNodes[1].textContent));
                            }
                        }
                    } finally {
                        complete();
                    }
                });
                if (options.form) {
                    $form = $(options.form);
                } else {
                    remove_form = true;
                    $form = $('<form>', {
                        action: options.url,
                        method: 'POST'
                    }).appendTo(document.body);
                }
                _(_.extend({}, options.data || {}, {
                    session_id: this.session_id,
                    token: token
                }))
                    .each(function (value, key) {
                    var $input = $form.find('[name=' + key + ']');
                    if (!$input.length) {
                        $input = $('<input type="hidden" name="' + key + '">')
                            .appendTo($form_data);
                    }
                    $input.val(value)
                });
            }
            $form
                .append($form_data)
                .attr('target', id)
                .get(0).submit();
            var waitLoop = function () {
                var cookies = document.cookie.split(';');
                // setup next check
                timer = setTimeout(waitLoop, CHECK_INTERVAL);
                for (var i = 0; i < cookies.length; ++i) {
                    var cookie = cookies[i].replace(/^\s*/, '');
                    if (!cookie.indexOf(cookie_name === 0)) {
                        continue;
                    }
                    var cookie_val = cookie.substring(cookie_length + 1);
                    if (parseInt(cookie_val, 10) !== token) {
                        continue;
                    }
                    // clear cookie
                    document.cookie = _.str.sprintf("%s=;expires=%s;path=/",
                        cookie_name, new Date().toGMTString());
                    if (options.success) {
                        options.success();
                    }
                    complete();
                    return;
                }
            };
            timer = setTimeout(waitLoop, CHECK_INTERVAL);
        },
    });
};