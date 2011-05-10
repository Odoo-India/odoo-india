
##############################################################################
#    Copyright 2011, SG E-ndicus Infotech Private Limited ( http://e-ndicus.com )
#    Contributors: Selvam - selvam@e-ndicus.com
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

from osv import fields, osv
from tools.translate import _

class account_month_invoice(osv.osv_memory):
    """
    Closes Account Fiscalyear and Generate Opening entries for New Fiscalyear
    """
    _name = "account.tds.helper"
    _description = "TDS Payment Helper"
    _columns = {
       'date': fields.date('Deducted Till Date'),                        
       'section_id': fields.many2one('account.tds.section',"Section"),
       'tds_nature_id': fields.many2one('account.tds.nature',"Nature of Payment",required=True),
       'deductee_status': fields.selection([('company','Company'),('noncompany','Non-Company')],"Section"),
       'account_id': fields.many2one('account.account',"Account",required=True),
       'period_id': fields.many2one('account.period', 'Period',required=True),
       'journal_id': fields.many2one('account.journal', 'Journal',required=True)
    }
    
    def account_create_voucher(self, cr, uid, ids,context=None):            
        vouch = self.pool.get("account.voucher")
        vouch_line = self.pool.get("account.voucher.line")
        part_obj = self.pool.get("res.partner")
        data = self.read(cr, uid, ids, [], context=context)[0]
        #data['form'].update(self.read(cr, uid, ids, [], context=context)[0])
        #Create invoice here, get all tds line mactchin
        date_str=""
        if data['date']:
            date_str = " and aml.date<='%s' "%(data['date'])
        sql = """
        select aml.id as move_line_id,aml.account_id,aml.credit as amount,'dr' as type from account_move_line aml 
        join account_tds tds on (aml.tds_id= tds.id)
        where tds_id is NOT NULL and debit=0
        and tds.tds_nature_id =  %s  and aml.reconcile_id is NULL     
        %s
        """%(data['tds_nature_id'],date_str)
        #join account_tds_nature nat on (tds.nature_id=nat.id)
        cr.execute(sql)
        val =  cr.dictfetchall()
        print val,"---aml lines for tds"        
        voucher={}
        voucher['comment']='some comment'
        voucher['account_id']=data['account_id']
        voucher['company_id']=1
        voucher['period_id']=data['period_id']
        voucher['journal_id']=data['journal_id']
        voucher['amount']=0.0
        try:
                voucher['partner_id']=  part_obj.search(cr,uid,[('name','=','GOVT')])[0]
        except:
                raise osv.except_osv(_('Error !'), _('You need to have a supplier with name="GOVT" for encoding TDS against govt. '))
        voucher['state']='draft'        
        voucher['type']='payment'        
        #voucher['number']='NUMBER'        
        voucher['currency_id']=21     
        new = []
        #for ele in val:
        #new.append((0,0,ele))        
        #voucher['line_ids'] = [(6,0,new)]        
        v_id = vouch.create(cr,uid,voucher)        
        print "Voucher id",v_id
        amt=0.0
        for ele in val:
                ele.update({'voucher_id':v_id})
                new.append(vouch_line.create(cr,uid,ele))
                amt += ele['amount']
        vouch.write(cr,uid,[v_id],{'line_ids':[(6,0,new)],'amount':amt})
                
        return {
        'domain': "[('id','in', ["+','.join(map(str,[v_id]))+"])]",
        'name': 'Voucher For TDS',
        'view_type': 'form',
        'view_mode': 'tree,form', 
        'res_model': 'account.voucher',
        'view_id': False,
        'type': 'ir.actions.act_window'
        }


account_month_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
