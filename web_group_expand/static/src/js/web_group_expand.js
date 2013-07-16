openerp.web_group_expand = function(openerp) {
    openerp.web.ViewManager.include({
        switch_mode: function(view_type, no_store, view_options) {
            if (view_type != 'list') {
                $("ul#ul_group_by").remove();
            }
            return this._super.apply(this, arguments);
        },
        expand: function(domains, contexts, groupbys) {
            $("ul#ul_group_by").remove();
            if(groupbys.length && this.active_view == 'list') {
                $("ul.oe_view_manager_switch.oe_button_group.oe_right").before('<div class="oe_list_buttons"><ul id="ul_group_by"class="oe_view_manager_switch oe_button_group oe_right"><li class="oe_i group_expand" style="border: none;border-top: 1px solid #ababab;position:relative;font-size:13px;transform: rotate(90deg);-webkit-transform: rotate(90deg);"><a id="group_by_expand"><hr style="height:2px; visibility:hidden; margin-bottom:-7px;"/>( )</a></li><li class="oe_i group_expand"><a style="top:3px;position:relative;" id="group_by_reset">P</a></li></ul></div>')
                $("a#group_by_reset").click(function(){
                    $('span.ui-icon-triangle-1-s').click()
                });
                $("a#group_by_expand").click(function(){
                    $('span.ui-icon-triangle-1-e').click()
                });
            }
        },
        setup_search_view: function(view_id, search_defaults) {
            self = this;
            res = this._super.apply(this, arguments);
            this.searchview.on('search_data', self, this.expand);
            return res
        },
    })
}