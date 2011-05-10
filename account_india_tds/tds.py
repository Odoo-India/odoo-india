
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
import pooler



class account_tds_deductee_type(osv.osv):
       _name = 'account.tds.deductee.type'
       _columns = {
          'name': fields.char("Name",size=256),
          'residential': fields.boolean('Residential status,Resident?'),
          'status': fields.boolean('status'),
          'company':fields.boolean('Deductee Status,Company?'),
          'active': fields.boolean('Active'),
          'tds_deductee_line': fields.one2many('account.tds.deductee.line','tds_deductee_id',"Deductee Line")
                  }
account_tds_deductee_type()

class account_tds_deductee_line(osv.osv):
       _name = 'account.tds.deductee.line'
       #TODO: multiple nature for same tds_deductee shd not be possible, may be _sql_constraints = [ UNIQUE(tds_deductee_id,tds_nature_id) ]
       _columns = {
          'tds_nature_id': fields.many2one('account.tds.nature',"TDS Nature ID"),
          'tds_deductee_id': fields.many2one('account.tds.deductee.type', "TDS Deductee Type"),
           
          
          'tds_deductee_line_line': fields.one2many('account.tds.deductee.line.line','tds_deductee_line_id',"Deductee Line Line")
          }
          
          
account_tds_deductee_line()

class account_tds_deductee_type_line_line(osv.osv):
       _name = 'account.tds.deductee.line.line'
       _order = "tds_deductee_line_id,date_from desc"
       _columns = {
          'date_from': fields.date('Date From',required=True),
          'tds_rate': fields.float('TDS Rate'),
          'tds_exempt_limit': fields.float('TDS Exempt Limit'),
          'sur_rate': fields.float('Sur Rate'),
          'sur_exempt_limit': fields.float('Sur Exempt Limit'),
          'ed_cess_rate': fields.float('ED CESS Rate'),          
          'ed_exempt_limit': fields.float('ED  Exempt Limit'),
          'sec_ed_cess_rate': fields.float('SEC ED CESS Rate'),
          'sec_ed_exempt_limit': fields.float('SEC Exempt Limit'),
          'tds_deductee_line_id': fields.many2one('account.tds.deductee.line', "TDS Deductee Type Line"),
                  }

account_tds_deductee_type_line_line()


class account_tds_deductor(osv.osv):
    
    _name = 'account.tds.deductor'
    _columns = {
    'name':fields.char('Deductor Name',size=256),
    'desig':fields.char('Designation',size=256),
    'address_id':fields.many2one('res.partner.address',"Address"),
    }
account_tds_deductor()

class account_tds_tax(osv.osv):
        _name='account.tds.tax'
        _columns  = {
           'name': fields.char('Name',size=256),
          'code': fields.integer('Code'),
          'description': fields.char('Description',size=256)
        }
account_tds_tax()

class account_tds_section(osv.osv):
       _name = 'account.tds.section'
       _columns = {
          'name': fields.char('Name',size=256),
          'code': fields.integer('Code'),
          'description': fields.char('Description',size=256)
        }
account_tds_section()

class account_tds_nature(osv.osv):
       _name = 'account.tds.nature'
       _columns = {
          'code': fields.integer('Code'),
          'name': fields.char('name',size=256),
          'tds_section_id': fields.many2one('account.tds.section','section'),
          'payment_code': fields.integer('Payment Code'),
          'account_id': fields.many2one('account.account', "Duties Account",required=True),
        }
account_tds_nature()

class account_tds(osv.osv):
       _name = 'account.tds'
       
       """
       def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
           print dir(self._columns['move_line_id']),"TDS READ",fields
           #though move_line_id is store=True, every read (tree view calls as well) will trigger fuctional call, by the act of  next line
           res = self._columns['move_line_id'].get(cr,self, ids, 'move_line_id', uid, context,None)
           print res,"------------++++++++++++------------------"
           for k,v in res.items():
                    print "Inside k,v tds.py",k,v
                    #self.write(cr,uid,[k],{'move_line_id':v[0]})
                    x= self._columns['move_line_id'].set(cr, self,k, 'move_line_id', v[0], uid, context)
           #res will have {10:350,11:360}
    
           return super(account_tds,self).read(cr,uid,ids,fields,context,load)
       """
       def _recalc_function(self, cr, uid, ids, context=None):
            print 'recalc calledRRRRRRRRRRRRRRRRRRRRRRR',ids
            obj = self.pool.get("account.move.line")
            data = obj.read(cr,uid,ids,['tds_id'])
            print data,"data "
            tds_ids = []#map(lambda x:x['tds_id'],data)
            for ele in data:
                if ele['tds_id']:
                    tds_ids.append(ele['tds_id'][0])                
            print tds_ids,"tds ids going to be returned"
            return tds_ids
                   
       def _sum_of_tds_line(self,cr,uid,ids,field_name=None,arg=False,context={}):
           res={}
           print "Sum of tds line",ids
           
           for id in ids:
               print "res id",id
               obj = self.browse(cr,uid,id)
               if obj.tds_line_id:
                 res[id]=sum(map(lambda x:x.credit,obj.tds_line_id))
           return res
           
       def _insert_value(self,cr,uid,ids,name,value,arg='',context=None):
           print "Insert value called"
           print cr,"Curosr"
           print uid,"UID",ids
           self.write(cr,uid,[ids],{'move_line_id':value})
               
               
       def _get_move_line_id(self, cr, uid, ids, name, args, context=None):
            res = {}
            print ids,"TDS IDS"
            move_line = self.pool.get('account.move.line')
            m_ids = move_line.search(cr,uid,[('tds_id','in',ids)])
            #data = move_line.read(cr,uid,m_ids,['name'])
            print m_ids,"MOVE IDS"
            for id in ids:
                res[id]= None
            for ele in move_line.browse(cr,uid,m_ids):
                print ele.tds_id,"ELE T ID"
                if ele.tds_id:
                    print ele.tds_id.id,"Assigning ID",ele.id
                    res[ele.tds_id.id] =  ele.id
                
            print res,"Before retuning tds.py-------------------++++++++++++="
            return res

           
           
       _columns = {     
        'date': fields.date('Date of Request',required=True,readonly=True,states={'draft':[('readonly',False)]}),
        'inv_line_id': fields.many2one('account.invoice.line','Inv Line ID'),
        'type_ref': fields.char("Reference",size=256),
        'name': fields.char("Voucher Number",size=256),
        'tds_nature_id': fields.many2one('account.tds.nature','TDS Nature ID'),
        'tds_acc_id': fields.many2one('account.account','TDS Acc ID'),
        'amount': fields.float('Assesable Amount',readonly=True),
        'deductnow':fields.boolean('Deduct Now'),          
        'tds_amount': fields.function(_sum_of_tds_line,method=True,string='TDS Total',store=True,help="Sum of TDS Line"),
        'tds_payable': fields.float('Payable',readonly=True,help="Total-TDS"),
        'tds_line_id': fields.one2many('account.tds.line','tds_id',"TDS Line ID"),
        'type': fields.selection([('dr','Debit'),('cr','Credit')]),
        'paid': fields.boolean('Paid'),
        'zero': fields.boolean('Zero'),
        'partner_id':fields.many2one('res.partner',"Supplier"),
        'invoice_partner_id':fields.many2one('res.partner',"Invoiced Supplier"),
        'tds_deductee_id':fields.many2one('account.tds.deductee.type',"Deductee Type",required=True),
        'salary':fields.boolean("Salary ?"),
        'state':fields.selection([('draft','Draft'),('later','Deduct Later'),('confirmed','Confirmed')],"State Label",readonly=True,required=True),
        'move_line_id': fields.function(_get_move_line_id,method=True,type='many2one',obj="account.move.line",string="Move Line",
        store = {
       'account.move.line': (
              _recalc_function,['reconcile_id','name'],20)})                      
        }
       _defaults={
        'date': lambda *a: time.strftime('%Y-%m-%d'),
         'state':lambda *a:'draft',
        
       }      
account_tds()


class account_tds_line(osv.osv):
       _name = 'account.tds.line'
       _columns = {
          #'tds_tax_id': fields.many2one('account.tds.tax','tax_id'),
          'tds_tax':fields.selection([('ic','Income Tax'),('sur','Sur Charge'),('ed','Educational Cess'),('seced','Sec Educational Cess')],"Tax"),
          'tds_id': fields.many2one('account.tds', 'TDS'),
          'rate': fields.float('Rate'),
          'debit': fields.float('Debit'),
          'credit': fields.float('Credit'),
          'base': fields.float('Base'),
                  }
account_tds_line()
