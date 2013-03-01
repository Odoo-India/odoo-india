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
from dateutil.relativedelta import relativedelta
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler

class indent(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.sr_no = 0
        self.cr = cr
        self.uid = uid
        self.get_value ={}
        super(indent, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
              'time': time, 
              'total_amount': self._get_total, 
              'project_name': self._project_code_name, 
              'last_supplier': self._last_supplier_code_name,
              'indent_no': self._indent_no,
              'sequence': self._serial_no,
              'last_issue': self._last_issue,
              'last_consumption_qty': self._last_consumption_qty,
              'current_consumption_qty': self._current_consumption_qty,
              'check_discount': self._check_dis,
              'get_value': self._get_value,
              'check_tax': self._check_tax,
              'qty': self._qty,
              })
        self.context = context

    def _serial_no(self, line):
        self.sr_no += 1
        return self.sr_no
    
    def _qty(self, qty):
        return int(qty)
    
    def _check_dis(self, line):
        purchase_obj = self.pool.get('purchase.order')
        line = purchase_obj.browse(self.cr, self.uid, line)
        for line_1 in line.order_line:
            self.get_value.update({'discount': line_1.discount})
        return self.get_value
    
    def _check_tax(self,purchase_no, product):
        po_line_obj = self.pool.get('purchase.order.line')
        po_line_id = po_line_obj.search(self.cr, self.uid, [('order_id', '=', purchase_no),('product_id', '=', product)])
        tax_dict = {}
        if po_line_id:
            po_line = po_line_obj.browse(self.cr, self.uid, po_line_id[0])
            for tax in po_line.taxes_id:
                tax_dict.update({str(tax.tax_type): tax.amount * 100})
        return tax_dict
    
    def _last_issue(self, product_id, date):
        stock_obj = self.pool.get('stock.move')
        stock_id = stock_obj.search(self.cr, self.uid, [('product_id', '=', product_id.id), ('type', '=', 'internal'),('state', '=', 'done'), ('create_date', '<=', date)])
        stock_id = sorted(stock_id,reverse=True)
        if stock_id and len(stock_id) >= 2:
            pick = stock_obj.browse(self.cr, self.uid, stock_id[1])
            self.get_value.update({'date': pick.picking_id.date.split(' ')[0], 'department' : pick.location_dest_id.name})
        elif stock_id:
            pick = stock_obj.browse(self.cr, self.uid, stock_id[0])
            self.get_value.update({'date': pick.picking_id.date.split(' ')[0], 'department' : pick.location_dest_id.name})
        return self.get_value

    def _last_consumption_qty(self, product_id):
        last_year = str(datetime.now() - relativedelta(years=1)).split('-')[0]
        current_year = str(datetime.now()).split('-')[0]
        res = {}
        stock_obj = self.pool.get('stock.move')
        stock_id = stock_obj.search(self.cr, self.uid, [('product_id', '=', product_id.id), ('type', '=', 'out'),('state', '=', 'done'), ('create_date', '<=', '03-31-'+ current_year),('create_date', '>=', '04-01-'+ last_year)])
        consume_qty = 0.0
        if stock_id:
            for id in stock_id:
                stock_data = stock_obj.browse(self.cr, self.uid, id)
                consume_qty += stock_data.product_qty
            res.update({'last_year_qty': consume_qty})
        return res
    
    def _get_value(self):
        return self.get_value

    def _current_consumption_qty(self, product_id):
        next_year = str(datetime.now() + relativedelta(years=1)).split('-')[0]
        current_year = str(datetime.now()).split('-')[0]
        res = {}
        stock_obj = self.pool.get('stock.move')
        stock_id = stock_obj.search(self.cr, self.uid, [('product_id', '=', product_id.id), ('type', '=', 'out'),('state', '=', 'done'), ('create_date', '<=', '03-31-'+ next_year),('create_date', '>=', '04-01-'+ current_year)])
        consume_qty = 0.0
        if stock_id:
            for id in stock_id:
                stock_data = stock_obj.browse(self.cr, self.uid, id)
                consume_qty += stock_data.product_qty
            res.update({'current_year_qty': consume_qty})
        return res

    def _indent_no(self, name):
        no = name.split('/')
        return no[len(no)-1]

    def _get_total(self, id):
        total =  0.0
        for line in id.product_lines:
            if line.product_id and line.product_id.last_supplier_rate:
                total += (line.product_uom_qty * line.product_id.last_supplier_rate )
            else:
                total += 0.0
        return total

    def _project_code_name(self, project_id):
        code = ''
        if project_id:
            code = (project_id.code or '') +'  '+ project_id.name or ''
        return code
    
    def _last_supplier_code_name(self, id):
        code = ''
        if id:
            code = (id.ref or '')+' '+ id.name or ''
        return code

report_sxw.report_sxw('report.indent.indent','indent.indent','addons/indent/report/indent.rml',parser=indent, header='internal landscape')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

