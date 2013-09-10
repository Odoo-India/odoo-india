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

import time
from datetime import datetime
import math
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import tools
from lxml import etree

class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    _columns = {
        'person' : fields.integer('Person'),
    }
    
    def _prepare_line_purchase(self,cr,uid,name,procurement, qty, uom_id,price,schedule_date,taxes):
        res = super(procurement_order, self)._prepare_line_purchase(cr, uid, name,procurement, qty, uom_id,price,schedule_date,taxes)
        res.update({'person':procurement.person})
        return res
        
procurement_order()
class indent_indent(osv.Model):
    _inherit = 'indent.indent'
    _columns = {
        'contract': fields.boolean('Contract', help="Check box True means the contract otherwise it is indent"),
        'indent_section_id': fields.many2one('indent.section','Section', help="Indent Section", readonly=True, states={'draft': [('readonly', False)]}),
        'indent_equipment_id': fields.many2one('indent.equipment','Equipment', help="Indent Equipment", readonly=True, states={'draft': [('readonly', False)]}),
        }

    def _prepare_indent_line_procurement(self, cr, uid, indent, line, move_id, date_planned, context=None):
        res = super(indent_indent, self)._prepare_indent_line_procurement(cr, uid, indent, line, move_id, date_planned, context=context)
        res.update({'person':line.person})
        return res

    def indent_confirm(self, cr, uid, ids, context=None):
        for contract_rec in self.browse(cr, uid, ids, context=context):
            if contract_rec.contract and contract_rec.amount_total == 0.0:
                raise osv.except_osv(_("Warning !"), _("Contract amount must be greater than zero."))
        res = super(indent_indent, self).indent_confirm(cr, uid, ids, context=context)
        return True

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: 
            context = {}
        res = super(indent_indent, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        domain = [('state','=', 'done')]
        nodes = doc.xpath("//div[@name='buttons']/button[@string='Enquiry']")
        if context.get('default_contract_contract'):
            if 'product_lines' in res['fields'].keys() and 'product_id' in res['fields']['product_lines']['views']['form']['fields'].keys():
                domain.append(('type','=', 'service'))
                res['fields']['product_lines']['views']['form']['fields']['product_id']['domain'] = domain
        else:
            if 'product_lines' in res['fields'].keys() and 'product_id' in res['fields']['product_lines']['views']['form']['fields'].keys():
                res['fields']['product_lines']['views']['form']['fields']['product_id']['domain'] = domain
        res['arch'] = etree.tostring(doc)
        return res

    _defaults = {
        'contract': False
        }

indent_indent()

class indent_product_lines(osv.Model):
    _inherit = 'indent.product.lines'

    _columns = {
        'person': fields.integer('Person'),
    }

    def onchange_product_id(self, cr, uid, ids, product_id=False, product_uom_qty=0.0, product_uom=False, price_unit=0.0, qty_available=0.0, virtual_available=0.0, name='', analytic_account_id=False, indent_type=False, contract=False, context=None):
        result = {}
        product_obj = self.pool.get('product.product')
        if not product_id:
            return {'value': {'product_uom_qty': 1.0, 'product_uom': False, 'price_unit': 0.0, 'qty_available': 0.0, 'virtual_available': 0.0, 'name': '', 'delay': 0.0}}
        if analytic_account_id:
            if contract == False:
                prod_ids = product_obj.search(cr, uid, [('default_code', '=like', '%s%%' % '0152')], context=context)
                if product_id not in prod_ids:
                    raise osv.except_osv(_("Warning !"), _("You must select a product whose code start with '0152'."))
            else:
                prod_ids = product_obj.search(cr, uid, [('default_code', '=like', '%s%%' % '0192')], context=context)
                if product_id not in prod_ids:
                    raise osv.except_osv(_("Warning !"), _("You must select a product whose code start with '0192'."))

        product = product_obj.browse(cr, uid, product_id, context=context)
        if indent_type and indent_type == 'existing' and product.type != 'service':
            raise osv.except_osv(_("Warning !"), _("You must select a service type product."))
        if not product.seller_ids:
            raise osv.except_osv(_("Warning !"), _("You must define at least one supplier for this product."))
        result['name'] = product_obj.name_get(cr, uid, [product.id])[0][1]
        result['product_uom'] = product.uom_id.id
        result['price_unit'] = product.standard_price
        result['qty_available'] = product.qty_available
        result['virtual_available'] = product.virtual_available
        result['delay'] = product.seller_ids[0].delay
        return {'value': result}

indent_product_lines()

class purchase_order(osv.Model):
    _inherit = 'purchase.order'

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        DATETIME_FORMAT = "%Y-%m-%d"
        from_dt = datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        diff_day = timedelta.days + float(timedelta.seconds) / 86400
        return diff_day

    def onchange_compute_days1(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days1'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days1'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = d1+d2+round(math.floor(diff_day))+1+d3
        else:
            result['value']['no_of_days1'] = 0

        return result
    
    def onchange_compute_days2(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days2'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days2'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2+d3
        else:
            result['value']['no_of_days2'] = 0

        return result

    def onchange_compute_days3(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days3'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days3'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2+d3
        else:
            result['value']['no_of_days3'] = 0

        return result       

    def onchange_compute_days4(self, cr, uid, ids, date_from, date_to,d1=0,d2=0,d3=0):
        """
        If there are no date set for date_to, automatically set one 8 hours later than
        the date_from.
        Also update the number_of_days.
        """
        # date_to has to be greater than date_from
        if (date_from and date_to) and (date_from > date_to):
            raise osv.except_osv(_('Warning!'),_('The start date must be anterior to the end date.'))

        result = {'value': {}}

        # No date_to set so far: automatically compute one 8 hours later
        if date_from and not date_to:
            result['value']['no_of_days4'] = 0
            result['value']['total_days'] = d1+d2+d3

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days4'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2+d3
        else:
            result['value']['no_of_days4'] = 0

        return result
    
    _columns = {
        'contract': fields.related('indent_id', 'contract', type='boolean', relation='indent.indent', string='Contract', store=True, readonly=True),
        'no_of_days1': fields.integer("No of Days1", help="Calculate number of days for contracts"),
        'no_of_days2': fields.integer("No of Days2", help="Calculate Extended number of days 1st time for contracts"),
        'no_of_days3': fields.integer("No of Days3", help="Calculate Extended number of days 2nd time for contracts"),
        'no_of_days4': fields.integer("No of Days4", help="Calculate Extended number of days 2nd time for contracts"),
        'total_days': fields.integer("Total Days", help="Calculate Total number of days for contracts"),
        'date_from': fields.date('From Date', required=True),
        'date_to': fields.date('To Date'),
        'extended_date_from1': fields.date('Extended From'),
        'extended_date_from2': fields.date('Extended From'),
        'extended_date_from3': fields.date('Extended From'),
        'extended_date_to1': fields.date('Extended Upto'),
        'extended_date_to2': fields.date('Extended Upto'),
        'extended_date_to3': fields.date('Extended Upto'),
        'retention': fields.selection([('leived', 'CONTRACTOR\'S RETENTION TO BE LEIVED'),('not_leived', 'CONTRACTOR\'S RETENTION NOT TO BE LEIVED')], "Retention Type"),
        }
    
    _defaults = {
        'date_from': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        }
class indent_section(osv.Model):
    _name = 'indent.section'
    _rec_name = 'code'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res 
    
    _columns = {
        'name': fields.char('Name',size=256),
        'code': fields.char('Code', size=64)
        }
indent_section()

class indent_equipment(osv.Model):
    _name = 'indent.equipment'
    _rec_name = 'code'
    
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res 
    
    _columns = {
        'name': fields.char('Name',size=256),
        'code': fields.char('Code', size=64)
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of an equipment must be unique!')
    ]

indent_equipment()
