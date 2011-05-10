
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
from report import report_sxw
import traceback
import datetime
from tools.amount_to_text_en import amount_to_text
class order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(order, self).__init__(cr, uid, name, context)
        self.company_partner = None
        self.localcontext.update({
        'time': time,
        'get_tds_16':self.get_tds16,
        'getDeductee':self.getDeductee,
        'getCompany':self.getCompany,
        'getAddress':self.getAddress,
        'getDate':self.getDate,
        'getNaturename':self.getNaturename,
	'getDate':self.getDate,
    'amount_to_text':amount_to_text
    
	
        
        })
    def getCompany(self,data):
        print data
        obj=self.pool.get('res.company') 
        try:
            comp=obj.browse(self.cr,self.uid,1)
            print comp.partner_id.name,"---pname"
            self.company_partner =  comp.partner_id
        except:
            traceback.print_exc()      
        return comp
    def getDate(self,date):
        do = datetime.datetime.strptime(date,"%Y-%m-%d")
        return datetime.datetime.strftime(do,"%d-%b-%Y")  #same as do.strftime("%d-%b-%Y")
                
    def getAddress(self,data):
        try:
            obj = self.company_partner.address[0]
            st = obj.street
            city = obj.city
            return [st,city]
        except:
            traceback.print_exc()      
        return ["ERROR","ERROR"]
    
            
        
    def getDeductee(self,data,type='normal'):
        
        print data

        try:
            obj = self.pool.get('res.partner')
            record = obj.browse(self.cr,self.uid,data['form']['partner_id'])
            if type=='object':
                return record
            obj = record.address[0]
            name=  record.name
            st = obj.street
            city = obj.city
            state= obj.state_id and obj.state_id.name or ''
            return [name,st,city,state]
        except:
            traceback.print_exc()
        return record.name

    def getNaturename(self,data):
        try:
            print data
            obj=self.pool.get('account.tds.nature')
            nature=obj.browse(self.cr,self.uid,data['form']['tds_nature_id'])
            print nature,"--nature"
        except:
            print "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
            traceback.print_exc()
            return "ERROR"
            
        return [nature.tds_section_id.name,nature.name]
        
    def get_tds16(self,data):
            date_str=""
            if data['form']['date_start'] and data['form']['date_end']:
                date_str = " and aml.date>='%s' and aml.date<='%s' "%(data['form']['date_start'],data['form']['date_end'])
            #TODO:date constraint need to be added
            try:
                    part = self.pool.get('res.partner')
                    p_obj = part.browse(self.cr,self.uid,data['form']['partner_id'])
                    print p_obj.property_account_payable.name,"--XXXXXXXXXXXXXXXXXXXXXXXXXXxx"
                    data['form'].update({'account_id':p_obj.property_account_payable.id})
                    aml = self.pool.get("account.move.line")
                    aml_ids  = aml.search(self.cr,self.uid,[('tds_id','!=',None),('reconcile_id','!=',None),            
                    ('tds_id.invoice_partner_id','=',data['form']['partner_id']),
                    ('tds_id.tds_nature_id','=',data['form']['tds_nature_id']),                                
                    ])
                    obj = aml.browse(self.cr,self.uid,aml_ids)
                    reconcile_ids = ''
                    if obj:
                        reconcile_ids = ','.join(map(lambda x:str(x.reconcile_id.id),obj))
                    sql1 =  """select aml.id as aml_id,tds.id as tds_id,
                    inv.amount_total as invoice_total,inv.date_invoice as date_invoice,'DATE VOUCH PAID' as date_inv_payment,                        
                    
                    aml.reconcile_id as reconcile_id,
                    
                    av.cheque_no as cheque_no,av.bsr_no as bsr,
                    
                    av.date as voucher_date,av.number as voucher_number,
                    aml.credit as tds_total
                    
                    from account_move_line  aml 
                    join account_tds tds on (tds.id = aml.tds_id)
                    join account_move am on (am.id = aml.move_id)
                    join account_invoice inv on (inv.move_id = am.id)            
                    
                    join account_voucher_line avl on (aml.id = avl.move_line_id)
                    join account_voucher av on (av.id = avl.voucher_id)            
                    
                    where  aml.tds_id is NOT NULL
                    and aml.reconcile_id is NOT NULL
                    and tds.invoice_partner_id = %s
                    and tds.tds_nature_id = %s     
                    and av.state='posted'    
                    and inv.state not in ('draft')
                    %s
                    """%(data['form']['partner_id'],data['form']['tds_nature_id'],date_str)                                    
                    self.cr.execute(sql1)
                    print sql1,"---sql"
                    res1 = self.cr.dictfetchall()
                    #join account_tds_line tdsl on (tdsl.tds_id= tds.id)
                    new=[]
                    #getting all lines, may be we can add a where condn for tds_id to reduce resultds
                    tds_sql = """
                    select tds_id,tds_tax,credit from account_tds_line
                    group by tds_tax,tds_id,credit
                    """
                    
                    self.cr.execute(tds_sql)
                    tds_res = self.cr.dictfetchall()
                    tot_tds = 0.0
                    tot_sur = 0.0
                    tot_ed = 0.0
                    tot_tot = 0.0
                    #print tds_res,"--TTTTTTTTTTTTTTTTTTDDDDDDDDDDDDDDDDDDSSSSSSSSSSSSSSSSSS"
                    for ele in res1:
                        tmp= {}
                        tmp.update(ele)
                        tot_tot += ele['tds_total']
                        for tds in tds_res:
                            if tds['tds_id'] == ele['tds_id']:
                                print "TDS ID",tds
                                if tds['tds_tax'] == 'ic':
                                    tmp['tds'] = tds['credit']
                                    tot_tds += tds['credit']
                                if tds['tds_tax'] == 'sur':
                                    tmp['sur'] = tds['credit']
                                    tot_sur += tds['credit']
                                if tds['tds_tax'] ==  'ed':
                                    tmp['ed'] = tds['credit']
                                    tot_ed += tds['credit']
                        new.append(tmp)     
                    self.localcontext.update({'total':{'tot_tds':tot_tds,'tot_sur':tot_sur,'tot_ed':tot_ed,'tot_tot':tot_tot}})
                    #print sql1
                    print "Reconcile ids",reconcile_ids
                    print new,"---res1"
                    return new
            except:
                traceback.print_exc()
            
report_sxw.report_sxw('report.account.tds.form16a', 'account.account',
'addons/account_tds_report/report/tds_report_form16a.rml', parser=order, header=True)



