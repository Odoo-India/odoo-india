from openerp.osv import fields, osv
from openerp.tools.translate import _

class move_analysis_datestart_from(osv.osv_memory):
    
    _name = 'move.analysis.datestart.from'
    
    _columns = {
            'date_from': fields.date('Date From'),
            'date_to': fields.date('Date To')
        }
    
    def get_data(self, cr, uid, ids, context=None):

        mod_obj = self.pool.get('ir.model.data')
        read_rec = self.read(cr, uid, ids[0], context=context)
        browse_rec = self.browse(cr, uid, ids[0], context=context)
        date_from = browse_rec.date_from 
        date_to = browse_rec.date_to 
        if date_from and not date_to or date_to and not date_from:
            raise osv.except_osv(_("Warning !"), _("Enter values in both Date From and Date To."))
        if date_from > date_to:
            raise osv.except_osv(_("Warning !"), _("Date To should be greater than Date From."))
        
        action_model, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'stock', 'action_stock_move_report'))
        action = self.pool.get(action_model).read(cr, uid, action_id, context=context)
        domain = [
                  ('date', '>=', date_from),
                  ('date', '<=', date_to), 
                 ]
            
        action['domain'] = domain
        return action

