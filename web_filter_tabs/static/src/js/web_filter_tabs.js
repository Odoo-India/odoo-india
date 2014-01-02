openerp.web_filter_tabs = function(instance) {
    var QWeb = instance.web.qweb,
      _t =  instance.web._t,
     _lt = instance.web._lt;

instance.web.search.CustomFilters.include({
    start: function() {
        this._super.apply(this, arguments);
        this.filters_tabs = {};
        this.$filters_tabs = {};
        this.color_pallete = ['#4986E7', '#16A765', '#FFC7C7', '#FFF1C7', '#E3FFC7', '#C7FFD5', '#C7FFFF', '#C7D5FF', '#E3C7FF', '#FFC7F1'];
        this.color_number = 0;
        //var parent = this.view.getParent();
        //$("<tr><td colspan='4' class='oe_custom_filter_tabs'></td></tr>").appendTo(parent.$el.find('.oe_view_manager_header'));
        //var $tabs_template = QWeb.render('CustomFilter.Tabs', {'widget': this});
        //parent.$el.find('.oe_custom_filter_tabs').html(QWeb.render('CustomFilter.Tabs', {'widget': this}));
    },
    set_filters: function() {
        var self = this;
        this._super.apply(this, arguments);
        //_(this.filters).map(_.bind(this.append_filter_tabs, this));
        var parent = this.view.getParent();
        $('<div title="Add Current Filter"><span>+</span></div>').appendTo(parent.$el.find('.oe_searchview_custom_tabs_div'))
        .addClass('oe_searchview_add_custom_tab')
        .click(function(){
            var $dialog = instance.web.dialog($('<div>'), {
                            modal: true,
                            title: _t("Save Current Filter"),
                            width: 'auto',
                            height: 'auto'
                        }).html(QWeb.render('SaveFilter', {'widget': this}));
            $dialog.find('button').click(function() {
                self.$('input:first').val($dialog.find('input:first').val());
                self.$('#oe_searchview_custom_public').val($dialog.find('#oe_searchview_custom_public').val());
                self.$('#oe_searchview_custom_default').val($dialog.find('#oe_searchview_custom_default').val());
                var result = self.save_current();
                $dialog.dialog('destroy');
                return result;
            });
            
        });
    },
    append_filter: function(filter) {
        var self = this;
        var parent = this.view.getParent();
        var key = this.key_for(filter);
        var warning = _t("This filter is global and will be removed for everybody if you continue.");

        var $filter;
        var $filter_tab

        if (key in this.$filters_tabs) {
            $filter_tab = this.$filters_tabs[key];
        } else {
            var id = filter.id;
            this.filters_tabs[key] = filter;

            //Add tab in header row
            $filter_tab = this.$filters_tabs[key] = $('<li></li>')
                .appendTo(parent.$el.find('.oe_searchview_custom_tabs'))
                .addClass(filter.user_id ? 'oe_searchview_custom_private'
                                         : 'oe_searchview_custom_public')
                .toggleClass('oe_searchview_custom_default', filter.is_default)
                .hover(function(){
                    if(!$(this).hasClass('oe_active_tab')) {
                        self.color_number = Math.floor((Math.random()*10)+1);
                        $(this).css({'border-top': 'thick solid '+self.color_pallete[self.color_number]});
                    }
                }, function() {
                    if(!$(this).hasClass('oe_active_tab'))
                        $(this).css({'border-top': 'thin solid #414141'});
                });
            $('<span></span>').appendTo($filter_tab);
            $filter_tab.find('span').text(filter.name);
        }

        if (key in this.$filters) {
            $filter = this.$filters[key];
        } else {
            var id = filter.id;
            this.filters[key] = filter;

            //Add Filter in searchbox
            $filter = this.$filters[key] = $('<li></li>')
            .appendTo(this.$('.oe_searchview_custom_list'))
            .addClass(filter.user_id ? 'oe_searchview_custom_private'
                                     : 'oe_searchview_custom_public')
            .toggleClass('oe_searchview_custom_default', filter.is_default)
            .text(filter.name);
        }

        if(!$filter.has('a').length) {
            $('<a class="oe_searchview_custom_delete">x</a>')
                .click(function (e) {
                    e.stopPropagation();
                    if (!(filter.user_id || confirm(warning))) {
                        return;
                    }
                    self.model.call('unlink', [id]).done(function () {
                        $filter_tab.remove();
                        $filter.remove();
                        delete self.$filters[key];
                        delete self.filters[key];
                        delete self.$filters_tabs[key];
                        delete self.filters_tabs[key];
                    });
                })
                .appendTo($filter);
        }
        if(!$filter_tab.has('a').length) {
            $('<a class="oe_searchview_custom_delete">x</a>')
                .click(function (e) {
                    e.stopPropagation();
                    if (!(filter.user_id || confirm(warning))) {
                        return;
                    }
                    self.model.call('unlink', [id]).done(function () {
                        $filter_tab.remove();
                        $filter.remove();
                        delete self.$filters[key];
                        delete self.filters[key];
                        delete self.$filters_tabs[key];
                        delete self.filters_tabs[key];
                    });
                })
                .appendTo($filter_tab);
        }

        $filter.unbind('click').click(function () {
            self.toggle_filter(filter);
            //self.toggle_tabs(filter);
        });
        $filter_tab.unbind('click').click(function () {
            self.toggle_filter(filter);
            //self.toggle_tabs(filter);
        });
    },
    toggle_filter: function(filter){
        this._super.apply(this, arguments);
        var current = this.view.query.find(function (facet) {
            return facet.get('_id') === filter.id;
        });
        var previous_active_tab = _(this.$filters_tabs).detect(function($filter) {return $filter.hasClass('oe_active_tab');});
        if (previous_active_tab) {
            previous_active_tab.removeClass('oe_active_tab').css({'border-top': 'thin solid #414141'});
        }
        if (!current) {
            return;
        }
        this.$filters_tabs[this.key_for(filter)].addClass('oe_active_tab').css({'border-top': 'thick solid '+this.color_pallete[this.color_number]});
    },
    /*
    toggle_tabs: function(filter, preventSearch) {
        var previous_active_tab = _(this.$filters_tabs).detect(function($filter) {return $filter.hasClass('oe_active_tab');});
        if (previous_active_tab) {
            previous_active_tab.removeClass('oe_active_tab');
        }
        //this.view.query.reset([this.facet_for(filter)], {
        //    preventSearch: preventSearch || false});
        this.$filters_tabs[this.key_for(filter)].addClass('oe_active_tab');
    },
    */
    clear_selection: function () {
        this._super.apply(this, arguments);
        var previous_active_tab = _(this.$filters_tabs).detect(function($filter) {return $filter.hasClass('oe_active_tab');});
        if (previous_active_tab) {
            previous_active_tab.removeClass('oe_active_tab').css({'border-top': 'thin solid #414141'});
        }
    },
});

instance.web.ViewManager.include({
    switch_mode: function(view_type, no_store, view_options) {
        if(view_type != 'list') {
            this.$el.find('.oe_custom_filter_tabs').hide();
        } else {
            this.$el.find('.oe_custom_filter_tabs').show();
        }
        return this._super.apply(this, arguments);
    }
});
};