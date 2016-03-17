# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from openerp import models, fields, _
from openerp.exceptions import ValidationError

from aramex_request import AramexRequest


_logger = logging.getLogger(__name__)


class ProviderAramex(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('aramex', "aramex")])

    aramex_user_name = fields.Char(string="User Name")
    aramex_password = fields.Char(string="Password")
    aramex_version = fields.Char(string="Version")
    aramex_account_number = fields.Char(string="Account Number")
    aramex_account_entity = fields.Char(string="Account Entity")
    aramex_account_pin = fields.Char(string="Account Pin Number")
    aramex_country_code = fields.Char(string="Account Country Code")
    aramex_test_mode = fields.Boolean(default=True, string="Test Mode", help="Uncheck this box to use production aramex Web Services")
    aramex_weight_unit = fields.Selection([('LB', 'LB'), ('KG', 'KG')], default='LB')
    aramex_package_dimension_unit = fields.Selection([('IN', 'Inches'), ('CM', 'Centimeters')], string="Units for UPS Package Size", default='IN')
    aramex_package_height = fields.Integer(string='Package Height', help="Fixed height if not provided on the product packaging.")
    aramex_package_width = fields.Integer(string='Package Width', help="Fixed width if not provided on the product packaging.")
    aramex_package_length = fields.Integer(string='Package Length', help="Fixed length if not provided on the product packaging.")

    def aramex_get_shipping_price_from_so(self, orders):
        res = []
        for order in orders:
            price = 0.0
            total_qty = 0
            total_weight = 0
            # Estimate weight of the sale order; will be definitely recomputed on the picking field "weight"
            for line in order.order_line.filtered(lambda line: not line.is_delivery):
                total_qty += line.product_uom_qty
                total_weight += line.product_id.weight * line.product_uom_qty
            weight = _convert_weight(total_weight, self.aramex_weight_unit)
            # Authentication stuff
            srm = AramexRequest(request_type="rating", test_mode=self.aramex_test_mode)
            srm.client_info(self.aramex_user_name, self.aramex_password, self.aramex_version, self.aramex_account_number, self.aramex_account_pin, self.aramex_account_entity, self.aramex_country_code)

            # Build basic rating request and set addresses
            srm.transaction_detail(order.name)
            srm.set_shipper(order.company_id.partner_id, order.warehouse_id.partner_id)
            srm.set_recipient(order.partner_id)
            srm.add_package(self, weight, int(total_qty))

            request = srm.rate()

            if request.get('errors_message'):
                raise ValidationError(request['errors_message'])

            if order.currency_id.name == request['currency']:
                price = request['price']
            else:
                request_currency = self.env['res.currency'].search([('name', '=', request['currency'])], limit=1)
                price = request_currency.compute(float(request['price']), order.currency_id)

            res = res + [price]
        return res

    def aramex_send_shipping(self, pickings):
        res = []

        for picking in pickings:
            net_weight = _convert_weight(picking.weight, self.aramex_weight_unit)

            srm = AramexRequest(request_type="shipping", test_mode=self.aramex_test_mode)
            srm.client_info(self.aramex_user_name, self.aramex_password, self.aramex_version, self.aramex_account_number, self.aramex_account_pin, self.aramex_account_entity, self.aramex_country_code)

            srm.transaction_detail(picking.id)
            srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id, self.aramex_account_number, 'shipping')
            srm.set_recipient(picking.partner_id, 'shipping')
            srm.add_package(self, net_weight)
            srm.send_shipping()
            srm.label_info()
            shipping = srm.send_shipment()
            if shipping.get('errors_message'):
                raise ValidationError(shipping['errors_message'])
            carrier_tracking_ref = shipping['tracking_number']
            logmessage = (_("Shipment created into Aramex <br/> <b>Tracking Number: </b>%s") % (carrier_tracking_ref))
            attachments= srm.get_label()
            if attachments:
                attachments = [('LabelAramex-%s.pdf' % carrier_tracking_ref, attachments)]
            picking.message_post(body=logmessage, attachments=attachments)
            shipping_data = {'exact_price': 100 ,
            'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
        return res

    def aramex_get_tracking_link(self, pickings):
        res = []
        for picking in pickings:
            res = res + ['http://www.aramex.com/express/track_results_multiple.aspx?ShipmentNumber=%s' % picking.carrier_tracking_ref]
        return res

def _convert_weight(weight, unit='KG'):
    ''' Convert picking weight (always expressed in KG) into the specified unit '''
    if unit == 'KG':
        return weight
    elif unit == 'LB':
        return weight / 0.45359237
    else:
        raise ValueError
