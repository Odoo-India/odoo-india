
openerp.web_mail_img = function (openerp) {
		var QWeb = openerp.web.qweb,
		_t = openerp.web._t,
		_lt = openerp.web._lt;
		openerp.mail.MessageCommon.include({
			display_attachments: function() {
				this._super.apply(this, arguments);
				$('div.oe_attachment.oe_preview a').addClass("zoomIt");
		    	img_no=$('div.oe_attachment.oe_preview a').size();
		    	for(i=0;i<img_no;i++)
		    		{   
		    			$('div.oe_attachment.oe_preview a:eq('+i+')').addClass("zoom_img"+i);
		    			jQuery('.zoom_img'+i).jqZoomIt({
		    				zoomDistance : 10,
		    				multiplierX	: 6, 
		    				multiplierY	: 3});
		    		}
			}
			
		});
};

