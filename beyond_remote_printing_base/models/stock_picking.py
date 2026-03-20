# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def _action_done(self):
        res = super()._action_done()
        
        for picking in self.filtered(lambda p: p.state == 'done'):
            
            pdf_printer = picking.picking_type_id.printer_id.filtered(lambda p: p.pdf)[:1]
            picking_type_id = picking.picking_type_id
            
            if not pdf_printer:
                continue
            
            if picking_type_id.auto_print_delivery_slip_direct_print:
                self.env['remote.printer.task']._create_report_task(
                    printer_id=pdf_printer.id,
                    report_id='stock.report_deliveryslip',
                    res_id=picking.id,
                    res_model=picking._name,
                    quantity=picking_type_id.delivery_slip_qty,
                    printer_options={},
                    name=None)
                
        return res
    
    
