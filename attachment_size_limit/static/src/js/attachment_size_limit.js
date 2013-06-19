openerp.attachment_size_limit = function(openerp) {
    openerp.web.Sidebar.include({
        fetch: function(model, fields, domain, ctx){
                return new openerp.web.Model(model).query(fields).filter(domain).context(ctx).all()
            },
        on_attachment_changed: function(e) {
            var $e = $(e.target);
            var file_node = e.target;
            var file = file_node.files[0];
            //var c = openerp.web.pyeval.eval('context')
            var self = this;
            var old = this;
            var total_att;
            this.$('.oe_form_dropdown_section:eq(1)').each(function() {
            total_att=$(this).find('li').length;
            });
            var loaded = self.fetch('res.users',['name','company_id'],[['id','=',this.session.uid]])
                    .then(function(users){
                     var att_size=self.fetch('res.company',['attachment_size','attachment_num','user_blocked'],[['id','=',users[0].company_id[0]]])
                                    .then(function(company){
                                     attachment_size=company[0].attachment_size;
                                     user_dict={}
                                     for(var i=0; i<company[0].user_blocked.length;i++){user_dict[company[0].user_blocked[i]]="";}
                                     if((old.session.uid in user_dict))
                                     {
                                    	 var msg = _t("You are not allowd to upload. Contact administrator.");
                                    	 openerp.webclient.notification.warn(_t("File upload"), _.str.sprintf(msg,""));
                                    	 return false;
                                     }
                                     if(company[0].attachment_num==0)
                                     {	
                                        var msg = _t("Maximum number of file allowed is not configured contact administrator.");
                                        openerp.webclient.notification.warn(_t("File upload"), _.str.sprintf(msg,""));
                                        return false;
                                     }
                                     if(company[0].attachment_num<total_att)
                                     {
                                        var msg = _t("Maximum file upload limit reached. Only ");
                                        openerp.webclient.notification.warn(_t("File upload"), _.str.sprintf(msg + (company[0].attachment_num) + " files allowed",""));
                                        return false;
                                     }
                                     if (attachment_size == 0){
                                        var msg = _t("Maximum file size is not configured contact administrator.");
                                        openerp.webclient.notification.warn(_t("File upload"), _.str.sprintf(msg,""));
                                        return false;
                                        }
                                     else if(file.size > (attachment_size* 1024 * 1024)) {
                                        var msg = _t("The selected file exceed the maximum file size of %s.");
                                        openerp.webclient.notification.warn(_t("File upload"), _.str.sprintf(msg, attachment_size +" MB"));
                                        return false;
                                        }
                                     if ($e.val() !== '') {
                                         old.$el.find('form.oe_form_binary_form').submit();
                                         $e.parent().find('input[type=file]').prop('disabled', true);
                                         $e.parent().find('button').prop('disabled', true).find('img, span').toggle();
                                         old.$('.oe_sidebar_add_attachment span').text(_t('Uploading...'));
                                         openerp.web.blockUI();
                                        }
                                 });
                        });
            },
    });
};

