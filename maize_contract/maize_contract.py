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

class indent_indent(osv.Model):
    _inherit = 'indent.indent'
    _columns = {
        'contract': fields.boolean('Contract', help="Check box True means the contract otherwise it is indent"),
        'contract_series_id': fields.many2one('contract.series','Contract Series', help="contract_series", readonly=True, states={'draft': [('readonly', False)]}),
        'indent_section_id': fields.many2one('indent.section','Section', help="Indent Section", readonly=True, states={'draft': [('readonly', False)]}),
        'indent_equipment_id': fields.many2one('indent.equipment','Equipment', help="Indent Equipment", readonly=True, states={'draft': [('readonly', False)]}),
        }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if context is None: 
            context = {}
        res = super(indent_indent, self).fields_view_get(cr, user, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//div[@name='buttons']/button[@string='Enquiry']")
        if context.get('search_default_contract_contract'):
            if 'product_lines' in res['fields'].keys() and 'product_id' in res['fields']['product_lines']['views']['form']['fields'].keys():
               domain = [('type','=', 'service')]
               res['fields']['product_lines']['views']['form']['fields']['product_id']['domain'] = domain
            for node in nodes:
                node.set('modifiers','{"invisible":true}')
        res['arch'] = etree.tostring(doc)
        return res

#    def indent_confirm(self, cr, uid, ids, context=None):
#        for record in self.browse(cr,uid,ids,context):
#            if record.contract:
#                sequence = '/'
#                if record.contract_series_id.code == 'MS':
#                    sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.ms')
#                elif record.contract_series_id.code == 'PR':
#                    sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.pr')
#                elif record.contract_series_id.code == 'OM':
#                    sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.om')
#                elif record.contract_series_id.code == 'TM':
#                    sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.tm')
#                self.write(cr,uid,record.id,{'name':sequence})
#            else:
#                sequence = self.pool.get('ir.sequence').get(cr, uid, 'indent.indent') or '/'
#                self.write(cr,uid,record.id,{'name':sequence})
#        return super(indent_indent, self).indent_confirm(cr, uid, ids, context)
    
    def create(self, cr, uid, vals, context=None):
        co_series = self.pool.get('contract.series')
        if vals.get('contract'):
            co = co_series.browse(cr,uid,vals['contract_series_id']).code
            if co == 'MS':
                sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.ms')
            elif co == 'PR':
                sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.pr')
            elif co == 'OM':
                sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.om')
            elif co == 'TM':
                sequence = self.pool.get('ir.sequence').get(cr, uid, 'contract.tm')
        else:
            sequence = self.pool.get('ir.sequence').get(cr, uid, 'indent.indent')
        vals['name']=sequence
        result = super(indent_indent, self).create(cr, uid, vals, context=context)
        return result
    _defaults = {
        'contract': False
        }
    
indent_indent()

class contract_series(osv.Model):
    _name = 'contract.series'
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
contract_series()

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

    def onchange_compute_days1(self, cr, uid, ids, date_from, date_to,d1=0,d2=0):
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
            result['value']['total_days'] = d1+d2

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days1'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = d1+d2+round(math.floor(diff_day))+1
        else:
            result['value']['no_of_days1'] = 0

        return result
    
    def onchange_compute_days2(self, cr, uid, ids, date_from, date_to,d1=0,d2=0):
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
            result['value']['total_days'] = d1+d2

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days2'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2
        else:
            result['value']['no_of_days2'] = 0

        return result
    
    def create(self,cr,uid,vals,context):
        if not vals.get('indent_id') and vals.get('po_series_id'):
            series = self.pool.get('product.order.series').browse(cr,uid,vals.get('po_series_id'))
            c_data = {'company_id':1,'po_series_id':series.id}
            if not self.pool.get('ir.sequence').search(cr,uid,[('name','=',series.code)]):
                seqq = self.pool.get('indent.indent').create_series_sequence(cr,uid,c_data,context)
            po_seq = self.pool.get('ir.sequence').get(cr, uid, series.code) or '/'
            vals['name'] = po_seq
        return super(purchase_order, self).create(cr, uid, vals,context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if ids:
            record = self.browse(cr,uid,ids)[0]
            if (vals.get('po_series_id') and record.indent_id.contract) or not record.indent_id:
                series = self.pool.get('product.order.series').browse(cr,uid,vals.get('po_series_id'))
                if series:
                    c_data = {'company_id':1,'po_series_id':series.id}
                    if not self.pool.get('ir.sequence').search(cr,uid,[('name','=',series.code)]):
                        seqq = self.pool.get('indent.indent').create_series_sequence(cr,uid,c_data,context)
                    po_seq = self.pool.get('ir.sequence').get(cr, uid, series.code) or '/'
                    vals['name'] = po_seq
        return super(purchase_order, self).write(cr, uid, ids, vals, context=context)

    def onchange_compute_days3(self, cr, uid, ids, date_from, date_to,d1=0,d2=0):
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
            result['value']['total_days'] = d1+d2

        # Compute and update the number of days
        if (date_to and date_from) and (date_from <= date_to):
            diff_day = self._get_number_of_days(date_from, date_to)
            result['value']['no_of_days3'] = round(math.floor(diff_day))+1
            result['value']['total_days'] = round(math.floor(diff_day))+1+d1+d2
        else:
            result['value']['no_of_days3'] = 0

        return result       
    
    _columns = {
        'contract': fields.related('indent_id', 'contract', type='boolean', relation='indent.indent', string='Contract', store=True, readonly=True),
        'no_of_days1': fields.integer("No of Days1", help="Calculate number of days for contracts"),
        'no_of_days2': fields.integer("No of Days2", help="Calculate number of days for contracts"),
        'no_of_days3': fields.integer("No of Days3", help="Calculate number of days for contracts"),
        'total_days': fields.integer("Total Days", help="Calculate number of days for contracts"),
        'date_from': fields.date('From Date', required=True),
        'date_to': fields.date('To Date'),
        'extended_date_from1': fields.date('Extended From'),
        'extended_date_from2': fields.date('Extended From'),
        'extended_date_to1': fields.date('Extended Upto'),
        'extended_date_to2': fields.date('Extended Upto'),
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
indent_equipment()
