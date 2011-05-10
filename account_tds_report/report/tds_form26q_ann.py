
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
import itertools
import operator
from report import report_sxw
import traceback
import pooler
import datetime
class order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(order, self).__init__(cr, uid, name, context)
        self.localcontext.update({
        'time': time,
        'tdsreport':self.tdsreport,
        'rows':None,
        'ded_obj':None,
        'getDate':self.getDate,       
        'compObj':self.compObj
    
        })
    def compObj(self):
        comp = self.pool.get('res.company')
        c_ids = comp.search(self.cr,self.uid,[])
        return comp.browse(self.cr,self.uid,c_ids[0])
        
    def getDate(self,date):
        if not date:
            #return currrent date if date is not there
            return datetime.datetime.now().strftime("%d-%b-%Y")
        do = datetime.datetime.strptime(date,"%Y-%m-%d")
        return datetime.datetime.strftime(do,"%d-%b-%Y")  #same as do.strftime("%d-%b-%Y")
        
        
    def tdsreport(self,data):
        
        """ It has to fetch for current quarter """
        #http://www.simpletaxindia.org/2007/08/frequently-asked-questionsetdsetcs.html
        
        try:
            ded = self.pool.get('account.tds.deductor')
            ded_obj = ded.browse(self.cr,self.uid,data['form']['name_id']) 

            sec = pooler.get_pool(self.cr.dbname).get('account.tds.section')
            #sec_ids = sec.search(self.cr,self.uid,[])
            final = []
            #TODO:date constraint need to be added
            date_str=""
            if data['form']['date_start'] and data['form']['date_end']:
                date_str = " and aml.date>='%s' and aml.date<='%s' "%(data['form']['date_start'],data['form']['date_end'])

            new=[]            
            tds_sql = """
            select '02' as code,'PAN' as pan,part.name as partname,av.date as voucher_date,
            inv.amount_untaxed+inv.amount_tax as inv_total,
            'YES' as book,
             tds.tds_amount as tds_total,
            av.amount as tax_deposited,
            av.bsr_no as bsr_no,
            av.number as voucher_number,
            inv.date_invoice,
            tds.id as tds_id,
            sec.id as sec_id,
            sec.name as sec_name            
            from account_move_line  aml           
            join account_tds tds on (tds.id = aml.tds_id)
            join account_tds_deductee_type ded_type on (ded_type.id = tds.tds_deductee_id)
            join account_move am on (am.id = aml.move_id)
            join account_invoice inv on (inv.move_id = am.id)                        
            join account_voucher_line avl on (aml.id = avl.move_line_id)
            join account_voucher av on (av.id = avl.voucher_id)                    
            join res_partner part on (tds.partner_id=part.id)
            join account_tds_nature nat on (tds.tds_nature_id = nat.id)
            join account_tds_section sec on (nat.tds_section_id= sec.id)            
            where inv.state not in ('draft')
            and av.state in ('posted')
            and aml.state = 'valid'
            and ded_type.residential is true
            and tds.salary is false
            %s
            
            group by pan,part.name,voucher_date,inv_total,book,tds_total,tax_deposited, date_invoice,tds.id,
            sec.id,sec.name,bsr_no,voucher_number            
            order by tds.id;
            """%(date_str)
            self.cr.execute(tds_sql)
            res =  self.cr.dictfetchall()
            print res,"--res"

            tds_sql = """
                    select tds_id,tds_tax,credit from account_tds_line
                    group by tds_tax,tds_id,credit
            """                    
            self.cr.execute(tds_sql)
            tds_res = self.cr.dictfetchall()
            new=[]
            tot_tds = 0.0
            tot_sur = 0.0
            tot_ed = 0.0
            tot_tds_tot = 0.0
            tot_inv = 0.0
            tot_tax_deposited = 0.0
            #print tds_res,"--TTTTTTTTTTTTTTTTTTDDDDDDDDDDDDDDDDDDSSSSSSSSSSSSSSSSSS"
            for ele in res:
                tmp= {}
                tot_inv += ele['inv_total']
                tot_tax_deposited += ele['tax_deposited']
                tot_tds_tot += ele['tds_total']
                tot_inv += ele['inv_total']
                tmp.update(ele)
                
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
            self.localcontext.update({'total':{'tot_tds':tot_tds,'tot_sur':tot_sur,'tot_ed':tot_ed,'tot_tds_tot':tot_tds_tot,
            'tot_inv':tot_inv,'tot_tax_deposited':tot_tax_deposited}})        
            #return new
            print new,"---NNNNNNNNNNNNNNNNNNNNNNNNNN"
            """
            #print operator.itemgetter('sec_id'),"_SSSSSSSSSSSSSSSSSSSSSSSSSSS"
            for key, items in itertools.groupby(new, operator.itemgetter('sec_id')):
                #print list(items),"ITEMS"
                final.append(list(items))
                final.append({'sec_name':sec.browse(self.cr,self.uid,key).name})
            print final,"FFFFFFFFFFFFFF"
            """
            self.localcontext.update({'rows':new})
            self.localcontext.update({'ded_obj':{'obj':ded_obj}})
            #return res      
        except:
            traceback.print_exc()
                        
report_sxw.report_sxw('report.account.tds.form26q_ann', 'account.account',
'addons/account_tds_report/report/tds_report_form26q_ann.rml', parser=order, header=True)



