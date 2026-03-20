from odoo import _, api, fields, models

class remotePrinterServer(models.Model):
    _name = 'remote.printer.server'
    _description = 'remote.printer.server'

    name = fields.Char('Name', required=True)
    technical_name = fields.Char('Technical name', required=True)

    online = fields.Boolean('Online', readonly=True)
    last_connection = fields.Datetime('Last Connection',readonly=True)

    printer_ids = fields.One2many(comodel_name='remote.printer.printer',inverse_name='server_id',string='Printers')
    
    def set_cancel_tasks(self):
        self.printer_ids.set_cancel_tasks()