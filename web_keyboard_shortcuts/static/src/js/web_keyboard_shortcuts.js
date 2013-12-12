
openerp.web_keyboard_shortcuts = function (openerp) {
		var QWeb = openerp.web.qweb,
		_t = openerp.web._t;
		openerp.web_shortcuts.Shortcuts.include({
			 init: function() {
		            this._super.apply(this, arguments);
		            var old=this;
		            var match=0;
		        	var str ="";
		        	var select=0;
		        	var menu_id=0;
		        	$(document).keyup(function(event){
		        			if(fullscreen_toggle.menu_dict)
		        				{
		        				var d = event.keyCode;
		        				var pa=$(".oe_searchview_input").html();
		        				for (key in Object.keys(fullscreen_toggle.menu_dict))
		        					{if (pa)
		        						{
		        						if(pa=='<br>')
		        							{
		        							$("div.oe_searchview_clear").click();
		        							break;
		        							}
		        						if (pa.length>0 )
		        						{		pa=pa.replace(/\\/g, "\\\\");
		        								pa=pa.replace(/\(/g, "\\(");
		        								pa=pa.replace(/\)/g, "\\)");
		        								var patt1=new RegExp("^"+pa);
		        								if(patt1.test(Object.keys(fullscreen_toggle.menu_dict)[key]))
		        									{
		        									str = Object.keys(fullscreen_toggle.menu_dict)[key]
		        									var sub = str.substring(pa.length);
		        									$("#search_hint").remove();
		        									$(".oe_searchview_input").append('<div id="search_hint" style="color:#898585">'+sub+"</div>");
		        									match=1;
		        									}
		        							}
		        						}
		        					
		        					}
		        		      }
		                  if(d==39 && match==1)
		                  {
		                	  $(".oe_searchview_input").trigger("paste");
		                	  match=0;
		                	  select=1;
		                	  menu_id=fullscreen_toggle.menu_dict[str];
		                  }
		                  if(d==37 || d==8)
		                  {   
		                	  event.preventDefault();
		                	  match=0;
		                	  select=0;
		                  }
		                  if (fullscreen_toggle.menu_dict){
		                  if(d==13 && select==1 && menu_id)
		                	  {
		                      var self = old,
		                      id = menu_id;
		                      menu_id=0;
			                  self.session.active_id = id;
			                  // TODO: Use do_action({menu_id: id, type: 'ir.actions.menu'})
			                  select=0;
			                  match=0;
			                  self.rpc('/web/menu/action', {'menu_id': id}).done(function(ir_menu_data) {
			                      if (ir_menu_data.action.length){
			                          openerp.webclient.on_menu_action({action_id: ir_menu_data.action[0][2].id});
			                      }
			                  });
		                	  }
		                  }
		                  
		                  
		        	});
			 },
			 
		});

};





$(document).ready(function(event) {
	 $(document).keyup(function(event) {
		 $("button u span").unwrap();
	 });
    $(document).keydown(function(event) {
	    	jQuery(".oe_menu").sortable({axis: "x",
			cursor: "move",
		});
    	
    	$("#search_hint").remove();
        var n = String.fromCharCode(event.charCode);
        var d = event.keyCode;
        var alt_dict={}
        if (event.altKey) {
        	$("header button:visible").attr("accesskey",function(index,currentvalue){ 
        																if(currentvalue){
        																	
        																	var button_text = $(this).text();
        																	 $(this).html(button_text.replace(currentvalue,'<u class="alt_base"><span class="under_line">'+currentvalue+'</sapn></u>'));
        																	 alt_dict[currentvalue]=$(this);
        																	 $('.alt_base').addClass("alt_after");
																			}
        															   });
//        	$("button").attr("accesskey",function(index,currentvalue){ 
//				if(currentvalue){
//					
//					var button_text = $(this).text();
//					 $(this).html(button_text.replace(currentvalue,'<u><span class="under_line">'+currentvalue+'</sapn></u>'));
//					 alt_dict[currentvalue]=$(this);
//					 $(this).removeAttr("accesskey");
//					 $(this).attr("acckey",currentvalue);
//					}
//			   });
        	
        }
        
        if (event.keyCode && event.keyCode != 18 && event.altKey) {
        	event.preventDefault();
        	var pressed = String.fromCharCode(event.keyCode);
        	if (alt_dict.hasOwnProperty(pressed)!=false)
        	{
//    		if(alt_dict[pressed].is(":visible"))
//    		{
//    	
//    			alt_dict[pressed].click();
//    		}

        	}
        }
        if (event.keyCode && event.keyCode != 17 && event.ctrlKey) {
            if (d == 83) {
                event.preventDefault();
                var x = document.getElementsByTagName('button');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_button oe_form_button_save oe_highlight" && $(y).is(':visible')) {
                        y.click();
                    }
                }
            }

            if (d == 75) {

                event.preventDefault();
                var x = document.getElementsByTagName('a');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_vm_switch_kanban") {
                        y.click();
                    }
                }

            }

            if (d == 222) {

                event.preventDefault();
                var x = document.getElementsByTagName('a');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_vm_switch_graph") {
                        y.click();
                    }
                }

            }

            if (d == 70) {

                event.preventDefault();
                var x = document.getElementsByTagName('div');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_searchview_facets") {
                        y.click();
                        if(fullscreen_toggle.fullscreen_toggle)
                        	{
                        	$('div.oe_searchview').animate({
                                "top": "0px"
                            },"fast");
                        	fullscreen_toggle.search=1;
                        	}
                        	else{
	                        $('div.oe_searchview').animate({
	                            "top": "32px"
	                        },"fast");
	                        fullscreen_toggle.search=1;
	                        }
                        $("div.oe_searchview").animate({
                            opacity: '1',
                            }, "fast");
                       
                    }
                }
            }
            if (d == 68) {
            	event.preventDefault();
            	
            	if(fullscreen_toggle.fullscreen_toggle)
            	{
            	$('div.oe_searchview').animate({
                    "top": "-32px"
                },"fast");
            	fullscreen_toggle.search=0;
            	}
            	else{
            		$('div.oe_searchview').animate({
                        "top": "0px"
                    },"fast");
            		fullscreen_toggle.search=0;	
            	}
            }
            
            if (d == 76) {

                event.preventDefault();
                var x = document.getElementsByTagName('a');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_vm_switch_list") {
                        y.click();
                    }
                }
            }

            if (d == 27) {

                event.preventDefault();
                var x = document.getElementsByTagName('a');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_bold oe_form_button_cancel" && $(y).is(':visible')) {
                        y.click();
                    }
                }

            }

            if (d == 186 | d == 59) {

                event.preventDefault();
                var x = document.getElementsByTagName('a');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_vm_switch_form") {
                        y.click();
                    }
                }

            }

            if (d == 32) {

                event.preventDefault();
                var x = document.getElementsByTagName('button');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if ((y.className == "oe_button oe_list_add oe_highlight" | y.className == "oe_kanban_button_new oe_highlight" | y.className == "oe_button oe_form_button_create") && $(y).is(':visible')) {
                        y.click();
                    }

                }

            }
           
            if (d == 187) {

                event.preventDefault();
                var x = document.getElementsByTagName('button');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    alert(d);
                    if (y.className == "oe_button oe_form_button_edit") {
                        //y.click();
                    }
                }
            }
            if (d == 69) {

                event.preventDefault();
                var x = document.getElementsByTagName('button');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_button oe_form_button_edit") {
                        y.click();
                    }
                }
            }

            if (d == 40) {

                event.preventDefault();
                var x = document.getElementsByTagName('span');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "ui-icon ui-icon-triangle-1-e") {
                        y.click();
                    }
                }
            }

            if (d == 38) {

                event.preventDefault();
                var x = document.getElementsByTagName('span');
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "ui-icon ui-icon-triangle-1-s") {
                        y.click();
                    }
                }
            }

//            if (d == 80) {
            	
//            	$('.oe_leftbar').remove();
//            	$('colgroup').remove();
//            	$('.oe_topbar').remove();
//            	$('.oe_loading').remove();
//            	$('tfoot').remove();
//            	$('ul').remove();
//            	$('.oe_notification.ui-notify').remove();
//            	$('.oe_view_manager_view_kanban').remove();
//            	$('tr.oe_header_row:eq(1)').remove();
//            	$('.oe_view_manager_view_search').remove();
//            	var _elementClone = $(".oe_view_manager.oe_view_manager_current").clone(); 
//            	$(".oe_view_manager.oe_view_manager_current").remove();
//            	$("body").prepend(_elementClone);
//            	$("table.oe_webclient").removeClass();
//            	$("td.oe_application").removeClass();
//            }
            
            if (d == 80) {


                event.preventDefault();
                var x = document.getElementsByTagName('div');
                var list = 0;
		var form = 0;
		var check = 0;
		$('.oe_form_sheet').each(function() {
                    if ($(this).parents('div:hidden').length == 0) {
                        form=1;
                    }
		    else {
			form=0;
			check = 0	
			}
                });
		$('.oe_view_manager_view_graph').each(function() {
                    if ($(this).parents('div:hidden').length == 0) {
                        form=1;
                    }
		    else {
			form=0;
			check = 0	
			}
                });
		$('.oe_list_content').each(function() {
                    if ($(this).parents('div:hidden').length == 0) {
                        list=1;
                    }
                });
                for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if ((y.className == "oe_form_sheet oe_form_sheet_width" | y.className == "oe_semantic_html_override editor-render oe_view") & form==1) {
			if ($(y).parents('div:hidden').length == 0) {
                        	check=1;
                    		}
			else continue;
			
			var logo_url =  $('a.oe_logo').children("img").attr("src");
			var add_img = '<img src="'+logo_url+'" class="sheet_logo"/>'
			var graph_img = '<img src="'+logo_url+'" style="padding:10px;padding-bottom:0px" class="sheet_logo"/>'
			var hr='<hr class="sheet_logo" style="border: 2;width: 100%;margin-bottom:25px"/>'
			$('.oe_form_sheet').prepend(hr);
			$('.oe_form_sheet').prepend(add_img);
			$('.oe_semantic_html_override.editor-render.oe_view').prepend(hr);
			$('.oe_semantic_html_override.editor-render.oe_view').prepend(graph_img);
                        html2canvas(y, {
                            onrendered: function(canvas) {
                                myWindow = window.open('', '', 'width='+window.innerWidth+',height='+window.innerHeight);
                                var strDataURI = canvas.toDataURL();
                                var link = document.createElement("img");
                                link.setAttribute("src", strDataURI);
                                link.setAttribute("id", "embedImage");
                                var linkText = document.createTextNode("Click me");
                                link.appendChild(linkText);

                                var openerp_img = document.createElement("img");
                                openerp_img.setAttribute("class", "open");
                                openerp_img.setAttribute("src", logo_url);
                                var openerp_imgText = document.createTextNode("Click me");
                                openerp_img.appendChild(openerp_imgText);

                                var css = document.createElement("style");
                                var cssText = document.createTextNode(".css3button {margin-left:37%;margin-top:2%;font-family: Arial, Helvetica, sans-serif;font-weight:700;font-size: 14px;color: #c2c0c2;padding: 10px 20px;background: -moz-linear-gradient(top,#302e30 0%,#000000);background: -webkit-gradient(linear, left top, left bottom, from(#302e30),to(#000000));-moz-border-radius: 1px;-webkit-border-radius: 1px;border-radius: 1px;border: 1px solid #000000;-moz-box-shadow:0px 1px 3px rgba(000,000,000,0.5),inset 0px 0px 1px rgba(255,255,255,0.6);-webkit-box-shadow:0px 1px 3px rgba(000,000,000,0.5),inset 0px 0px 1px rgba(255,255,255,0.6);box-shadow:0px 1px 3px rgba(000,000,000,0.5),inset 0px 0px 1px rgba(255,255,255,0.6);text-shadow:0px -1px 0px rgba(000,000,000,1),0px 1px 0px rgba(184,180,184,0.2);}body{background-color:#252525;}img{margin-left:10%;margin-top:2%;}.open{margin-left:35%;margin-top:1%;}");
                                css.appendChild(cssText);

                                var input = document.createElement("input");
                                var inputText = document.createTextNode("a");
                                input.appendChild(inputText);
                                input.setAttribute("id", "saveImage");
                                input.setAttribute("onclick", "download()");
                                input.setAttribute("type", "button");
                                input.setAttribute("class", "css3button");
                                input.setAttribute("value", "Download Png");

                                var jscript = document.createElement("script");
                                jscript.setAttribute("type", "text/javascript");
                                var jscriptText = document.createTextNode("function download(){var img = document.getElementById('embedImage');var button = document.getElementById('saveImage');window.location.href = img.src.replace('image/png', 'image/octet-stream');}");
                                jscript.appendChild(jscriptText);

                                myWindow.document.head.appendChild(css);
                                myWindow.document.head.appendChild(jscript);
                                //myWindow.document.body.appendChild(canvas);
                                myWindow.document.body.appendChild(openerp_img);
                                myWindow.document.body.appendChild(link);
                                myWindow.document.body.appendChild(input);
                                myWindow.focus();
                                $(".sheet_logo").remove();
                            }
                        });

                    }
                }

                if (list == 1 & check==0) {
                    var x = document.getElementsByTagName('table');
                    for (i = 0; i < x.length; i++) {
                        y = x[i];
                        if (y.className == "oe_list_content") {
			if ($(y).parents('div:hidden').length == 0) {
                        	
                    		}
			else continue;
			var logo_url =  $('a.oe_logo').children("img").attr("src");
                            html2canvas(y, {
                                onrendered: function(canvas) {
                                    myWindow = window.open('', '', 'width=950,height=680');
                                    var strDataURI = canvas.toDataURL();

                                    var link = document.createElement("img");
                                    link.setAttribute("src", strDataURI);
                                    link.setAttribute("id", "embedImage");
                                    var linkText = document.createTextNode("Click me");
                                    link.appendChild(linkText);

                                    var openerp_img = document.createElement("img");
                                    openerp_img.setAttribute("class", "open");
                                    openerp_img.setAttribute("src", logo_url);
                                    var openerp_imgText = document.createTextNode("Click me");
                                    openerp_img.appendChild(openerp_imgText);

                                    var css = document.createElement("style");
                                    var cssText = document.createTextNode(".css3button {margin-left:37%;margin-top:2%;font-family: Arial, Helvetica, sans-serif;font-weight:700;font-size: 14px;color: #c2c0c2;padding: 10px 20px;background: -moz-linear-gradient(top,#302e30 0%,#000000);background: -webkit-gradient(linear, left top, left bottom, from(#302e30),to(#000000));-moz-border-radius: 1px;-webkit-border-radius: 1px;border-radius: 1px;border: 1px solid #000000;-moz-box-shadow:0px 1px 3px rgba(000,000,000,0.5),inset 0px 0px 1px rgba(255,255,255,0.6);-webkit-box-shadow:0px 1px 3px rgba(000,000,000,0.5),inset 0px 0px 1px rgba(255,255,255,0.6);box-shadow:0px 1px 3px rgba(000,000,000,0.5),inset 0px 0px 1px rgba(255,255,255,0.6);text-shadow:0px -1px 0px rgba(000,000,000,1),0px 1px 0px rgba(184,180,184,0.2);}body{background-color:#252525;}img{margin-left:10%;margin-top:2%;}.open{margin-left:35%;margin-top:1%;}");
                                    css.appendChild(cssText);

                                    var input = document.createElement("input");
                                    var inputText = document.createTextNode("a");
                                    input.appendChild(inputText);
                                    input.setAttribute("id", "saveImage");
                                    input.setAttribute("onclick", "download()");
                                    input.setAttribute("type", "button");
                                    input.setAttribute("class", "css3button");
                                    input.setAttribute("value", "Download Png");

                                    var jscript = document.createElement("script");
                                    jscript.setAttribute("type", "text/javascript");
                                    var jscriptText = document.createTextNode("function download(){var img = document.getElementById('embedImage');var button = document.getElementById('saveImage');window.location.href = img.src.replace('image/png', 'image/octet-stream');}");
                                    jscript.appendChild(jscriptText);

                                    myWindow.document.head.appendChild(css);
                                    myWindow.document.head.appendChild(jscript);
                                    //myWindow.document.body.appendChild(canvas);
                                    myWindow.document.body.appendChild(openerp_img);
                                    myWindow.document.body.appendChild(link);
                                    myWindow.document.body.appendChild(input);
                                    myWindow.focus();

                                }
                            });
                        }
                    }
                }

            }

            if (d == 8) {

                event.preventDefault();
                var x = document.getElementsByTagName('a');
                f_list = []
                    for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "oe_breadcrumb_item") {
                        f_list.push(y);
                    }

                }
                x = f_list.pop();
                if (x) {
                    x.click();
                }
            }
            if (d == 122) {

                event.preventDefault();
                var x = document.getElementsByTagName('div');
                f_list = []
                    for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "fullscreen") {
                        y.click();
                        if(fullscreen_toggle.search==0)
                        	{
                        	$('div.oe_searchview').delay(500).animate({
                                "top": "-32px"
                            },"fast");
                        	
                        	}
                    }

                }

            }

            if (!fullscreen_toggle.fullscreen_toggle) {
                if (d == 49 | d == 50 | d == 51 | d == 52 | d == 53 | d == 54 | d == 55 | d == 56 | d == 57) {

                    event.preventDefault();
                    n = d - 48;
                    var x = document.getElementsByTagName('a');
                    for (i = 0; i < x.length; i++) {
                        y = x[i];
                        if (y.className == "oe_menu_toggler") {
                            if (n == i + 1) {
                                y.click();
                            }
                        }

                    }
                }
            }

            if (d == 188) {
                event.preventDefault();
                $('.oe_i[data-pager-action="previous"]').each(function() {
                    if ($(this).parents('div:hidden').length == 0) {
                        $(this).trigger('click');
                    }
                });
            }
            if (d == 190) {
                event.preventDefault();
                $('.oe_i[data-pager-action="next"]').each(function() {
                    if ($(this).parents('div:hidden').length == 0) {
                        $(this).trigger('click');
                    }
                });
            }

        }

        if (d == 192) {
            if (event.ctrlKey == 1) {
                event.preventDefault();
                $("div ul li a.oe_menu_leaf:visible:first").focus();
            }

        }

        if (d == 40) {
            for (i = 0; i < $("div ul li a.oe_menu_leaf:visible").length; i++) {
                if ($("div ul li a.oe_menu_leaf:visible:eq(" + i + ")").is(":focus")) {
                    event.preventDefault();
                    var flg = i + 1;
                    $("div ul li a.oe_menu_leaf:visible:eq(" + flg + ")").focus();
                    break;
                }

            }
        }
        if (d == 38) {
            var flg = 0;
            for (i = 0; i < $("div ul li a.oe_menu_leaf:visible").length; i++) {
                if ($("div ul li a.oe_menu_leaf:visible:eq(" + i + ")").is(":focus")) {
                    event.preventDefault();
                    var flg = i - 1;
                    $("div ul li a.oe_menu_leaf:visible:eq(" + flg + ")").focus();
                    break;
                }

            }
        }

        if (event.ctrlKey != 1) {
            if (d == 27) {
                event.preventDefault();
                var x = document.getElementsByTagName('div');
                f_list = []
                    for (i = 0; i < x.length; i++) {
                    y = x[i];
                    if (y.className == "fullscreentrue") {
                        y.click();
                        if(fullscreen_toggle.search==0)
                    	{
                        	$('div.oe_searchview').delay(500).animate({
                                "top": "0px"
                            },"fast");
                    	
                    	}
                    }

                }

            }
        }

    });
});
