# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-20013 Tiny SPRL (<http://tiny.be>).
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

class tax_retail_invoice_installer(osv.osv_memory):
    _name = 'tax.retail.invoice.installer'
    _inherit = 'res.config.installer'

    _columns = {
        'rml_header2': fields.text('RML Internal Header', required=True),
    }
    
    _header = """
<header>
    <pageTemplate>
        <frame id="first" x1="1.3cm" y1="2.0cm" height="26.0cm" width="19.0cm"/>
        <pageGraphics>
            <!-- You Logo - Change X,Y,Width and Height -->
            <drawRightString x="3.8cm" y="27.8cm">[[ company.name ]]</drawRightString>
            <image x="16.5cm" y="27.7cm" height="40.0">[[ company.logo or removeParentNode('image') ]]</image>
            <setFont name="DejaVu Sans" size="8"/>
            <fill color="black"/>
            <stroke color="black"/>
            <lines>1.3cm 27.7cm 20cm 27.7cm</lines>
            <!--page bottom-->
            <lines>1.2cm 2.15cm 19.9cm 2.15cm</lines>
            <drawCentredString x="10.5cm" y="1.30cm">[[ company.partner_id.name ]] [[ company.partner_id.street ]], [[ company.partner_id.street2 ]], [[ company.partner_id.city ]]</drawCentredString>
            <drawCentredString x="10.5cm" y="1.0cm">Phone : [[ company.partner_id.phone ]] Email : [[ company.partner_id.email ]] Website : [[ company.partner_id.website ]]</drawCentredString>
        </pageGraphics>
    </pageTemplate>
</header>"""

    _defaults = {
        'rml_header2': _header,
    }

    def execute(self, cr, uid, ids, context=None):
        res_company_obj = self.pool.get('res.company')
        res_country_obj = self.pool.get('res.country')
        country_id = res_country_obj.search(cr, uid, [('code','=','IN')], context=context)
        company_ids = res_company_obj.search(cr, uid, [('partner_id.country_id', 'in', country_id)])
        header_data = self.browse(cr, uid, ids[0], context=context).rml_header2
        res_company_obj.write(cr, uid, company_ids, {'rml_header2': header_data}, context=context)
        return super(tax_retail_invoice_installer, self).execute(cr, uid, ids, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
