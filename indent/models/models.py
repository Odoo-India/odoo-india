# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp

class StockLocation(models.Model):
    _inherit = 'stock.location'

    manager_id = fields.Many2one('res.users', 'Manager')
    is_plant = fields.Boolean('Plant')


class Equipment(models.Model):
    _name = 'indent.equipment'
    _description = 'Equipment'

    name = fields.Char('Name')
    code = fields.Char('Code')

    _sql_constraints = [
        ('equipment_code', 'unique(code)', 'Equipment code must be unique !')
    ]


class EquipmentSection(models.Model):
    _name = 'indent.equipment.section'
    _description = 'Equipment Section'

    equipment_id = fields.Many2one('indent.equipment', string='Equipment', required=True)
    name = fields.Char('Name', size=256)
    code = fields.Char('Code', size=16)

    _sql_constraints = [
        ('equipment_section_code', 'unique(equipment_id, code)', 'Section code must be unique per Equipment !')
    ]


class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    indent_close = fields.Boolean('Close Indents', default=False)
    purchase_close = fields.Boolean('Close Purchase', default=False)


class Indent(models.Model):
    _name = 'stock.indent'
    _description = 'Indent'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'date_approve desc'

    name = fields.Char('Indent')

    date_indent = fields.Datetime('Indent Date')
    date_approve = fields.Datetime('Approve Date')
    date_required = fields.Datetime('Required Date')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    department_id = fields.Many2one('stock.location', string='Department', domain=[('is_plant','=', True)])
    user_id = fields.Many2one('res.users', string='Indentor', default=lambda self: self.env.user)
    manager_id = fields.Many2one('res.users', string='Manager', related="department_id.manager_id", store=True)
    approve_user_id = fields.Many2one('res.users', string='Approved By')

    analytic_account_id = fields.Many2one('account.analytic.account', string='Project')

    indent_type = fields.Selection([('new', 'Purchase Indent'), ('existing', 'Repairing Indent')], string='Type')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('waiting_approval', 'Waiting for Approval'), ('inprogress', 'In Progress'), ('received', 'Received'), ('reject', 'Rejected')], string='State')

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')], string='Receive Method')

    equipment_id = fields.Many2one('indent.equipment', string='Equipment')
    equipment_section_id = fields.Many2one('indent.equipment.section', string='Section')

    line_ids = fields.One2many('stock.indent.line', 'indent_id', string='Lines')
    description = fields.Text()


class IndentLine(models.Model):
    _name = 'stock.indent.line'
    _description = 'Indent Line'

    indent_id =  fields.Many2one('stock.indent', 'Indent', required=True, ondelete='cascade')
    name =  fields.Text('Purpose', required=True)
    product_id =  fields.Many2one('product.product', 'Product', required=True)
    original_product_id =  fields.Many2one('product.product', 'Product to be Repaired')
    produre_type =  fields.Selection([('make_to_stock', 'Stock'), ('make_to_order', 'Purchase')], string='Procure', required=True)
    product_uom_qty =  fields.Float('Quantity Required', digits_compute=dp.get_precision('Product UoS'), required=True)
    product_uom =  fields.Many2one('product.uom', 'Unit of Measure', required=True)

    product_uos_qty =  fields.Float('Quantity (UoS)' ,digits_compute=dp.get_precision('Product UoS'))
    product_uos =  fields.Many2one('product.uom', 'Product UoS')

    price_unit =  fields.Float('Price', required=True, digits_compute=dp.get_precision('Product Price'))
    price_subtotal =  fields.Float(compute='_compute_price_subtotal')
    qty_available =  fields.Float('In Stock')
    virtual_available =  fields.Float('Forecasted Qty')
    delay =  fields.Float('Lead Time', required=True)
    specification =  fields.Text('Specification')
    sequence = fields.Integer('Sequence')
    indent_type =  fields.Selection([('new', 'Purchase Indent'), ('existing', 'Repairing Indent')], 'Type')

    @api.multi
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_uom_qty
