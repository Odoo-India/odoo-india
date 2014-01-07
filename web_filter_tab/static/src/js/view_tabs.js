openerp.web_filter_tab = function(instance) {
    var QWeb = instance.web.qweb,
    _t = instance.web._t;
    openerp.web.ListView.include({
        load_list: function(data) {
            var self = this;
            this._super.apply(this, arguments);
            var search_view = self.getParent().searchview;
            self.getParent().$el.find('.tabs_row').remove();
            self.$el.before(QWeb.render('view_tabs'));
            if(search_view){
                var $tabs_row = $('.tabs_row');
                _.each(search_view.$el.find(".oe_searchview_custom_list li"),function(x) {
                    $tabs_row.append($(x).clone(true).css('width',100/search_view.$el.find(".oe_searchview_custom_list li").length+'%'));
                });
           }
        },
    });
}