from odoo import _, api, fields, models

class remotePrinterServer(models.Model):
    _name = 'remote.printer.server'
    _description = 'remote.printer.server'

    name = fields.Char('Name', required=True)
    technical_name = fields.Char('Technical name', required=True)

    online = fields.Boolean('Online', readonly=True)
    last_connection = fields.Datetime('Last Connection',readonly=True)

    printer_ids = fields.One2many(comodel_name='remote.printer.printer',inverse_name='server_id',string='Printers')
    api_key = fields.Char('API Key')
    production_url = fields.Char('Production URL')
    production_db = fields.Char('Production DB')
    
    @api.model
    def create(self, vals):
        """Encrypt API key before storing."""
        if 'api_key' in vals and vals['api_key']:
            vals['api_key'] = self._encrypt_api_key(vals['api_key'])
        return super().create(vals)
    
    def write(self, vals):
        """Encrypt API key before updating."""
        if 'api_key' in vals and vals['api_key']:
            vals['api_key'] = self._encrypt_api_key(vals['api_key'])
        return super().write(vals)
    
    @staticmethod
    def _encrypt_api_key(api_key):
        """Encrypt the API key (simple base64 encoding - use proper encryption in production)."""
        import base64
        return base64.b64encode(api_key.encode()).decode()
    
    @staticmethod
    def _decrypt_api_key(encrypted_key):
        """Decrypt the API key."""
        import base64
        try:
            return base64.b64decode(encrypted_key.encode()).decode()
        except Exception:
            return encrypted_key
    
    def get_api_key(self):
        """Get decrypted API key."""
        return self._decrypt_api_key(self.api_key) if self.api_key else ''
    
    def set_cancel_tasks(self):
        self.printer_ids.set_cancel_tasks()