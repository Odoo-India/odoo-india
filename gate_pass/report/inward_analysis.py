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

from openerp import tools
from openerp.osv import fields,osv
from openerp.addons.decimal_precision import decimal_precision as dp


class report_stock_move(osv.osv):
    _name = "report.stock.move"
    _description = "Moves Statistics"
    _auto = False
    _columns = {
        'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'month':fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month',readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', readonly=True),
        'product_id':fields.many2one('product.product', 'Product', readonly=True),
        'company_id':fields.many2one('res.company', 'Company', readonly=True),
        'picking_id':fields.many2one('stock.picking', 'No', readonly=True),
        'type': fields.selection([('out', 'Sending Goods'), ('in', 'Getting Goods'), ('receipt', 'Receipt'), ('internal', 'Internal'), ('other', 'Others')], 'Shipping Type', required=True, select=True, help="Shipping type specify, goods coming in or going out."),
        'location_id': fields.many2one('stock.location', 'Source Location', readonly=True, select=True, help="Sets a location if you produce at a fixed location. This can be a partner location if you subcontract the manufacturing operations."),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', readonly=True, select=True, help="Location where the system will stock the finished products."),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
        'product_qty':fields.integer('Quantity',readonly=True),
        'categ_id': fields.many2one('product.category', 'Product Category', ),
        'product_qty_in':fields.integer('In Qty',readonly=True),
        'product_qty_out':fields.integer('Out Qty',readonly=True),
        'value' : fields.float('Total Value', required=True),
        'day_diff2':fields.float('Lag (Days)',readonly=True,  digits_compute=dp.get_precision('Shipping Delay'), group_operator="avg"),
        'day_diff1':fields.float('Planned Lead Time (Days)',readonly=True, digits_compute=dp.get_precision('Shipping Delay'), group_operator="avg"),
        'day_diff':fields.float('Execution Lead Time (Days)',readonly=True,  digits_compute=dp.get_precision('Shipping Delay'), group_operator="avg"),
        'stock_journal': fields.many2one('stock.journal','Stock Journal', select=True),
        'gate_pass_id': fields.many2one('gate.pass', 'Gate No'),
        'gp_date': fields.date('Gate Date', help="Creation time, usually the time of the order."),
        'case_code': fields.boolean("Cash Code"),
        'challan_no': fields.char("Challan No",size=256),
        'product_uom': fields.many2one('product.uom', 'UOM'),
        'purchase_id': fields.many2one('purchase.order', 'Purchase Order No'),
        'po_series_id': fields.many2one('product.order.series', 'Purchase Series'),
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'inward_year': fields.char('Inward Year', size=10, readonly=True),
        'puchase_year': fields.char('Purchase Year', size=10, readonly=True),
        'indent_year': fields.char('Indent Year', size=10, readonly=True),
        'indentor_id': fields.many2one('res.users', 'Indentor Name'),
        'tr_code': fields.integer('TR Code'),
        'diff': fields.float('Diff.', digits_compute= dp.get_precision('Account'), help="Amount to be add or less"),
        'lr_no': fields.char("LR No",size=64),
        'lr_date': fields.date("LR Date"),
        'excies': fields.float('Excies.', digits_compute= dp.get_precision('Account')),
        'rate': fields.float('Rate', digits_compute= dp.get_precision('Account'), help="Rate for the product which is related to Purchase order"),
        'department_id': fields.many2one('stock.location', 'Dept. Code'),
        'bill_no': fields.integer('Bill No'),
        'bill_date': fields.date('Bill Date'),
        'cess': fields.float('Cess.', digits_compute= dp.get_precision('Account')),
        'high_cess': fields.float('High cess.', digits_compute= dp.get_precision('Account')),
        'import_duty': fields.float('Import Duty.', digits_compute= dp.get_precision('Account')),
        'cenvat': fields.float('CenVAT.', digits_compute= dp.get_precision('Account')),
        'half_cess': fields.float('50% Cess.', digits_compute= dp.get_precision('Account')),
        'half_high_cess': fields.float('50% High cess.', digits_compute= dp.get_precision('Account')),
        'half_import_duty': fields.float('50% Import Duty.', digits_compute= dp.get_precision('Account')),
        'half_cenvat': fields.float('50% CenVAT.', digits_compute= dp.get_precision('Account')),
        'payment_id': fields.char('Payment Terms',size=64),
        'despatch_mode': fields.selection([('person','By Person'),
                                           ('scooter','By Scooter'),
                                           ('tanker','By Tanker'),
                                           ('truck','By Truck'),
                                           ('auto_rickshaw','By Auto Rickshaw'),
                                           ('loading_rickshaw','By Loading Rickshaw'),
                                           ('tempo','By Tempo'),
                                           ('metador','By Metador'),
                                           ('rickshaw_tempo','By Rickshaw Tempo'),
                                           ('cart','By Cart'),
                                           ('cycle','By Cycle'),
                                           ('pedal_rickshaw','By Pedal Rickshaw'),
                                           ('car','By Car'),
                                           ('post_parcel','By Post Parcel'),
                                           ('courier','By Courier'),
                                           ('tractor','By Tractor'),
                                           ('hand_cart','By Hand Cart'),
                                           ('camel_cart','By Camel Cart'),
                                           ('others','Others'),],"Despatch Mode"),
        'ac_code_id': fields.many2one('ac.code', 'AC Code', help="AC Code"),
        'tr_code_id': fields.many2one('tr.code', 'TR Code', help="TR Code"),
        'cylinder': fields.char('Cylinder Number', size=50),
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_stock_move')
        cr.execute("""
            CREATE OR REPLACE view report_stock_move AS (
                SELECT
                        min(sm_id) as id,
                        date_trunc('day',al.dp) as date,
                        al.curr_year as year,
                        al.curr_month as month,
                        al.curr_day as day,
                        al.curr_day_diff as day_diff,
                        al.curr_day_diff1 as day_diff1,
                        al.curr_day_diff2 as day_diff2,
                        al.location_id as location_id,
                        al.picking_id as picking_id,
                        al.company_id as company_id,
                        al.location_dest_id as location_dest_id,
                        al.product_qty,
                        al.out_qty as product_qty_out,
                        al.in_qty as product_qty_in,
                        al.partner_id as partner_id,
                        al.product_id as product_id,
                        al.state as state ,
                        al.product_uom as product_uom,
                        al.categ_id as categ_id,
                        coalesce(al.type, 'other') as type,
                        al.stock_journal as stock_journal,
                        al.gate_pass_id as gate_pass_id,
                        al.gp_date as gp_date,
                        al.challan_no as challan_no,
                        al.case_code as case_code,
                        al.purchase_id as purchase_id,
                        al.po_series_id as po_series_id,
                        al.indent_id as indent_id,
                        al.inward_year as inward_year,
                        al.puchase_year as puchase_year,
                        al.indent_year as indent_year,
                        al.indentor_id as indentor_id,
                        al.tr_code as tr_code,
                        al.diff as diff,
                        al.lr_no as lr_no,
                        al.lr_date as lr_date,
                        al.excies as excies,
                        al.rate as rate,
                        al.department_id as department_id,
                        al.bill_no as bill_no,
                        al.bill_date as bill_date,
                        al.cess as cess,
                        al.high_cess as high_cess,
                        al.import_duty as import_duty,
                        al.cenvat as cenvat,
                        al.half_cess as half_cess,
                        al.half_high_cess as half_high_cess,
                        al.half_import_duty as half_import_duty,
                        al.half_cenvat as half_cenvat,
                        al.payment_id as payment_id,
                        al.despatch_mode as despatch_mode,
                        al.tr_code_id as tr_code_id,
                        al.ac_code_id as ac_code_id,
                        al.cylinder as cylinder,
                        sum(al.in_value - al.out_value) as value
                    FROM (SELECT
                        CASE WHEN sp.type in ('out') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS out_qty,
                        CASE WHEN sp.type in ('in') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor)
                            ELSE 0.0
                            END AS in_qty,
                        CASE WHEN sp.type in ('out') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * pt.standard_price
                            ELSE 0.0
                            END AS out_value,
                        CASE WHEN sp.type in ('in') THEN
                            sum(sm.product_qty * pu.factor / pu2.factor) * pt.standard_price
                            ELSE 0.0
                            END AS in_value,
                        min(sm.id) as sm_id,
                        sm.date as dp,
                        to_char(date_trunc('day',sm.date), 'YYYY') as curr_year,
                        to_char(date_trunc('day',sm.date), 'MM') as curr_month,
                        to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as curr_day,
                        avg(date(sm.date)-date(sm.create_date)) as curr_day_diff,
                        avg(date(sm.date_expected)-date(sm.create_date)) as curr_day_diff1,
                        avg(date(sm.date)-date(sm.date_expected)) as curr_day_diff2,
                        sm.location_id as location_id,
                        sm.location_dest_id as location_dest_id,
                        sum(sm.product_qty) as product_qty,
                        pt.categ_id as categ_id ,
                        sm.partner_id as partner_id,
                        sm.product_id as product_id,
                        sm.picking_id as picking_id,
                        sm.po_series_id as po_series_id,
                        sm.indent_id as indent_id,
                        sm.inward_year as inward_year,
                        sm.puchase_year as puchase_year,
                        sm.indent_year as indent_year,
                        sm.indentor_id as indentor_id,
                        sm.diff as diff,
                        sm.excies as excies,
                        sm.rate as rate,
                        sm.bill_no as bill_no,
                        sm.bill_date as bill_date,
                        sm.cess as cess,
                        sm.high_cess as high_cess,
                        sm.import_duty as import_duty,
                        sm.cenvat as cenvat,
                        (sm.cess / 2 ) as half_cess,
                        (sm.high_cess / 2 ) as half_high_cess,
                        (sm.import_duty / 2 ) as half_import_duty,
                        (sm.cenvat / 2 ) as half_cenvat,
                        sm.payment_id as payment_id,
                            sm.company_id as company_id,
                            sm.state as state,
                            sm.product_uom as product_uom,
                            sp.type as type,
                            sp.stock_journal_id AS stock_journal,
                            sp.gate_pass_id as gate_pass_id,
                            sp.gp_date as gp_date,
                            sp.challan_no as challan_no,
                            sp.case_code as case_code,
                            sp.purchase_id as purchase_id,
                            sp.tr_code as tr_code,
                            sp.lr_no as lr_no,
                            sp.lr_date as lr_date,
                            sp.department_id as department_id,
                            sp.despatch_mode as despatch_mode,
                            sp.tr_code_id as tr_code_id,
                            sp.ac_code_id as ac_code_id,
                            sp.cylinder as cylinder,
                            to_char(date_trunc('day',sm.date), 'YYYY-MM-DD') as date
                    FROM
                        stock_move sm
                        LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                        LEFT JOIN product_product pp ON (sm.product_id=pp.id)
                        LEFT JOIN product_uom pu ON (sm.product_uom=pu.id)
                          LEFT JOIN product_uom pu2 ON (sm.product_uom=pu2.id)
                        LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    GROUP BY
                        sm.id,sp.type, sm.date,sm.partner_id,
                        sm.product_id,sm.state,sm.product_uom,sm.date_expected,
                        sm.product_id,pt.standard_price, sm.picking_id, sm.product_qty,
                        sm.company_id,sm.product_qty, sm.location_id,sm.location_dest_id,pu.factor,pt.categ_id, sp.stock_journal_id,sp.gate_pass_id,sp.gp_date,sp.challan_no, sp.case_code,sp.purchase_id,sp.tr_code,sp.lr_no,sp.lr_date,sp.department_id,sm.po_series_id,sm.indent_id,sm.inward_year,sm.puchase_year,sm.indent_year,sm.indentor_id,sm.diff,sm.excies,sm.rate,sm.bill_no,sm.bill_date,sm.cess,sm.high_cess,sm.import_duty,sm.cenvat,sm.payment_id,sp.despatch_mode,sp.tr_code_id,sp.ac_code_id,sp.cylinder)
                    AS al
                    GROUP BY
                        al.out_qty,al.in_qty,al.curr_year,al.curr_month,
                        al.curr_day,al.curr_day_diff,al.curr_day_diff1,al.curr_day_diff2,al.dp,al.location_id,al.location_dest_id,
                        al.partner_id,al.product_id,al.state,al.product_uom,
                        al.picking_id,al.company_id,al.type,al.product_qty, al.categ_id, al.stock_journal,al.gate_pass_id,al.gp_date,al.challan_no,al.case_code,al.purchase_id,al.po_series_id,al.indent_id,al.inward_year,al.puchase_year,al.indent_year,al.indentor_id,al.tr_code,al.diff,al.lr_no,al.lr_date,al.excies,al.rate,al.department_id,al.bill_no,al.bill_date,al.cess,al.high_cess,al.import_duty,al.cenvat,al.half_cess,al.half_high_cess,al.half_import_duty,al.half_cenvat,al.payment_id,al.despatch_mode,al.tr_code_id,al.ac_code_id,al.cylinder)
        """)

report_stock_move()
