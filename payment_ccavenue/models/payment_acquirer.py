# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import md5
import urlparse
from Crypto.Cipher import AES

from odoo import api, fields, models


class PaymentAcquirerCCAvenue(models.Model):
    _inherit = 'payment.acquirer'

    ccavenue_merchant_id = fields.Char(string='Merchant ID', required_if_provider='ccavenue')
    ccavenue_access_code = fields.Char(string='Access Code', required_if_provider='ccavenue')
    ccavenue_working_key = fields.Char(string='Working Key', required_if_provider='ccavenue')

    def _get_ccavenue_urls(self, environment):
        """ CCAvenue URLs"""
        if environment == 'prod':
            return {'ccavenue_form_url': 'https://secure.ccavenue.com/transaction/transaction.do?command=initiateTransaction'}
        else:
            return {'ccavenue_form_url': 'https://test.ccavenue.com/transaction/transaction.do?command=initiateTransaction'}

    @api.model
    def _get_providers(self):
        providers = super(PaymentAcquirerCCAvenue, self)._get_providers()
        providers.append(['ccavenue', 'CCAvenue'])
        return providers

    def ccavenue_pad(self, data):
        length = 16 - (len(data) % 16)
        data += chr(length)*length
        return data

    def _ccavenue_encrypted_request(self, values):
        iv = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        keys = 'merchant_id+order_id+currency+amount+redirect_url+cancel_url+language+billing_name+billing_address+billing_city+billing_state+billing_zip+billing_country+billing_tel+billing_email+delivery_name+delivery_address+delivery_city+delivery_state+delivery_zip+delivery_country+delivery_tel+merchant_param1+merchant_param2+merchant_param3+merchant_param4+merchant_param5+promo_code+customer_identifier'.split('+')
        sign = ''.join('%s=%s&' % (k, values.get(k)) for k in keys)
        plainText = self.ccavenue_pad(sign)
        encDigest = md5.new()
        encDigest.update(self.ccavenue_working_key)
        enc_cipher = AES.new(encDigest.digest(), AES.MODE_CBC, iv)
        encryptedText = enc_cipher.encrypt(plainText).encode('hex')
        return encryptedText

    def _ccavenue_encrypted_response(self, values, key):
        dncryptedText = {}
        iv = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        decDigest = md5.new()
        decDigest.update(key)
        encryptedText = values.get('encResp').decode('hex')
        dec_cipher = AES.new(decDigest.digest(), AES.MODE_CBC, iv)
        result = dec_cipher.decrypt(encryptedText)
        vals = result.split('&')
        for data in vals:
            temp = data.split('=')
            dncryptedText[temp[0]] = temp[1]
        return dncryptedText

    @api.multi
    def ccavenue_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        ccavenue_values = dict(values,
                               access_code=self.ccavenue_access_code,
                               merchant_id=self.ccavenue_merchant_id,
                               order_id=values.get('reference'),
                               currency=values.get('currency').name,
                               amount=values.get('amount'),
                               redirect_url='%s' % urlparse.urljoin(base_url, '/payment/ccavenue/return'),
                               cancel_url='%s' % urlparse.urljoin(base_url, '/payment/ccavenue/cancel'),
                               language='EN',
                               billing_name=values.get('partner_name'),
                               billing_address=values.get('partner_address'),
                               billing_city=values.get('partner_city'),
                               billing_state='',
                               billing_zip=values.get('partner_zip'),
                               billing_country=values.get('partner_country').name,
                               billing_tel=values.get('partner_phone'),
                               billing_email=values.get('partner_email'),
                               delivery_name=values.get('partner_name'),
                               delivery_address=values.get('partner_address'),
                               delivery_city=values.get('partner_city'),
                               delivery_state='',
                               delivery_zip=values.get('partner_zip'),
                               delivery_country=values.get('partner_country').name,
                               delivery_tel=values.get('partner_phone'),
                               merchant_param1='',
                               merchant_param2='',
                               merchant_param3='',
                               merchant_param4='',
                               merchant_param5='',
                               promo_code='',
                               customer_identifier=''
                               )

        ccavenue_values['encRequest'] = self._ccavenue_encrypted_request(ccavenue_values)
        return ccavenue_values

    @api.multi
    def ccavenue_get_form_action_url(self):
        self.ensure_one()
        return self._get_ccavenue_urls(self.environment)['ccavenue_form_url']
