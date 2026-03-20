from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_printing = fields.Boolean(string="Enable Remote Printing")
