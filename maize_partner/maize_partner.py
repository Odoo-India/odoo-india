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
        if isinstance(ids, (int, long)):
            ids = [ids]
        elif not len(ids):
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

class res_users(osv.Model):
    _inherit = "res.users"
    
    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('user_code', 'ilike', name)]+ args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', 'ilike', name)]+ args, limit=limit, context=context)#fix it ilike should be replace with operator

        return self.name_get(cr, user, ids, context=context)
    
    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        if isinstance(ids, (int, long)):
            ids = [ids]
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id, '['+ (elmt.user_code or '') +'] '+elmt.name))
        return res
    
    _columns = {
            'user_code': fields.char('Code', size=50),
                }
res_users()

class res_company(osv.osv):
    _inherit = 'res.company'
    
    _columns = {
        'rml_header3': fields.text('RML Internal Header for Landscape Reports', required=True),
    }

    def write(self, cr, uid, ids, values, context=None):
        values.update({'rml_header3': self.get_header(cr, uid, ids)})
        return super(res_company,self).write(cr, uid, ids, values, context=context)

    def get_header(self,cr, uid, ids):
        return """
        <header>
        <pageTemplate>
            <frame id="first" x1="1.0" y1="1.0" width="840" height="525"/>
            <pageGraphics>
                <fill color="black"/>
                <stroke color="black"/>
                <setFont name="DejaVu Sans" size="8"/>
                <drawString x="25" y="555"> [[ formatLang(time.strftime("%Y-%m-%d"), date=True) ]]  [[ time.strftime("%H:%M") ]]</drawString>
                <setFont name="DejaVu Sans Bold" size="10"/>
                <drawCentredString x="440" y="555">[[ company.partner_id.name ]]</drawCentredString>
                <stroke color="#000000"/>
                <lines>25 550 818 550</lines>
                <!-- left margin -->
            <rotate degrees="90"/>
            <setFont name="DejaVu Sans" size="6"/>
            <fill color="grey"/>
            <drawString x="1.00cm" y="-0.3cm">generated by OpenERP.com</drawString>
            <fill color="black"/>
            <rotate degrees="-90"/>
            </pageGraphics>
        </pageTemplate>
        </header>"""
    
    _defaults = {
        'rml_header3': get_header,
    }
    
res_company()