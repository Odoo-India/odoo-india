
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

from osv import osv, fields
import time
import datetime
def date_obj(s):
    if not s:
        now = datetime.datetime.now()
        return  now# datetime.datetime.strptime("%Y-%m-%d")
    return datetime.datetime.strptime(s,"%Y-%m-%d")

def date_orig(s):    
    return datetime.datetime.strptime(s,"%Y-%m-%d")

class account_move_line(osv.osv):
    _name = 'account.move.line'

    _inherit = 'account.move.line'
    _columns = {    
    'tds_id':fields.many2one("account.tds","TDS ID"),        
    }
account_move_line()

    
class account(osv.osv):
    _name = 'account.account'
    _inherit = 'account.account'
    _columns = {
    'is_tds':fields.boolean("Is TDS Applicable ?",help="Enable if this is a TDS reducable account"),
    'tds_nature_id':fields.many2one("account.tds.nature","TDS Nature",help="Choose this only if this is Tax account, For eg Duries & Taxes"),
    'tds_deductee_id':fields.many2one("account.tds.deductee.type","TDS Deductee Type",help="Choose this only if this is Supplier Payable account"),
    'advanced_tds':fields.boolean("Advanced TDS Entries ?"),
    'account_tds':fields.one2many("account.account.tds.line",'acc_id',"TDS")    
    }
account()

"""
class account_tds(osv.osv):
    _name = 'account.account.tds'    
    _columns = {    
    'tds_nature_id':fields.many2one("account.tds.nature","TDS Nature"),   
    'tds_lines':fields.one2many("account.account.tds.line",'acc_tds_id',"TDS Lines"),
    'acc_id':fields.many2one("account.account","Account"),   
    }
account_tds()
"""
class account_tds_line(osv.osv):
    _name = 'account.account.tds.line'    
    _columns = {    
    'tds_section_id': fields.many2one('account.tds.section','section'),
    'cert': fields.char('Certificate No/Date',size=256),
    'date_from': fields.date('Applicable From'),
    'date_to': fields.date('Applicable To'),
    'tds_rate': fields.float('TDS Rate'),
    'sur_rate': fields.float('Sur Rate'),
    'ed_cess_rate': fields.float('ED CESS Rate'),       
    'sec_ed_cess_rate': fields.float('SEC ED CESS Rate'),
    'acc_id':fields.many2one("account.account","Acc"),    
    
    }
account_tds_line()


class account_invoice_line(osv.osv):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'
    
    
    _columns = {
    'is_tds':fields.boolean("Is TDS Applicable ?"),
    'tds_ids':fields.one2many("account.tds","inv_line_id","TDS",ondelete='cascade'),
    'tds_deduct':fields.boolean("Deduct now ?"),    
    }
account_invoice_line()

class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'    
    def tds_generate(self,cr,uid,ids,context={}):
        print "Tds generate ",ids
        tds =  self.pool.get("account.tds")
        tds_line =  self.pool.get("account.tds.line")
        #inv_object = self.pool.get('account.invoice')
        tds_dict={} #not used
        
                
        for inv in self.browse(cr,uid,ids):
            
            for line in inv.invoice_line:                                
                if not line.is_tds:
                    #tds not applicable
                    continue
                if not line.tds_deduct:
                    print "Deduct later"
                    state = 'later'
                else:
                    state='draft'
                    #if not marked as deduct now
                    #with state draft, do it
                    #continue
                if line.tds_ids:
                    print "Deleting old"
                    tds.unlink(cr,uid,map(lambda x:x.id,line.tds_ids))
                          
                tds_line_dict=[]
                flag=False
                zero=False
                print line.id,"---inv line id"
                zero_tds= False
                if inv.account_id.is_tds:
                    if inv.account_id.advanced_tds:
                        #account tds need to override deductee type
                        print "Master overriding"
                        zero_tds = inv.account_id.account_tds
                    else:
                        print "No master"
                    #first checking acc master for advanced entries
                    if zero_tds:
                            zero=True
                            for d_line_line in zero_tds.tds_lines:                                
                                  print  d_line_line.date_from,"lineline date"
                                  print "d_line",inv.date_invoice                                
                                  tds_amount = 0.0
                                  if date_obj(inv.date_invoice) >= date_orig(d_line_line.date_from) and date_obj(inv.date_invoice) <= date_orig(d_line_line.date_to):
                                    flag=True
                                    #TODO: Exemption limit handling like normal TDS calc in the next part, once that works perfectly, can be added here as well
                                    ass_amount = float(line.price_subtotal)
                                    credit1 = float(d_line_line.tds_rate) * ass_amount                                    
                                    tds_line_dict.append({'tds_tax':'ic','rate':d_line_line.tds_rate,'debit':0.0,'credit':credit1,                                    
                                    'base':ass_amount})
                                    
                                    ass_amount = credit1
                                    credit2 = d_line_line.sur_rate * ass_amount                                                                                                        
                                    tds_line_dict.append({'tds_tax':'sur','rate':d_line_line.sur_rate,'debit':0.0,'credit':credit2,                                    
                                    'base':ass_amount})
                                    
                                    ass_amount = credit2+credit1
                                    credit3 = d_line_line.ed_cess_rate * ass_amount                                                                                                                                        
                                    tds_line_dict.append({'tds_tax':'ed','rate':d_line_line.ed_cess_rate,'debit':0.0,'credit':credit3,                                    
                                    'base':ass_amount})

                                    ass_amount = credit2+credit1
                                    credit4 = d_line_line.sec_ed_cess_rate * ass_amount                                                                                                                                        
                                    tds_line_dict.append({'tds_tax':'seced','rate':d_line_line.sec_ed_cess_rate,'debit':0.0,'credit':credit4,                                    
                                    'base':ass_amount})
                                    tds_amount = credit1+credit2+credit3+credit4
                                    print "In date range",tds_line_dict
                                    #break #go out of loop, once tds line obtained
                        
                    deductee = inv.account_id.tds_deductee_id
                    
                    if not flag:
                        #if acc master did not suit the criteria, go to deductee as usual
                      for d_line in deductee.tds_deductee_line:  
                        if d_line.tds_nature_id.id == line.account_id.tds_nature_id.id:                                
                                for d_line_line in d_line.tds_deductee_line_line:      
                                    max_dates = map(lambda x:date_orig(x.date_from),d_line.tds_deductee_line_line)                                    
                                    max_date = max(max_dates)                                    
                                    print  d_line_line.date_from,"lineline date"
                                    print "d_line",inv.date_invoice                                
                                    tds_amount = 0.0
                                    #this condn just takes the first best match
                                    #TODO: Rather it has get the max date for consideration
                                    #Have added order_by in the table, yet to check if it works                                    
                                    if max_date==date_orig(d_line_line.date_from) and date_obj(inv.date_invoice) >= date_orig(d_line_line.date_from):
                                        ass_amount = float(line.price_subtotal)
                                        #handling exemption limit on amount_untaxed of Invoice, is it right ?
                                        credit1 = 0.0
                                        print d_line_line.tds_exempt_limit,inv.amount_untaxed,"tds exempt and amount untaxed"
                                        if not d_line_line.tds_exempt_limit or d_line_line.tds_exempt_limit < inv.amount_untaxed:
                                            print "In for IC",ass_amount,d_line_line.tds_rate
                                            credit1 = float(d_line_line.tds_rate) * ass_amount                                    
                                            tds_line_dict.append({'tds_tax':'ic','rate':d_line_line.tds_rate,'debit':0.0,'credit':credit1,                                    
                                            'base':ass_amount})
                                            
                                        credit2=0.0
                                        print d_line_line.sur_exempt_limit,inv.amount_untaxed,"sur exempt and amount untaxed"
                                        if not d_line_line.sur_exempt_limit or d_line_line.sur_exempt_limit < inv.amount_untaxed:                                        
                                            ass_amount = credit1
                                            credit2 = d_line_line.sur_rate * ass_amount                                                                                                        
                                            tds_line_dict.append({'tds_tax':'sur','rate':d_line_line.sur_rate,'debit':0.0,'credit':credit2,                                    
                                            'base':ass_amount})
                                            
                                        credit3 = 0.0
                                        if not d_line_line.ed_exempt_limit or d_line_line.ed_exempt_limit < inv.amount_untaxed:                                        
                                            ass_amount = credit2+credit1
                                            credit3 = d_line_line.ed_cess_rate * ass_amount                                                                                                                                        
                                            tds_line_dict.append({'tds_tax':'ed','rate':d_line_line.ed_cess_rate,'debit':0.0,'credit':credit3,                                    
                                            'base':ass_amount})
                                            
                                        credit4=0.0
                                        if not d_line_line.sec_ed_exempt_limit or d_line_line.sec_ed_exempt_limit < inv.amount_untaxed:                                        
                                            ass_amount = credit2+credit1
                                            credit4 = d_line_line.sec_ed_cess_rate * ass_amount                                                                                                                                        
                                            tds_line_dict.append({'tds_tax':'seced','rate':d_line_line.sec_ed_cess_rate,'debit':0.0,'credit':credit4,                                    
                                            'base':ass_amount})
                                            
                                        tds_amount = credit1+credit2+credit3+credit4
                                        print "In date range",tds_line_dict
                                        #break #go out of loop, once tds line obtained
                                        
                    if tds_line_dict:  
                                            line_ids = []
                                            for ele in tds_line_dict:
                                                c_id = tds_line.create(cr,uid,ele)
                                                line_ids.append(int(c_id))
                                            print line_ids,"--line ids"
                                            tds.create(cr,uid,{'date':inv.date_invoice or time.strftime("%Y-%m-%d"),'inv_line_id':line.id,'name':'NAME',
                                            'tds_nature_id':d_line.tds_nature_id.id,'tds_acc_id': d_line.tds_nature_id.account_id.id,'amount':line.price_subtotal,
                                            'tds_amount':tds_amount,'tds_payable':(line.price_subtotal-tds_amount),                                        
                                            'tds_line_id':[(6,0,line_ids)],'type':'cr','paid':False,'state':state,'zero':zero,
                                            'partner_id':inv.partner_id.id,'invoice_partner_id':inv.partner_id.id,
                                            'tds_deductee_id':deductee.id
                                            
                                            })
                                    
                                    
                    
                print line.tds_ids,"tds ids"
        
        return True
account_invoice()



