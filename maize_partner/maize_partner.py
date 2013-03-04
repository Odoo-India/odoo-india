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


from openerp.osv import fields, osv

class supplier_series(osv.Model):
    _name = 'supplier.series'
    _description = ' Add Purchase Order series'
    _rec_name = 'code'
    
    _columns = {
        'code': fields.char('Series', size=15),
        'name': fields.char('Description', size=50),
        }
supplier_series()

class res_partner(osv.Model):
    _inherit = 'res.partner'
    _rec_name = 'supp_code'
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.supp_code and '[' + pckg.supp_code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res        
    _columns = {
        'co_code': fields.char('COCODE', size=256),
        'supp_code': fields.char('SUPPCODE', size=256),
        'street3': fields.char('Address3', size=256),
        'raw_code_id': fields.many2one('row.code','RAWCODE'),
        'tax_code_id': fields.many2one('tax.code','TAXCODE'),
        'bank_code_id': fields.many2one('account.journal','BANKCODE'),
        'md_code': fields.selection([('manufacture','M'),(' dealer','D')],'MDCODE'),
        'series_id':fields.many2one('supplier.series', 'SERIES'),
        'tds_per':fields.float('TDSPER'),
        'c_form':fields.boolean('CFORMIND'),
        'pan_no': fields.char('PANNO', size=256),
        'stno_1': fields.char('STNO_1', size=256),
        'stno_2': fields.char('STNO_2', size=256),
        'ecc_code': fields.char('ECCCODE', size=256),
        'ser_tax_reg_no': fields.char('SERTAXREGNO', size=256),
        'cst_no': fields.char('CSTNO', size=256)
        }

res_partner()

class row_code(osv.Model):
    _name = "row.code"
    _rec_name="code"
    _columns = {
        'code': fields.char('Code', size=256),
        'name': fields.char('Name', size=256),
        }
row_code()
class tax_code(osv.Model):
    _name = "tax.code"
    _rec_name="code"
    _columns = {
        'code': fields.char('STCODE', size=256),
        'name': fields.char('STDESC', size=256),
        }
tax_code()

class account_journal(osv.Model):
    _inherit = 'account.journal'
    
    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id, '['+elmt.code +'] '+elmt.name))
        return res

account_journal()
