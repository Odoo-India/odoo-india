# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pprint
import urlparse

from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class CCAvenueController(http.Controller):
    @http.route(['/payment/ccavenue/return', '/payment/ccavenue/cancel'], type='http', auth='public', csrf=False)
    def ccavenue_return(self, **post):
        _logger.info('CCAvenue: Entering form_feedback with post data %s', pprint.pformat(post))
        if post:
            PaymentAcquirer = request.env['payment.acquirer']
            key = PaymentAcquirer.search([('provider', '=', 'ccavenue')], limit=1).ccavenue_working_key
            post = PaymentAcquirer._ccavenue_encrypted_response(post, key)
            request.env['payment.transaction'].sudo().form_feedback(post, 'ccavenue')
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        return request.render('payment_ccavenue.payment_ccavenue_redirect', {
            'return_url': '%s' % urlparse.urljoin(base_url, '/shop/payment/validate')
        })
