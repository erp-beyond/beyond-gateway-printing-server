from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    _description = 'Stock Picking Type'
    
    printer_id = fields.Many2many(comodel_name='remote.printer.printer', tracking=True)

    auto_print_delivery_slip_direct_print = fields.Boolean(tracking=True)
    delivery_slip_qty = fields.Integer(string="Qty", default=1, tracking=True)
  
    @api.constrains('delivery_slip_qty','auto_print_delivery_slip_direct_print')
    def constrain_delivery_slip_qty(self):
        for record in self:
            if record.delivery_slip_qty < 1 and record.auto_print_delivery_slip_direct_print:
                raise ValidationError(_("The quantity must be greater than 0."))
    
    def _get_pdf_printer(self):
        self.ensure_one()
        return self.printer_id.filtered(lambda p: p.pdf)[:1]
    
    def _get_zpl_printer(self):
        self.ensure_one()
        return self.printer_id.filtered(lambda p: p.zpl)[:1]
        
    def _get_printer(self,label_type):
        self.ensure_one()
        
        printers = self.printer_id.filtered(lambda p: label_type in p.default_label_type_id)
        
        if printers:
            return printers[0]
        
        return None