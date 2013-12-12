# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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

class res_company(osv.osv):
    
    _inherit = 'res.company'
    
    _columns = {
        'ecc_no': fields.char('ECC', size=32, help="Excise Control Code"),
        'tin_no': fields.char('TIN', size=32, help="Tax Identification Number"),
        'cst_no': fields.char('CST', size=32, help='Central Sales Tax Number of Company'),
        'tin_date': fields.date('TIN Date', help="Tax Identification Number Date of Company"),
        'cst_date': fields.date('CST Date', help='Central Sales Tax Date of Company'),
        'vat_no' : fields.char('VAT Number', size=32, help="Value Added Tax Number"),
        'packing_cost': fields.boolean('Allow packing cost feature', help="Allows you to use packing cost feature."),
        'freight': fields.boolean('Allow freight feature', help="Allows you to use freight feature. This installs the module purchase_freight."),
        'dealers_discount': fields.boolean('Allow dealers discount feature', help="Allows you to use dealers discount feature.")
    }
    
    
    
    _header = """
    <header>
    <pageTemplate>
        <frame id="first" x1="1.3cm" y1="2.0cm" height="26.0cm" width="19.0cm"/>
        <pageGraphics>
            <!-- You Logo - Change X,Y,Width and Height -->
<drawRightString x="7.6cm" y="27.8cm">[[ company.name ]]</drawRightString>
            <image x="16.5cm" y="27.7cm" height="40.0" >[[ company.logo or removeParentNode('image') ]]</image>
            <setFont name="DejaVu Sans" size="8"/>
            <fill color="black"/>
            <stroke color="black"/>
            <lines>1.3cm 27.7cm 20cm 27.7cm</lines>
            <!--page bottom-->
            <lines>1.2cm 2.15cm 19.9cm 2.15cm</lines>
            <drawCentredString x="10.6cm" y="1.8cm">[[ company.rml_footer ]] </drawCentredString>
        </pageGraphics>
    </pageTemplate>"""


    _defaults ={
        'rml_header2': _header,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
