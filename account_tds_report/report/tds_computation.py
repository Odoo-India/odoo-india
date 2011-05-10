
##############################################################################
#    Copyright 2011, SG E-ndicus Infotech Private Limited ( http://e-ndicus.com )
#    Contributors: Selvam - selvam@e-ndicus.com,Karl-karl@e-ndicus.com
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
###############################################################################

import time
import traceback
from report import report_sxw
class order(report_sxw.rml_parse):    
        def __init__(self, cr, uid, name, context):
            super(order, self).__init__(cr, uid, name, context)
            self.localcontext.update({
            'time': time,
            'get_tds':self.get_tds,
            'get_normal_deducted':self.get_normal_deducted,
            'get_normal_deductable':self.get_normal_deductable,
            
            'get_zero_deducted':self.get_zero_deducted,
            'get_zero_deductable':self.get_zero_deductable
        })
        def get_tds(self,kind = 'paid'):
               if kind=='paid':
                   s="NOT NULL"
               elif kind=='unpaid':
                   s="NULL"
               sql =  """select sum(tds_amount) as amount,to_char(aml.date,'MON') as month from account_tds at join account_move_line aml on (at.id=aml.tds_id)
               where aml.reconcile_id is %s group by to_char(aml.date,'MON')"""%(s)                                       
               self.cr.execute(sql)
               c= self.cr.dictfetchall()
               print c,"before tds comp return 18"
               return c
               
        def get_normal_deducted(self):
               print "Get normal deducted"
               try:
                        sql =  """select sum(tds_amount) as amount from account_tds at join account_move_line aml on (at.id=aml.tds_id)
                        where at.state='confirmed' and at.zero='0' """
                        self.cr.execute(sql)
                        c= self.cr.fetchone()[0] or 0.0
               except:
                   traceback.print_exc()
               print c,"before tds comp return normal deducted"
               return c

        def get_zero_deducted(self):
               print "Get normal deducted"
               try:
                        sql =  """select sum(tds_amount) as amount from account_tds at join account_move_line aml on (at.id=aml.tds_id)
                        where at.state='confirmed' and at.zero='1'"""
                        self.cr.execute(sql)
                        c= self.cr.fetchone()[0] or 0.0
               except:
                   traceback.print_exc()
               print c,"before tds comp return normal deducted"
               return c
               
        def get_zero_deductable(self):
               print "Get normal deductable"
               sql =  """select sum(tds_amount) as amount from account_tds at join account_move_line aml on (at.id=aml.tds_id)
               where at.state='later'  and at.zero='1'
                """
               self.cr.execute(sql)
               c= self.cr.fetchone()[0] or 0.0
               print c,"before tds comp deductable"
               return c
               
        def get_normal_deductable(self):
               print "Get normal deductable"
               sql =  """select sum(tds_amount) as amount from account_tds at join account_move_line aml on (at.id=aml.tds_id)
               where at.state='later'  and at.zero='0'
                """
               self.cr.execute(sql)
               c= self.cr.fetchone()[0] or 0.0
               print c,"before tds comp deductable"
               return c
               
report_sxw.report_sxw('report.account.tds.computation', 'account.account',
'addons/account_tds_report/report/tds_compute.rml', parser=order, header=True)



