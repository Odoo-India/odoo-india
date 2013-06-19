var fullscreen_toggle = {
    fullscreen_toggle: 0,
    search: 0,
    };
openerp.web_gui = function(openerp) {

    var QWeb = openerp.web.qweb;
    openerp.web.search.Filters.include({
        init: function() {
            this._super.apply(this, arguments);
            $(document).ready(function() {
                if ($('div.oe_popup_search').offset()) {
                    $('div.oe_searchview').css({
                        "position": "relative","width":"40%","right":"0px","top":"5px"
                    });
                }
                $(".oe_searchview_drawer").mouseenter(function() {
                    $(".oe_searchview_drawer").animate({
                        opacity: '1',
                        }, "fast");
                });

                $("div.oe_searchview").mouseenter(function() {

                    $("div.oe_searchview").animate({
                        opacity: '1',
                        }, "fast");
                });

                $("div.oe_searchview").mouseleave(function() {
                	
                    $("div.oe_searchview").animate({
                        opacity: '0.6',
                        }, "fast");
                });
                var size=$(".oe_systray_shortcuts_items li").size();
                var tamp={};
                for(i=0;i<size;i++)
                	{
                	var x=$(".oe_systray_shortcuts_items li a:eq("+i+")");
                	var patt2=/[\w ]*$/g;
                	if (x.html())
                	{var words=x.html().trim().match(patt2)}
                	if (words)
                	{
                	tamp[words[0]]=x.attr("data-id");
                	}	
                	}
                fullscreen_toggle["menu_dict"]=tamp;
                });
        }
    });

    openerp.web.WebClient.include({
        update_logo: function() {
            $(document).ready(function() {
                $("table.oe_webclient tr:first td").css({
                    "visibility": "hidden"
                });
                $("table.oe_webclient tr td.oe_leftbar").css({
                    "height": "100%"
                });
                $("table.oe_webclient tr:eq(2)").css({
                    "position": "relative",
                    "height": "100%"
                });
                $("<tr><td colspan=\"2\" class=\"oe_topbar\" style=\"position:fixed;z-index:6;\"><div class=\"oe_menu_placeholder\" /><div class=\"oe_user_menu_placeholder\"/><div class=\"oe_systray\"/></td></tr>").insertBefore("table.oe_webclient tr:first");
                $("<div class=\"fullscreen\" valign=\"top\">Full Screen</div>").insertBefore("table.oe_webclient tr td.oe_leftbar a");
                $("div.fullscreen").hide();
                //$("div.fullscreen").fadeIn(1200);
                $("div.fullscreen").delay(2000).animate({
                    opacity: '0.001',
                    });
                $("div.fullscreen,div.fullscreentrue").mouseenter(function() {
                    $("div.fullscreen,div.fullscreentrue").animate({
                        opacity: '0.001',
                        });
                });
                $("div.fullscreen,div.fullscreentrue").mouseleave(function() {
                    $("div.fullscreen,div.fullscreentrue").animate({
                        opacity: '0.001',
                        });
                });
                var toggle = 0;

                $("div.fullscreen,div.fullscreentrue").click(function() {
                    if (toggle == 0) {
                        $("a.oe_logo").slideToggle("slow");
                        $("div.oe_secondary_menus_container").slideToggle("slow");
                        $("div.oe_footer").slideToggle("slow");
                        $("td.oe_topbar").delay(500).slideToggle("normal");
                        toggle = 1;
                        fullscreen_toggle.fullscreen_toggle = 1;
                        if (fullscreen_toggle.search==1)
                        {
                        $('div.oe_searchview').delay(500).animate({
                            "top": "0px"
                        });
                        }
                        $("div.fullscreen").addClass("fullscreentrue");
                        $("div.fullscreentrue").hide();
                        $("div.fullscreentrue").removeClass("fullscreen");
                        $("div.fullscreentrue").html("Exit Full Screen");
                        //$("div.fullscreentrue").delay(1000).fadeIn(1600);
                        $("div.fullscreentrue").delay(2000).animate({
                            opacity: '0.001',
                            }, "fast");

                    } else {
                        $("td.oe_topbar").slideToggle("normal");
                        $("a.oe_logo").delay(330).slideToggle("slow");
                        $("div.oe_secondary_menus_container").delay(330).slideToggle("slow");
                        $("div.oe_footer").delay(330).slideToggle("slow");
                        toggle = 0;
                        fullscreen_toggle.fullscreen_toggle = 0;
                        if(fullscreen_toggle.search==1)
                        {
                        $('div.oe_searchview').animate({
                            "top": "32px"
                        });
                        }
                        $("div.fullscreentrue").hide();
                        $("div.fullscreentrue").addClass("fullscreen");
                        $("div.fullscreen").removeClass("fullscreentrue");
                        $("div.fullscreen").html("Full Screen");
                        //$("div.fullscreen").fadeIn(1000);
                        $("div.fullscreen").delay(1600).animate({
                            opacity: '0.001',
                            }, "fast");
                    }
                });
            });
            this._super.apply(this, arguments);
        },
        });

}
