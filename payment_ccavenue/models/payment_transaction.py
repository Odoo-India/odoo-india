# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare


_logger = logging.getLogger(__name__)


class PaymentTransactionCCAvenue(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _ccavenue_form_get_tx_from_data(self, data):
        """ Given a data dict coming from ccavenue, verify it and find the related
        transaction record. """
        reference = data.get('order_id')
        if not reference:
            raise ValidationError(_('CCAvenue: received data with missing reference (%s)') % (reference))

        transaction = self.search([('reference', '=', reference)])
        if not transaction or len(transaction) > 1:
            error_msg = _('CCAvenue: received data for reference %s') % (reference)
            if not transaction:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            raise ValidationError(error_msg)
        return transaction

    @api.model
    def _ccavenue_form_get_invalid_parameters(self, transaction, data):
        invalid_parameters = []

        if transaction.acquirer_reference and data.get('order_id') != transaction.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', data.get('order_id'), transaction.acquirer_reference))
        #check what is buyed
        if float_compare(float(data.get('amount', '0.0')), transaction.amount, 2) != 0:
            invalid_parameters.append(('Amount', data.get('amount'), '%.2f' % transaction.amount))

        return invalid_parameters

    @api.model
    def _ccavenue_form_validate(self, transaction, data):
        if transaction.state == 'done':
            _logger.warning('CCAvenue: trying to validate an already validated tx (ref %s)' % transaction.reference)
            return True
        status_code = data.get('order_status')
        if status_code == "Success":
            transaction.write({
                'state': 'done',
                'acquirer_reference': data.get('tracking_id'),
                'date_validate': fields.Datetime.now(),
            })
            return True
        elif status_code == "Aborted":
            transaction.write({
                'state': 'cancel',
                'acquirer_reference': data.get('tracking_id'),
                'date_validate': fields.Datetime.now(),
            })
            return True
        else:
            error = data.get('failure_message')
            _logger.info(error)
            transaction.write({
                'state': 'error',
                'state_message': error,
            })
            return False
