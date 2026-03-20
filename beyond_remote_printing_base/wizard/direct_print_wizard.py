from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import urllib.parse

class DirectPrintWizard(models.TransientModel):
    _name = "print.direct.wizard"
    _description = "print.direct.wizard"

    name = fields.Char(string="Label For", readonly=True)
    printer_id = fields.Many2one("remote.printer.printer", string="Printer")
    print_lines = fields.One2many(comodel_name='print.direct.wizard.line',inverse_name='wizard_id')
    res_partner_id = fields.Many2one("res.partner", string="Partner")
    allowed_printer_ids = fields.Many2many(comodel_name='remote.printer.printer')
    company_id = fields.Many2one(comodel_name="res.company", string="Company", default=lambda self: self.env.company)

    @api.onchange('printer_id')
    def onchange_printer_id(self):
        self.print_lines.printer_id = self.printer_id

    @api.onchange('res_partner_id')
    def onchange_res_partner_id(self):
        self.print_lines.partner_id = self.res_partner_id
        
    def action_print(self):
        self.ensure_one()
        for line in self.print_lines:
            line.action_print()
            
        self.env['bus.bus']._sendone(
            self.env.user.partner_id,
            'simple_notification',
            {
                'title': 'Confirmation',
                'message': 'Your action has been successfully confirmed!',
                'type': 'success',
                'sticky': False,
            }
        )
        return {
            'type': 'ir.actions.act_window_close'
        }
            
    @api.model
    def create_wizard(self,name='name'):
        return self.create({
            'name': name
        })
    
    def set_report_printer_domain(self):
        printers = self.env['remote.printer.printer'].search([('pdf','=',True)])
        self.allowed_printer_ids = printers
        self.print_lines.allowed_printer_ids = printers
        
        for line in self.print_lines:
            if not line.printer_id and line.allowed_printer_ids:
                line.printer_id = line.allowed_printer_ids[0]
        
    def set_zpl_printer_domain(self):
        printers = self.env['remote.printer.printer'].search([('zpl','=',True)])
        self.allowed_printer_ids = printers
        self.print_lines.allowed_printer_ids = printers
    
    def add_report_line(self,name,res_id,res_model,ir_report_id,print_qty,printer=None,partner=None,printer_options=None):
        self.ensure_one()
        
        if isinstance(ir_report_id, str):
            ir_report_id = self.env['ir.actions.report']._get_report_from_name(report_name=ir_report_id).id 
                                                                  
        
        name = name.replace('/','-')
                                                               
        line = self.env['print.direct.wizard.line'].create({
            'wizard_id': self.id,
            'print_job_type': 'pdf',
            'name': name,
            'res_id': res_id,
            'res_model': res_model,
            'res_func': 'print_report',
            'print_qty': print_qty,
            'printer_id': printer.id if printer else False,
            'report_id': ir_report_id,
            'partner_id': partner.id if partner else False,
            'printer_options': printer_options,
        })
        
        self.set_report_printer_domain()
        return line
    
    def add_zpl_line(self,name,res_id,res_model,res_func,print_qty,printer=None,partner=None,label_type=None):
        self.ensure_one()

        if label_type:
            printer = self.env['remote.printer.printer'].search(([('default_label_type_id','=',label_type)]))
            if printer:
                printer_id = printer[0].id

        if partner:
            res_partner_id = partner.id
        else:
            res_partner_id = self.res_partner_id.id
            
        name = name.replace('/','-')
        
        line = self.env['print.direct.wizard.line'].create({
            'wizard_id': self.id,
            'name': name,
            'res_id': res_id,
            'res_model': res_model,
            'res_func': res_func,
            'print_qty': print_qty,
            'printer_id': printer.id if printer else False,
            'partner_id': res_partner_id
        })
        
        self.set_zpl_printer_domain()
        return line
    
    def open_wizard(self):
        self.ensure_one()
                
        if self.print_lines:
            return {
                "name": "Print",
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "print.direct.wizard",
                "res_id": self.id,
                "target": "new",
            }
        
        raise UserError(_('No Print lines created'))


class DirectPrintWizardLine(models.TransientModel):
    _name = "print.direct.wizard.line"
    _description = "print.direct.wizard.line"

    wizard_id = fields.Many2one(comodel_name='print.direct.wizard')
    company_id = fields.Many2one(comodel_name="res.company", related='wizard_id.company_id', string="Company", store=True)
    
    print_job_type = fields.Selection([('zpl','ZPL'),('pdf','PDF')],string="Print Job Type",default='zpl')

    res_id = fields.Integer(string="id", required=True,readonly=True)
    model_name = fields.Char()
    res_model = fields.Char(string="model", required=True,readonly=True)
    res_func = fields.Char(string="function", required=False,readonly=True)
    partner_id = fields.Many2one("res.partner", string="Partner")

    name = fields.Char(string='Name', readonly=True)
    print_qty = fields.Integer(string="Print Count", required=True)
    printer_id = fields.Many2one("remote.printer.printer", string="Printer")

    zpl_value = fields.Char(compute='_compute_zpl_value')
    
    report_id = fields.Many2one(comodel_name='ir.actions.report', string='Report', readonly=True)
    printer_options = fields.Json(string='Printer Options')
    
    allowed_printer_ids = fields.Many2many(comodel_name='remote.printer.printer')

    def action_print(self):
        self.ensure_one()

        if not self.printer_id:
            raise UserError(_('No Printer Selected for print line %s'%self.name))
        
        if self.print_job_type == 'zpl':
            self.action_print_zpl()
            
        if self.print_job_type == 'pdf':
            self.action_print_pdf()
            
    def action_print_zpl(self):
        obj = self.env[self.res_model].browse(self.res_id)
        func = getattr(obj, self.res_func)
        return func(self)
    
    def action_print_pdf(self):
        self.printer_id._create_report_task(name=self.name,report_id=self.report_id.id,res_id=self.res_id,res_model=self.res_model,quantity=self.print_qty,printer_options=self.printer_options)
        
    def action_preview_label(self):
        self.ensure_one()
        if  self.print_job_type == 'pdf':
            return self.action_preview_label_pdf()

        if self.print_job_type == 'zpl':
            return self.action_preview_zpl()
    
    def action_preview_label_pdf(self):
        self.ensure_one()

        report = self.report_id
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(report.report_name, [self.res_id])
        filename = f"{self.name.replace('/','-') or 'report'}.pdf"
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'})

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }
        
    def action_preview_zpl(self):
        self.ensure_one()
        if self.print_job_type != 'zpl':
            return
        
        ctx = self.env.context.copy()
        ctx['label_preview'] = True
        self.env.context = ctx

        obj = self.env[self.res_model].browse(self.res_id)
        func = getattr(obj, self.res_func)
        zpl_string =  func(self)

        base_url = 'https://labelary.com/viewer.html'
        encoded_zpl = urllib.parse.quote(zpl_string)  # Encode the ZPL string for the URL
        
        label_width = self.env.context.get('preview_label_width') or 200
        label_height = self.env.context.get('preview_label_height') or 200

        units = 'mm'
        preview_url = f'{base_url}?zpl={encoded_zpl}&width={label_width}&height={label_height}&units={units}'

        return {
            'type': 'ir.actions.act_url',
            'url': preview_url,
            'target': 'new',
        }
        
    def _compute_zpl_value(self):
        for rec in self:
            if rec.print_job_type != 'zpl':
                rec.zpl_value = False
                continue
            
            ctx = self.env.context.copy()
            ctx['label_preview'] = True
            self.env.context = ctx

            obj = self.env[rec.res_model].browse(rec.res_id)
            func = getattr(obj, rec.res_func)
            zpl_string =  func(self)
            
            rec.zpl_value = zpl_string 