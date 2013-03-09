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
from openerp.report import report_sxw
from openerp.osv import osv
from openerp import pooler
from openerp.tools import amount_to_text_en as text

class new_po(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        self.sr_no = 0
        self.cr = cr
        self.uid = uid
        self.get_value ={}
        super(new_po, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time, 
                                  'amount_to_word': self._amount_to_word,
                                  'indent_no': self._indent_no,
                                  'tax': self._tax,
                                  'get_value': self._get_value,
                                  'sequence': self._serial_no,})
        
        self.context = context
    
    def _indent_no(self, name):
        if name:
            no = name.split('/')
            return no[len(no)-1]
        else:
            return '-'
    
    def _serial_no(self, line):
        self.sr_no += 1
        return self.sr_no
    
    def _tax(self,order):
        tax_obj = self.pool.get('account.tax')
        excise_tax = vat_tax = ''
        for exc in order.excies_ids:
            excise_tax += exc.name + ' '
        for vat in order.vat_ids:
            vat_tax += vat.name + ' '
        return self.get_value.update({'excise': excise_tax, 'vat': vat_tax})
    
    def _get_value(self):
        return self.get_value
    
    def _amount_to_word(self,order):
        res = {}
        amt_en = text.amount_to_text(order.amount_total, 'en', 'RUPEES')
        return amt_en.replace('Cent', 'Paise').upper() + '(ONLY)'

report_sxw.report_sxw('report.new.purchase.order1','purchase.order','addons/indent/report/new_po.rml',parser=new_po, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

