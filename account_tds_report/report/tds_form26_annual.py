
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
import itertools
import operator
import datetime
class order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(order, self).__init__(cr, uid, name, context)
        self.val={}
        self.localcontext.update({
        'time': time,
        'tdsreport':self.tdsreport,
        'val':self.val,
        'get_tds26q':self.get_tds26q,
        'get_tds26q2':self.get_tds26q2,
        'getDate':self.getDate,        
        })
        self.all_tds =[]
        
    def getDate(self,date):
        do = datetime.datetime.strptime(date,"%Y-%m-%d")
        return datetime.datetime.strftime(do,"%d-%b-%Y")  #same as do.strftime("%d-%b-%Y")
        
        
    def get_tds26q(self,data):
        try:
            """ It has to fetch for current quarter """            
            date_str=""
            if data['form']['date_start'] and data['form']['date_end']:
                date_str = " and aml.date>='%s' and aml.date<='%s' "%(data['form']['date_start'],data['form']['date_end'])

            #TODO:date constraint need to be added
            new=[]
            
            tds_sql = """
            select section.name,aml.tds_id,atl.tds_tax,atl.credit from account_tds_line atl
            join account_tds at on (atl.tds_id = at.id)            
            join account_tds_nature nat  on (at.tds_nature_id = nat.id)
            join account_tds_deductee_type ded_type on (ded_type.id = at.tds_deductee_id)
            join account_tds_section section on (section.id = nat.tds_section_id)
            join account_move_line aml on (aml.tds_id = at.id)
            where aml.state='valid' and aml.reconcile_id is NOT NULL
            and ded_type.residential is true
            and at.salary is false
            and atl.credit > 0
            %s
            group by atl.tds_tax,aml.tds_id,atl.credit,section.name order by aml.tds_id
            """%(date_str)            
            self.cr.execute(tds_sql)
            tds_res = self.cr.dictfetchall()
            print tds_res,"--TTTTTTTTTTTTTTTTTTDDDDDDDDDDDDDDDSSSSSSSSSSS"
            new=[]
            #tmp= {}
            
            for key, items in itertools.groupby(tds_res, operator.itemgetter('tds_id')):
                print key,"tds key"
                self.all_tds.append(key)
                tmp = list(items)
                print tmp,"--tmp"
                ele_dict = {}
                ele_dict['ic'] = 0.0
                ele_dict['sur'] = 0.0
                ele_dict['ed'] = 0.0
                for tds in tmp:
                        if tds['tds_tax'] == 'ic':
                            ele_dict['ic'] = tds['credit']
                        
                        if tds['tds_tax'] == 'sur':
                            ele_dict['sur'] = tds['credit']
                        
                        if tds['tds_tax'] ==  'ed':
                            ele_dict['ed'] = tds['credit']                                                    
                        ele_dict['name'] = tds['name']   
                        print ele_dict,"ELE DICT"                         
                        
                new.append(ele_dict)
            """
            for tds in tds_res:
                
                tmp.update(ele)
                for ele in new:
                    if ele['name'] == tds['name']:
                        print "TDS ID",tds
                        if tds['tds_tax'] == 'ic':
                            tmp['tds'] = tds['credit']
                        
                        if tds['tds_tax'] == 'sur':
                            tmp['sur'] = tds['credit']
                        
                        if tds['tds_tax'] ==  'ed':
                            tmp['ed'] = tds['credit']
                new.append(tmp)        
            """
            #print sql1
            #print "Reconcile ids",reconcile_ids
            print new,"---res1"
            return new
        except:
            traceback.print_exc()
            return "ERROR"
            
    def get_tds26q2(self):    
        date_str=''
        tds_str= ','.join(map(str,self.all_tds))
        print tds_str
        if tds_str:
            sql1 =  """select aml.id as aml_id,tds.id as tds_id,    
            aml.reconcile_id as reconcile_id,
            aml.credit as tds_total,
            av.cheque_no as cheque_no,
            av.bsr_no as bsr,      
            'CHALLAN' as challan,      
            'Yes' as book,
            av.date as voucher_date,
            av.number as voucher_number            
            from account_move_line aml 
            join account_tds tds on (tds.id = aml.tds_id)            
            join account_voucher_line avl on (aml.id = avl.move_line_id)
            join account_voucher av on (av.id = avl.voucher_id)                        
            where  aml.tds_id in (%s)
            and aml.state='valid'
            and aml.reconcile_id is NOT NULL   
            order by tds.id
            """%(tds_str)                                    
            self.cr.execute(sql1)        
            res = self.cr.dictfetchall()
            print res,"---RES"
            return res    
        else:
            print "No TDS IDS"
            return []
        
    def tdsreport(self,data):
            try:
               fy = self.pool.get('account.fiscalyear')
               com = self.pool.get('res.company')
               ded = self.pool.get('account.tds.deductor')
               ded_obj = ded.browse(self.cr,self.uid,data['form']['name_id'])                             
               com_obj = com.browse(self.cr,self.uid,1)
               ds =  data['form']['date_start']
               de =  data['form']['date_end']
               #company id hard coded to 1, make it generic in the future
               dom = [('company_id','=',1)]
               if ds and de:
                   dom.extend([('date_start','<=',ds),('date_stop','>=',de)])
               f_ids = fy.search(self.cr,self.uid,dom)
               if not f_ids:
                    raise osv.except_osv('Invalid date !', 'The given date range does not fall on any fiscal year defined !')


               dom = [('company_id','=',1)]               
               curr_date  = datetime.datetime.now().strftime("%Y-%m-%d")
               #if curr_date:
               dom.extend([('date_start','<=',curr_date),('date_stop','>=',curr_date),('state','=','draft')]) #active fiscal year
               asses_ids = fy.search(self.cr,self.uid,dom)                    
               if not asses_ids:
                    raise osv.except_osv('Invalid fiscal !', 'The current date does not fall on any active fiscal year defined !')               
               print "SOME THING",dom
               self.val = {'tax_acc_no':com_obj.partner_id.vat_no,
               'perm_acc_no':com_obj.partner_id.pan_no,
               'previously_reported':'No',
               'fy':fy.browse(self.cr,self.uid,f_ids[0]).code, #code need to be like 2010-2011
               'ay':fy.browse(self.cr,self.uid,asses_ids[0]).code,
               'ded_comp_name':com_obj.name,
               'ded_comp_flat_no':com_obj.partner_id.address[0].flat_no,
               'ded_comp_name_building':com_obj.partner_id.address[0].build_name,
               'ded_comp_area':com_obj.partner_id.address[0].city,
               'ded_comp_street':com_obj.partner_id.address[0].street,
               'ded_comp_city':com_obj.partner_id.address[0].city,
               'ded_comp_state':com_obj.partner_id.address[0].state_id and com_obj.partner_id.address[0].state_id.name or '',
               'ded_comp_pin':com_obj.partner_id.address[0].zip,
               'ded_comp_phone':com_obj.partner_id.address[0].phone,
               'ded_comp_email':com_obj.partner_id.address[0].email,                                                            
               
               'ded_name':ded_obj.name,               
               'ded_flat_no':ded_obj.address_id.flat_no,
              'ded_name_building':ded_obj.address_id.build_name,
               'ded_area':ded_obj.address_id.city,
               'ded_street':ded_obj.address_id.street,
               'ded_city':ded_obj.address_id.city,
               'ded_state':ded_obj.address_id.state_id and ded_obj.address_id.state_id.name or '' ,
               'ded_pin':ded_obj.address_id.zip,
               'ded_phone':ded_obj.address_id.phone,
               'ded_email':ded_obj.address_id.email,                                                            
                              
               
               }
               
               print self.val
               self.localcontext.update({'val':self.val})
               self.localcontext.update({'ded_obj':ded_obj})
            except:
                traceback.print_exc()
            return ''
report_sxw.report_sxw('report.account.tds.form26', 'account.account',
'addons/account_tds_report/report/tds_report_form26_annual.rml', parser=order, header=True)



