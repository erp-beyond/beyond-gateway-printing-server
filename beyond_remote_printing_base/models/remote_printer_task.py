from odoo import _, api, fields, models
from datetime import datetime, timedelta
import base64


class RemotePrinterTask(models.Model):
    _name = "remote.printer.task"
    _description = "Remote Printer Task"

    name = fields.Char("Name")
    printer_id = fields.Many2one(
        comodel_name="remote.printer.printer", string="Remote Printer", required=True
    )
    server_id = fields.Many2one(
        comodel_name="remote.printer.server",
        related="printer_id.server_id",
        string="Remote printer Server",
    )
    res_id = fields.Integer(string="id", readonly=True)
    res_model = fields.Char(string="model", readonly=True)
    quantity = fields.Integer("Quantity", readonly=True)
    odoo_production_task_id = fields.Integer(
        string='Production Task ID',
        help='Task ID on the production Odoo instance, used to sync state back.',
        readonly=True,
    )
    task_server_identifier = fields.Integer(
        string='Task Server Identifier',
        help='Identifier of the relay server this task is routed to. Used for routing in multi-server setups.',
        readonly=True,
    )

    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("sent", "Sent"),
            ("cancel", "Cancelled"),
            ("error", "Error"),
        ],
        readonly=True,
        default="pending",
    )

    task_type = fields.Selection(
        [("zpl", "ZPL"), ("pdf", "PDF")], string="Task Type", readonly=True
    )

    zpl_data = fields.Char("ZPL data", readonly=True)

    report_id = fields.Many2one(
        comodel_name="ir.actions.report", string="Report", readonly=True
    )

    printer_options = fields.Json(string="Printer Options", readonly=True)

    @api.model
    def _create_zpl_task(
        self, printer_id, zpl, res_id, res_model, quantity=1, name=None
    ):

        if quantity == 0:
            return None

        if not name:
            name = self.build_task_name()

        name = name.replace("/", "-")

        self.create(
            {
                "printer_id": printer_id,
                "res_id": res_id,
                "res_model": res_model,
                "name": name,
                "state": "pending",
                "task_type": "zpl",
                "zpl_data": zpl,
                "quantity": quantity,
            }
        )

        return True

    @api.model
    def _create_report_task(
        self,
        printer_id,
        report_id,
        res_id,
        res_model,
        quantity=1,
        printer_options={},
        name=None,
    ):

        if quantity == 0:
            return None

        if not name:
            name = self.build_task_name()

        if isinstance(report_id, str):
            report_id = (
                self.env["ir.actions.report"]
                ._get_report_from_name(report_name=report_id)
                .id
            )

        name = name.replace("/", "-")

        self.create(
            {
                "printer_id": printer_id,
                "res_id": res_id,
                "res_model": res_model,
                "name": name,
                "state": "pending",
                "task_type": "pdf",
                "report_id": report_id,
                "quantity": quantity,
                "printer_options": printer_options,
            }
        )

        return True

    @api.model
    def build_task_name(self):
        sequence = (
            self.env["ir.sequence"].sudo().search([("code", "=", "remote-print-task")])
        )
        if not sequence:
            values = {
                "name": "remote-print-task",
                "code": "remote-print-task",
                "prefix": "PRINT-R" + "-",
                "padding": 7,
                "company_id": self.env.company.id,
            }
            sequence = self.env["ir.sequence"].sudo().create(values)
        return sequence.next_by_id()

    @api.model
    def cron_cleanup_tasks(self):

        # we keep stuff for 2 weeks
        two_weeks = datetime.now() - timedelta(days=14)
        candidates = self.search([("create_date", "<", two_weeks)])
        candidates.unlink()

    def set_error(self):
        self.state = "error"
        return True

    def set_in_progress(self):
        self.state = "in_progress"
        return True

    def set_done(self):
        self.state = "sent"
        return True

    def cancel(self):
        tasks = self.filtered(lambda t: t.state in ("pending", "in_progress"))
        tasks.state = "cancel"

    @api.model
    def get_pdf_data(self, report_id, task_id):
        report_id = report_id[0]
        report = self.env["ir.actions.report"].browse(report_id)
        if not report:
            raise ValueError("Report not found")
        res_id = self.env["remote.printer.task"].search([("id", "=", task_id)]).res_id
        pdf_data, _ = report._render_qweb_pdf(report.report_name, res_ids=[res_id])

        return base64.b64encode(pdf_data).decode("utf-8")

    @api.model
    def create_from_production(self, task_vals):
        """
        Called by production Odoo via XML-RPC.P
        Finds the correct printer by technical name and creates the task.
        """
        printer = self.env['remote.printer.printer'].sudo().search([
            ('technical_name', '=', task_vals.get('printer_technical_name'))
        ], limit=1)

        get_param = self.env['ir.config_parameter'].sudo().get_param
        relay_server_id = get_param('remote_printing_relay.default_server_id')
        relay_server = self.env['remote.printer.relay.server'].browse(int(relay_server_id)) if relay_server_id else None

        if not printer:
            raise ValueError(f"Printer not found: {task_vals.get('printer_technical_name')}")

        report_id = False
        if task_vals.get('task_type') == 'pdf' and task_vals.get('report_xml_id'):
            xml_id = task_vals.get('report_xml_id')
            try:
                report = self.env.ref(xml_id)
                report_id = report.id
            except Exception:
                report_id = False

        self.sudo().create({
            'name': task_vals.get('name'),
            'printer_id': printer.id,
            'res_id': task_vals.get('res_id'),
            'res_model': task_vals.get('res_model'),
            'quantity': task_vals.get('quantity', 1),
            'task_type': task_vals.get('task_type'),
            'zpl_data': task_vals.get('zpl_data') or False,
            'report_id': report_id,
            'printer_options': task_vals.get('printer_options') or {},
            'state': 'pending',
            'odoo_production_task_id': task_vals.get('odoo_production_task_id'),
            'task_server_identifier': relay_server.server_identifier if relay_server else None,
        })

        return True
