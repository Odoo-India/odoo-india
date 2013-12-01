# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _

class res_partner(osv.osv):
    _inherit = 'res.partner'
    _columns = {
        'member': fields.boolean('Member', help="If checked, this is member partner."),
        'sex':fields.selection([('male','Male'), ('female','Female')], 'Sex'),
        'educaion_ids': fields.one2many('res.partner.history', 'partner_edu_id', 'Education', domain=[('type','=','Education')]),
        'professional_ids': fields.one2many('res.partner.history', 'partner_pro_id', 'Professional', domain=[('type','=','Professional')])
    }
    
    _defaults = {
        'sex':'male',
        'member':True
    }
    
    def write(self, cr, uid, ids, vals, context):
        res = False
        allow_users = [
            1
        ]
        member_id = self.pool.get('res.users').browse(cr, uid, uid).partner_id.id
        if uid in allow_users or member_id in ids:
            res = super(res_partner, self).write(cr, uid, ids, vals, context)
        else:
            raise osv.except_osv(_('Error!'),_('You are not allows to change details of other member !'))
        return res

res_partner()

class res_member_education(osv.osv):
    _name = 'res.partner.history'
    
    _columns = {
        'orginazation_id':fields.many2one('res.partner', 'Company Name', domain=[('is_company','=',True)]),
        'name': fields.char('Job Position', size=256),
        'start_date': fields.date('Join Date'),
        'end_date': fields.date('Left on'),
        'current_position':fields.boolean('Current Position'),
        'note': fields.text('Additional Notes'),
        'type': fields.selection([('Education', 'Education'), ('Professional', 'Professional')], 'Type'),
        'partner_edu_id':fields.many2one('res.partner', 'Partner'),
        'partner_pro_id':fields.many2one('res.partner', 'Partner'),
        
        'city': fields.char('City', size=128),
        'state_id': fields.many2one("res.country.state", 'State'),
        'country_id': fields.many2one('res.country', 'Country')
    }
    
    def _default_type(self, cr, uid, context=None):
        return context.get('type')
    
    def _default_current_position(self, cr, uid, context=None):
        res = True
        if context.get('type') == 'Education':
            res = False
        return res
    
    _defaults = {
        'type':_default_type,
        'current_position':_default_current_position
    }
res_member_education()