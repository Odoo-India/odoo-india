openerp.web_group_expand = function(openerp) {

    openerp.web.SearchView.include({
        do_search: function (_query, options) {
            if (options && options.preventSearch) {
                return;
            }
            var search = this.build_search_data();
            if (!_.isEmpty(search.errors)) {
                this.on_invalid(search.errors);
                return;
            }
            
            $("ul#ul_group_by").remove();
            if(search.groupbys.length)
            	{
            	$("ul.oe_view_manager_switch.oe_button_group.oe_right").before('<ul id="ul_group_by"class="oe_view_manager_switch oe_button_group oe_right"><li class="oe_i group_expand" style="border: none;border-top: 1px solid #ababab;position:relative;font-size:13px;transform: rotate(90deg);-webkit-transform: rotate(90deg);"><a id="group_by_expand"><hr style="height:2px; visibility:hidden; margin-bottom:-7px;"/>( )</a></li><li class="oe_i group_expand"><a style="top:3px;position:relative;" id="group_by_reset">P</a></li></ul>')
            	$("a#group_by_reset").click(function(){
            		var x = document.getElementsByTagName('span');
            		for (i = 0; i < x.length; i++) {
            			y = x[i];
            			if (y.className == "ui-icon ui-icon-triangle-1-s") {
            				y.click();
            			}
            		}
            	});
            	$("a#group_by_expand").click(function(){
            		var x = document.getElementsByTagName('span');
            		for (i = 0; i < x.length; i++) {
            			y = x[i];
            			if (y.className == "ui-icon ui-icon-triangle-1-e") {
            				y.click();
            			}
            		}
            	});
            	}
            this.trigger('search_data', search.domains, search.contexts, search.groupbys);
        },
    })
}