from openerp.osv import fields, osv
from openerp.tools.translate import _

class datestart_from(osv.osv_memory):
    
    _name = 'datestart.from'
    
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
        print context
        action_model, action_id = tuple(mod_obj.get_object_reference(cr, uid, context.get('model'), context.get('action')))
        action = self.pool.get(action_model).read(cr, uid, action_id, context=context)
        demo = action['context']
        action['context'] = {'date_from':date_from,'date_to':date_to}
        action['context'].update(eval(demo))
        if context.get('action') == 'maize_advance_note_report':
            domain = [('advance_date', '>=', date_from),('advance_date', '<=', date_to)]
        if context.get('action') == 'action_indent_purchase_report':
            domain = [('purchase_date', '>=', date_from),('purchase_date', '<=', date_to)]
        else:
            domain = [
                      ('date', '>=', date_from),
                      ('date', '<=', date_to), 
                     ]
        action['domain'] = domain
        return action

