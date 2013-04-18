openerp.web_report_small = function(instance) {
var _t = instance.web._t;
var QWeb = instance.web.qweb;
    instance.web.WebClient.include({
        show_application:function(){
            this.bind_report();
            return this._super.apply(this, arguments);
        },
        bind_report:function(){
          var self = this;
          $(document).keydown(function(e){
            if(e.ctrlKey && e.which === 80){
                e.preventDefault();
                var widget = self.action_manager.inner_widget;
                var bool = self.$el.find('.oe_view_manager_current .oe_searchview');
                var final_val = {
                    "q": [],
                    "w":[],
                }
                var final_show = {
                    "q":"Filter On :",
                    "w":"Group by :",
                }
                if(bool.is(":visible")){
                    _.each(bool.find('.oe_facet_category'),function(el){
                        var content = $(el).html().trim();
                        var next = $(el).next().children();
                        var temp = []
                        _.each(next,function(con){
                            temp.push($(con).html().trim());
                        })
                       var temp1 = final_val[content];
                         try{
                              final_val[content] = temp1.concat(temp);
                          }
                        catch(err){
                            console.warn("Not showing Advance/Custom Filters");
                          }
                    });
                }
                var para = [];
                _.each(_.keys(final_val),function(kk){
                    var p ;
                    if((final_val[kk]).length){
                         p = final_show[kk] + " ";
                        _.each(final_val[kk],function(key, value){
                             p = p + key
                             if (value != (final_val[kk]).length - 1) p = p + ","
                          })
                    }
                    if(p)para.push(p)
                })
               var notify = '';
               var old_print = window.print;
               if(window.orignal_dirty !== true){
                  window.orignal_dirty = true
                  window.print = function(){
                    old_print();
                    if(notify)notify.close();
                }
               }
               if(para.length){
                    notify= self.do_notify("",QWeb.render("search_report", {'widget':para}));
                    notify.element.find(".ui-notify-close").hide()
               }
               
               var timer = setInterval(function(){
                    window.print();
                    clearInterval(timer)
               },500);
            }
        });
        }
    })
};
