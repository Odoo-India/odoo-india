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
from tools.amount_to_text_en import amount_to_text

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
                                  'sequence': self._serial_no,
                                  'change_date': self._change_date,
                                  'reset_no': self._reset_serial_no,})
        
        self.context = context
    
    def _indent_no(self, name):
        if name:
            no = name.split('/')
            return no[len(no)-1]
        else:
            return '-'
    
    def _serial_no(self, line):
        self.sr_no += 1
        if line.product_id.ex_chapter:
            self.get_value.update({'excisable': 'NOTE : SUBMIT CENVAT COPY ALONG WITH SUPPLY FOR OUR CENVAT CLAIM'})
        return self.sr_no
    
    def _reset_serial_no(self, line):
        self.sr_no = 0
        return self.sr_no
    
    def _tax(self,order):
        tax_obj = self.pool.get('account.tax')
        excise_tax = vat_tax = service_tax = ''
        for exc in order.excies_ids:
            excise_tax += exc.name + ' '
        for vat in order.vat_ids:
            vat_tax += vat.name + ' '
        for service in order.service_ids:
            service_tax += service.name + ' '
        self.get_value.update({'excise': excise_tax, 'vat': vat_tax,'service': service_tax})
        return self._get_value()
    
    def _get_value(self):
        return self.get_value
    def amount_to_text(self, num):
        list1 = [10000000,100000,1000,100,10]
        dict1 = {1:'One',2:'Two',3:'Three',4:'Four',5:'Five',6:'Six',7:'Seven',8:'Eight',9:'Nine',10:'Ten',
            11:'Eleven',12:'Twelve',13:'Thirteen',14:'Fourteen',15:'Fifteen',16:'Sixteen',17:'Seventeen',18:'Eighteen',19:'Nineteen'}
        dict2 = {2:'Twenty',3:'Thirty',4:'Forty',5:'Fifty',6:'Sixty',7:'Seventy',8:'Eighty',9:'Ninety'}
        dict3 = {10000000:'Crore', 100000:'Lakh' , 1000:'Thousand' , 100:'Hundred' ,10:'Ten'}
        
        str = ""
        while num > 0:
            if num > 99:
                for l in list1:
                    ans = num / l
                    if ans > 0:
                        if ans <= 19:
                            str = str + dict1[ans] + ' ' + dict3[l] + ' '
                            num = num % l
                            break
                        else:
                            ans1 = ans / 10
                            remind = ans % 10
                            if remind == 0:
                                str = str + dict2[ans1] + ' ' + dict3[l] + ' '
                                num = num % l
                                break
                            else:
                                str = str + dict2[ans1] + ' '+ dict1[remind] + ' ' + dict3[l] + ' '
                                num = num % l
                                break
            else:
                if num <= 19:
                    str = str + dict1[num] + ' '
                    num = 0
                    break
                else:
                    remind = num % 10
                    ans = num / 10
                    if remind == 0:
                        str = str + dict2[ans] + ' '
                    else:
                        str = str + dict2[ans] + ' '+ dict1[remind] + ' '
                    num = 0
                    break
        return str
        
    def _amount_to_word(self,amount):
        res = {}
        amount = str(amount).split('.')
        amt_ruppes = ''
        if int(amount[0]) > 0:
            amt_ruppes = 'Rupees '+self.amount_to_text(int(amount[0]))
        amt_paisa = ''
        if int(amount[1]) > 0:
            amt_paisa = ' and '+ self.amount_to_text(int(amount[1]))+' paise'
        amount_in_word = (amt_ruppes+amt_paisa+' only').upper()
        return amount_in_word

    def _change_date(self,order):
        self.cr.execute('select write_date from purchase_order where id=%s', (order,))
        write_date = self.cr.fetchone()[0].split(' ')[0]
        return write_date
report_sxw.report_sxw('report.new.purchase.order1','purchase.order','addons/indent/report/new_po.rml',parser=new_po, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

