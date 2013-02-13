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
        super(new_po, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({'time': time, 'amount_to_word': self._amount_to_word})
        
    def _amount_to_word(self,order):
        res = {}
        amt_en = text.amount_to_text(order.amount_total, 'en', 'RUPEES')
        res[order.id] = amt_en.upper() + '(ONLY)'
        return amt_en

report_sxw.report_sxw('report.new.purchase.order1','purchase.order','addons/indent/report/new_po.rml',parser=new_po)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

