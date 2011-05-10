
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
from osv import fields, osv
from tools.translate import _

class account_month_invoice(osv.osv_memory):
    """
    Closes Account Fiscalyear and Generate Opening entries for New Fiscalyear
    """
    _name = "account.tds.form26"
    _description = "TDS Report"
    _columns = {
       'date_start': fields.date('Start Date'),                        
       'date_end': fields.date('End Date'),
    
    'name_id':fields.many2one("account.tds.deductor","Name of Deductor2",required=True),       
       'date':fields.date('Current Date'),
       'place': fields.char('Place',size=128),       }
    
    def account_tds_report(self, cr, uid, ids, data={},context=None):            
        print "data=",data
        data['form']={}
        data['form'].update(self.read(cr, uid, ids, [], context=context)[0])
        #data = self.pre_print_report(cr, uid, ids, data, context=context)
        return {'type': 'ir.actions.report.xml', 'report_name': 'account.tds.form26','datas':data}


account_month_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
