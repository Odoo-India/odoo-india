openerp.web_filter_tabs = function(instance) {
    var QWeb = instance.web.qweb,
      _t =  instance.web._t,
     _lt = instance.web._lt;

    instance.web.search.CustomFilters.include({
        init: function(){
            this._super.apply(this, arguments);
            this.tab_filters = {};
        },
        append_filter: function(filter) {
            this._super.apply(this, arguments);
            this.add_tab(this.key_for(filter));
        },
        add_tab: function(key){
            this.tab_filters[key] = new instance.web.search.TabFilters(this, key);
            this.tab_filters[key].appendTo($('.oe_searchview_custom_tabs'))
        },
        toggle_filter: function (filter, preventSearch) {
            this._super.apply(this, arguments);
            var current = this.view.query.find(function (facet) {
                return facet.get('_id') === filter.id;
            });
            active_tab = _(this.tab_filters).detect(function(tab_filter) { return tab_filter.$el.hasClass('oe_selected'); })
            //super already adds current facet, so applied reverse condition
            if (!current && active_tab) {
                active_tab.$el.removeClass('oe_selected');
                return;
            }
            if (current)
                this.tab_filters[this.key_for(filter)].$el.addClass('oe_selected');
        },
        clear_selection: function() {
            _(this.tab_filters).each(function(tab_filter){tab_filter.$el.removeClass('oe_selected')})
            this._super.apply(this, arguments);
        }
    });
    instance.web.search.TabFilters = instance.web.Widget.extend({
        init: function(parent, key){
            this._super.apply(this, arguments);
            this.key = key;
            this.filter = parent.$filters[key].clone(true, true);
            this.parent = parent;
        },
        start: function(){
            var self = this;
            this._super.apply(this, arguments);
            var self = this;
            this.filter.find(".oe_searchview_custom_delete").click(function(){
                self.destroy();
            });
        },
        renderElement: function(){
            return this.replaceElement(this.filter)
        },
        destroy: function(){
            delete this.parent.tab_filters[this.key];
            return this._super.apply(this, arguments);
        }
    });
    instance.web.ViewManager.include({
        switch_mode: function(view_type, no_store, view_options) {
            if(view_type == 'form') {
                this.$el.find('.oe_custom_filter_tabs').hide();
            } else {
                this.$el.find('.oe_custom_filter_tabs').show();
            }
            return this._super.apply(this, arguments);
        }
    });
};