from odoo import _, api, fields, models

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'
    
    printer_id = fields.Many2many(comodel_name='remote.printer.printer')
    
    def _get_printer(self,label_type):
        self.ensure_one()
        
        printers = self.printer_id.filtered(lambda p: label_type in p.default_label_type_id)
        
        if printers:
            return printers[0]
        
        return None