
from odoo import fields, models


class GodaddyConfigSettings(models.TransientModel):
    _inherit = 'website.config.settings'

    godaddy_api_key = fields.Char(
        related='website_id.godaddy_api_key',
        string='Godaddy API Key',
        help="Godaddy API key you can get it from https://developer.godaddy.com/keys")
    godaddy_api_secret = fields.Char(
        related='website_id.godaddy_api_secret',
        string='Godaddy API secret')
