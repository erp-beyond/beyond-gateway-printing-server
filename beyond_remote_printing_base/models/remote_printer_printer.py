from odoo import _, api, fields, models
from datetime import datetime

class RemotePrinterPrinter(models.Model):
    _name = 'remote.printer.printer'
    _description = 'Remote Printer Printer'
    _order = 'sequence, id'
    
    sequence = fields.Integer('Sequence', default=10)
    
    name = fields.Char('Name', required=True)
    technical_name = fields.Char('Technical name', required=True)
    default_label_type_id = fields.Many2many(comodel_name='label.type')
    state = fields.Char(string='State',readonly=True)
    server_id = fields.Many2one(comodel_name='remote.printer.server',string='Remote Server', required=True)

    task_ids = fields.One2many(comodel_name='remote.printer.task',inverse_name='printer_id',string='Tasks',readonly=True)

    zpl = fields.Boolean('Print ZPL')

    pdf = fields.Boolean('Print PDF')
    
    cancel_tasks = fields.Boolean()

    #Called from remote printer server
    def get_next_task(self):
        self.ensure_one()
        self.server_id.last_connection = datetime.now()
        task = self._get_next_task()
        
        if task:
            return task.read()[0]
        return False
          
    def _get_next_task(self):
        self.ensure_one()
        tasks = self.task_ids.filtered(lambda j: j.state == 'in_progress').sorted(key=lambda j:j.id)
        if tasks:
            return tasks[0]
        tasks = self.task_ids.filtered(lambda j: j.state == 'pending').sorted(key=lambda j:j.id)
        if tasks:
            return tasks[0]
        return False
    
    def set_cancel_tasks(self):
        self.task_ids.cancel()
        self.cancel_tasks = True
        return True
    
    def reset_cancel_tasks(self):
        self.cancel_tasks = False
        return True
    
    def _create_zpl_task(self,zpl,res_id,res_model,quantity=1):
        self.ensure_one()
        return self.env['remote.printer.task']._create_zpl_task(self.id,zpl,res_id,res_model,quantity)

    def _create_report_task(self,report_id,res_id,res_model,quantity=1,printer_options={},name=None):
        self.ensure_one()
        return self.env['remote.printer.task']._create_report_task(printer_id=self.id,report_id=report_id,res_id=res_id,res_model=res_model,quantity=quantity,printer_options=printer_options,name=name)