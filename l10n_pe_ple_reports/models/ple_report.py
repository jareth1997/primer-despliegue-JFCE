###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import _
from odoo.tools.translate import _, LazyTranslate
_lt = LazyTranslate(__name__, default_lang='en_US')

from odoo.addons.iap import jsonrpc

DEFAULT_IAP_ENDPOINT = "https://iap.odoofact.pe"

_logger = logging.getLogger(__name__)

# List codes for IAP token status
SUCCESS = 10
ERROR_TOKEN_RENEWED = 11
NOT_READY = 12
ERROR_INTERNAL = 1
ERROR_NOT_ACTIVE = 2
ERROR_EXPIRED = 3
ERROR_INVALID_SERVICE_TOKEN = 4
ERROR_TOKEN_ALREADY_USED = 5
ERROR_NO_TOKEN_FOR_SERVICE = 6
ERROR_INVALID_SERVICE_TOKEN = 7
ERROR_NO_CONNECTION = 8

# List codes for Report response
ERROR_NOT_ENOUGH_CREDIT = 21
ERROR_DATA_NOT_FOUND = 22

ERROR_MESSAGES = {
    SUCCESS: _lt("Your token is active"),
    ERROR_INTERNAL: _lt("An error occurred"),
    ERROR_NOT_ACTIVE: _lt(
        "Your token is waiting for activation, try again in a few hours."
    ),
    ERROR_EXPIRED: _lt("Your token has expired or has been canceled"),
    ERROR_INVALID_SERVICE_TOKEN: _lt(
        "Invalid token or does not exist. Please contact the administrator"
    ),
    ERROR_TOKEN_RENEWED: _lt("The token was linked to this database."),
    ERROR_TOKEN_ALREADY_USED: _lt(
        "The token already used in another database. Check your account at www.odoofact.com."
    ),
    ERROR_NO_TOKEN_FOR_SERVICE: _lt("The token is not valid for this Service."),
    ERROR_NO_CONNECTION: _lt("Server not available. Please retry later"),
    ERROR_NOT_ENOUGH_CREDIT: _lt(
        "You don't have enough credit to generate your PLE report."
    ),
    ERROR_DATA_NOT_FOUND: _lt(
        "There is no data found. Please remove the content of the TXT file before upload to SUNAT."
    ),
}


class PleReport(models.AbstractModel):
    _name = "l10n_pe.ple.report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "PLE Reports"
    _check_company_auto = True

    @api.depends("report_status_code", "company_id.l10n_pe_ple_test")
    def _compute_error_message(self):
        for record in self:
            if record.report_status_code not in (SUCCESS, NOT_READY):
                if ERROR_TOKEN_RENEWED == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_TOKEN_RENEWED],
                    )
                elif NOT_READY == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[NOT_READY],
                    )
                elif ERROR_NOT_ACTIVE == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_NOT_ACTIVE],
                    )
                elif ERROR_EXPIRED == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_EXPIRED],
                    )
                elif ERROR_INVALID_SERVICE_TOKEN == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_INVALID_SERVICE_TOKEN],
                    )
                elif ERROR_TOKEN_ALREADY_USED == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_TOKEN_ALREADY_USED],
                    )
                elif ERROR_NO_TOKEN_FOR_SERVICE == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_NO_TOKEN_FOR_SERVICE],
                    )
                elif ERROR_INVALID_SERVICE_TOKEN == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_INVALID_SERVICE_TOKEN],
                    )
                elif ERROR_NO_CONNECTION == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_NO_CONNECTION],
                    )
                elif ERROR_NOT_ENOUGH_CREDIT == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_NOT_ENOUGH_CREDIT],
                    )
                elif ERROR_DATA_NOT_FOUND == record.report_status_code:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_DATA_NOT_FOUND],
                    )
                else:
                    report_error_message = _("Report id %s: %s") % (
                        str(record.id),
                        ERROR_MESSAGES[ERROR_INTERNAL],
                    )
            else:
                report_error_message = ""
            print("report_error_message: ", report_error_message)
            report_test_message = ""
            if record.company_id.l10n_pe_ple_test:
                report_test_message = _(
                    "TEST MODE: Your database is limited to generate books of up to 30 records. Activate unlimited token. \n"
                )
            # Save the data
            record.report_error_message = report_test_message + report_error_message

    name = fields.Char(
        string="Name",
        copy=False,
        readonly=False,
        store=True,
        index=True,
        tracking=True,
        default="/",
    )
    code_type_ids = fields.Many2many(
        "ple.report.code",
        string="Allowed Codes from Report Type",
        related="ple_report_type_id.code_ids",
    )
    code_ids = fields.Many2many(
        "ple.report.code",
        string="Report Codes",
        help="Used to generate the Reports",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    compute_date = fields.Datetime(string="Compute Date", copy=False)
    date = fields.Date(
        string="Date",
        required=True,
        index=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        copy=False,
        default=fields.Date.context_today,
    )
    date_from = fields.Date(
        string="From",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=-1, day=1)).date()
        ),
    )
    date_to = fields.Date(
        string="To",
        required=True,
        readonly=True,
        # states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(day=1, days=-1)).date()
        ),
    )
    file_ids = fields.One2many(
        "ple.report.file", "report_id", string="Report Files", copy=False
    )
    files_count = fields.Integer(string="Files Count", compute="_compute_line_count")
    line_ids = fields.One2many(
        "l10n_pe.ple.report.line",
        "report_id",
        string="Report lines",
        copy=True,
        readonly=True,
        # states={"draft": [("readonly", False)], "in_progress": [("readonly", False)]},
    )
    lines_count = fields.Integer(string="Lines Count", compute="_compute_line_count")
    error_lines_count = fields.Integer(
        string="Error Lines Count", compute="_compute_line_count"
    )
    opportunity_eeff_code = fields.Selection(
        string="Code Opportunity EEFF",
        selection=[]
    )
    operations_indicator = fields.Selection(
        selection=[
            ("0", "0- Cierre de operaciones - baja de inscripción en el RUC"),
            ("1", "1- Empresa o entidad operativa"),
            ("2", "2- Cierre del libro - no obligado a llevarlo"),
        ],
        string="Operations Indicator",
        required=True,
        tracking=True,
        default="1",
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )
    period = fields.Char(string="Period", compute="_compute_date_from")
    ple_report_type_id = fields.Many2one(
        "l10n_pe.ple.report.type", "PLE Report Type", required=True, index=True
    )
    ple_remote_id = fields.Char(string="PLE remote ID", readonly=True)
    ple_test_mode = fields.Boolean(
        "Test mode", related="company_id.l10n_pe_ple_test", readonly=True
    )
    content_indicator = fields.Selection(
        selection=[
            ("0", "0- Sin informacion"),
            ("1", "1- Con Informacion"),
        ],
        string="Content Indicator",
        required=True,
        compute="_compute_content_indicator",
    )
    currency_indicator = fields.Selection(
        selection=[
            ("1", "1- Soles"),
            ("2", "2- US Dolares"),
        ],
        string="Currency Indicator",
        required=True,
        tracking=True,
        default="1",
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("verified", "Verified"),
            ("in_progress", "In Progress"),
            ("posted", "Posted"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="draft",
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        index=True,
        tracking=2,
        default=lambda self: self.env.user,
        readonly=True,
        # states={"draft": [("readonly", False)]},
    )
    warning_message = fields.Text(string="Warning message", default="")

    # IAP Methods
    report_status_code = fields.Integer("Status code", copy=False)
    report_error_message = fields.Text("Error message", compute=_compute_error_message)
    report_remote_id = fields.Integer(
        "Id of the request to IAP-PLE",
        default="-1",
        help="PLE report id",
        copy=False,
        readonly=True,
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends("line_ids")
    def _compute_content_indicator(self):
        """compute if the report contain data"""
        for report in self:
            if report.line_ids:
                report.content_indicator = "1"
            else:
                report.content_indicator = "0"

    @api.depends("line_ids", "line_ids.line_has_error", "file_ids")
    def _compute_line_count(self):
        for report in self:
            report.lines_count = 0
            report.files_count = 0
            report.error_lines_count = 0
            if report.line_ids:
                report.lines_count = len(report.line_ids)
                report.error_lines_count = len(
                    report.line_ids.filtered(lambda line: line.line_has_error)
                )
            if report.file_ids:
                report.files_count = len(report.file_ids)

    @api.depends("date_from")
    def _compute_date_from(self):
        for report in self:
            if report.date_from:
                report.period = report.date_from.strftime("%Y-%m")
            else:
                report.period = ""

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange("ple_report_type_id", "period")
    def _onchange_ple_report_type_id(self):
        """Compute the report name"""
        if self.ple_report_type_id:
            self.code_ids = self.ple_report_type_id.code_ids and self.ple_report_type_id.code_ids.ids or False
        if self.ple_report_type_id and self.period:
            self.name = "%s | %s" % (self.period, self.ple_report_type_id.name)
        else:
            self.name = "/"

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _get_move_domain(self):
        """Return domain base for report lines by company and dates"""
        return [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]

    def _get_allowed_document_type_ids(self):
        """Return configured document type ids for this report type (or empty)."""
        self.ensure_one()
        return self.ple_report_type_id.allowed_document_type_ids.ids

    def _get_report_lines(self):
        """Get the report lines"""
        self.ensure_one()
        result = {}
        domain = self._get_move_domain()
        move_ids = self.env["account.move"].search(domain)
        for move in sorted(move_ids, key=lambda x: x.date):
            # create/overwrite the rule in the temporary results
            move_line_ids = move.line_ids.filtered(lambda l: l.display_type != 'line_section' and l.display_type != 'line_note')
            result[move.id] = {
                "move_id": move.id,
                "move_line_id": move_line_ids and move_line_ids[0].id or False,
                "manual": False,
                "report_id": self.id,
            }
        return result.values()

    def compute_lines(self):
        reports = self.filtered(lambda r: r.state in ["draft", "in_progress"])
        # delete old report lines
        reports.line_ids.filtered(lambda line: not line.manual).unlink()
        for report in reports:
            # number = report.number or self.env['ir.sequence'].next_by_code('salary.slip')
            lines = [(0, 0, line) for line in report._get_report_lines()]
            report.write({"line_ids": lines, "compute_date": fields.Datetime.now()})
            for line in report.line_ids:
                line._onchange_move_id()
                line._onchange_move_line_id()
        # delete old report files
        reports.file_ids.unlink()
        return True

    def verify_lines(self):
        reports = self.filtered(lambda r: r.state in ["draft"])
        for report in reports:
            warning_message = ""
            for line in report.line_ids:
                message = line.verify_line() or ""
                line.write(
                    {
                        "line_has_error": bool(message),
                        "line_error_message": message,
                        "line_verified_at": fields.Datetime.now(),
                    }
                )
                if message:
                    warning_message += message
            report.warning_message = warning_message
            # if not warning_message:
            #     report.write({"state": "verified"})
        return True

    def _get_txt_file_name(self, report_id=False, code_id=False):
        if report_id and code_id:
            txt_file_name = "LE%s%s%s%s%s%s%s%s%s1.txt" % (
                report_id.company_id.partner_id.vat,
                report_id.date_from.strftime("%Y"),
                report_id.date_from.strftime("%m"),
                report_id.opportunity_eeff_code or "00",
                code_id.code,
                report_id.opportunity_eeff_code,
                report_id.operations_indicator,
                report_id.content_indicator,
                report_id.currency_indicator,
            )
        else:
            txt_file_name = "TXT File"
        return txt_file_name

    def generate_report_files(self):
        """Verifica si hay algun error en los registros"""
        self.verify_lines()
        """Generate Report Files"""
        for report in self:
            ple_data = []
            for code in report.code_ids:
                txt_file_name = report._get_txt_file_name(report, code)
                data_lines = getattr(
                    report, "_get_data_lines_%s" % code.name.replace(".", "")
                )(self.line_ids)
                ple_data.append(
                    {
                        "code_id": code.id,
                        "code_name": code.name,
                        "code_description": code.description,
                        "period": report.period,
                        "ple_report_type_id": report.ple_report_type_id.id,
                        "report_id": report.id,
                        "txt_file_name": txt_file_name,
                        "data_lines": data_lines,
                    }
                )
            report_status_code = report.get_ple_data(ple_data)
            if report_status_code in [10, 11]:
                report.write({"state": "in_progress"})
        return True

    def get_ple_data(self, data):
        self.ensure_one()
        ir_params = self.env["ir.config_parameter"].sudo()
        default_endpoint = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("odoofact_iap_endpoint", DEFAULT_IAP_ENDPOINT)
        )
        iap_server_url = ir_params.get_param("l10n_pe_edi_endpoint", default_endpoint)

        user_token = self.env["iap.account"].get("l10n_pe_ple")
        dbuuid = self.env["ir.config_parameter"].sudo().get_param("database.uuid")
        params = {
            "client_service_token": self.company_id.l10n_pe_ple_token,
            "ple_remote_id": self.ple_remote_id,
            "account_token": user_token.account_token,
            "dbuuid": dbuuid,
            "data": data,
            "company_name": self.company_id.name,
            "vat": self.company_id.vat,
            "phone": self.company_id.phone,
            "email": self.company_id.email,
            "service": "ple",
            "test_mode": self.company_id.l10n_pe_ple_test,
        }
        result = jsonrpc(iap_server_url + "/iap/get_ple_data", params=params)
        if result.get("report_status_code", False) == 10:
            # delete old report lines
            self.file_ids.unlink()
            # Save the new data
            self.write(
                {
                    "ple_remote_id": result.get("ple_remote_id", False)
                    or self.ple_remote_id,
                    "report_status_code": result.get(
                        "report_status_code", ERROR_INTERNAL
                    ),
                    "file_ids": result.get("file_ids", []),
                }
            )
        else:
            self.write(
                {
                    "report_status_code": result.get(
                        "report_status_code", ERROR_INTERNAL
                    ),
                }
            )
        return result.get("report_status_code", ERROR_INTERNAL)

    def button_open_lines(self):
        """Redirect the user to the line(s) of this report.
        :return:    An action on l10n_pe.ple.report.line.
        """
        self.ensure_one()
        action = {
            "name": _("PLE report details"),
            "type": "ir.actions.act_window",
            "context": {"default_report_id": self.id},
            "view_mode": "list,form",
            "domain": [("id", "in", self.line_ids.ids)],
        }
        if self.state not in ["draft", "in_progress"]:
            action["context"].update(
                {
                    "create": False,
                }
            )
        return action

    def button_open_error_lines(self):
        """Redirect the user to report lines that still have verification errors."""
        self.ensure_one()
        action = self.button_open_lines()
        error_line_ids = self.line_ids.filtered(lambda line: line.line_has_error).ids
        action.update({"domain": [("id", "in", error_line_ids)]})
        return action

    def button_open_files(self):
        """Redirect the user to the File(s) of this report.
        :return:    An action on ple.report.file.
        """
        self.ensure_one()
        action_xmlid = self._get_button_open_files_action_xmlid()
        if action_xmlid:
            action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        else:
            list_view = self.env.ref(
                "l10n_pe_ple_reports.ple_report_file_tree", raise_if_not_found=False
            )
            action = {
                "name": _("PLE report files"),
                "type": "ir.actions.act_window",
                "res_model": self._get_button_open_files_res_model(),
                "view_mode": "list",
                "domain": [("id", "in", self.file_ids.ids)],
            }
            if list_view:
                action.update({
                    "view_id": list_view.id,
                    "views": [(list_view.id, "list")],
                })

        action.update(
            {
                "context": {
                    "create": False,
                    "edit": False,
                    "default_report_id": self.id,
                },
                "domain": [("id", "in", self.file_ids.ids)],
            }
        )
        return action

    def _get_button_open_files_action_xmlid(self):
        return False

    def _get_button_open_files_res_model(self):
        return "ple.report.file"

    def button_draft(self):
        self.write({"state": "draft"})

    def button_cancel(self):
        self.write({"state": "cancel"})

    def action_post(self):
        self.write({"state": "posted"})

    # -------------------------------------------------------------------------
    # IAP METHODS
    # -------------------------------------------------------------------------

    def buy_credits(self):
        url = self.env["iap.account"].get_credits_url(
            base_url="", service_name="l10n_pe_ple"
        )
        return {
            "type": "ir.actions.act_url",
            "url": url,
        }

    def buy_token(self):
        url = "https://www.operu.pe/shop/libros-ple-ilimitados-92"
        return {
            "type": "ir.actions.act_url",
            "url": url,
        }


class PleReportLine(models.AbstractModel):
    _name = "l10n_pe.ple.report.line"
    _description = "PLE Reports lines"

    name = fields.Char(
        string="Description",
        copy=False,
        index=True,
        # states={"posted": [("readonly", True)]},
    )
    company_id = fields.Many2one(
        related="report_id.company_id", store=True, readonly=True
    )
    cuo_number = fields.Char(
        string="CUO Number",
        copy=False,
        index=True,
        help="1. Contribuyentes del Régimen General: Número correlativo del mes o Código Único de la Operación (CUO), que es la llave única"
        "o clave única o clave primaria del software contable que identifica de manera unívoca el asiento contable en el Libro Diario "
        "o del Libro Diario de Formato Simplificado en que se registró la operación."
        "2. Contribuyentes del Régimen Especial de Renta - RER:  Número correlativo del mes",
        # states={"posted": [("readonly", True)]},
    )
    cuo_sequence = fields.Char(
        string="CUO Squence",
        copy=False,
        index=True,
        help="Número correlativo del asiento contable identificado en el campo 2, cuando se utilice el Código Único de la Operación (CUO). "
        "El primer dígito debe ser: 'A' para el asiento de apertura del ejercicio, 'M' para los asientos de movimientos o ajustes del"
        "mes o 'C' para el asiento de cierre del ejercicio.",
        # states={"posted": [("readonly", True)]},
    )
    currency_rate = fields.Float(
        "Currency Rate", digits=(2, 3), # states={"posted": [("readonly", True)]}
    )
    currency_name = fields.Char(
        string="Currency", # states={"posted": [("readonly", True)]}
    )
    date = fields.Date(
        string="Date", index=True, copy=False, # states={"posted": [("readonly", True)]}
    )
    date_to = fields.Date(
        string="Limit date", related="report_id.date_to", readonly=True
    )
    document_type = fields.Char(
        string="Doc. Type", size=2, copy=False, # states={"posted": [("readonly", True)]}
    )
    manual = fields.Boolean(string="Manual Record", default=True)
    move_id = fields.Many2one(
        "account.move",
        string="Account Move",
        domain="[('company_id', '=', company_id),('date', '<=', date_to)]",
        index=True,
        ondelete="set null",
        check_company=True,
        # states={"posted": [("readonly", True)]},
    )
    move_line_id = fields.Many2one(
        "account.move.line",
        string="Account Move Line",
        domain="[('company_id', '=', company_id)]",
        index=True,
        ondelete="set null",
        check_company=True,
        # states={"posted": [("readonly", True)]},
    )
    partner_document_type = fields.Char(
        string="Partner Doc. Type",
        size=3,
        copy=False,
        # states={"posted": [("readonly", True)]},
    )
    partner_document_number = fields.Char(
        string="Partner Doc. Number",
        size=15,
        copy=False,
        # states={"posted": [("readonly", True)]},
    )
    partner_name = fields.Char(
        string="Partner Name",
        size=100,
        copy=False,
        # states={"posted": [("readonly", True)]},
    )
    period = fields.Char(string="Period", # states={"posted": [("readonly", True)]}
                         )
    report_id = fields.Many2one(
        "l10n_pe.ple.report",
        string="PLE report",
        index=True,
        bypass_search_access=True,
        ondelete="cascade",
        check_company=True,
    )
    line_has_error = fields.Boolean(
        string="Has Error",
        index=True,
        help="Set by Verify Lines. Uncheck it to mark the line as corrected.",
    )
    line_error_message = fields.Text(string="Line Error Message")
    line_verified_at = fields.Datetime(string="Line Verified At")
    state = fields.Selection(string="Status", readonly=True, related="report_id.state")

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange("move_id")
    def _onchange_move_id(self):
        if self.move_id:
            self.cuo_number = self.get_cuo_number(self.move_id)
            self.period = self.convert_date_to_period(self.move_id.date)
            self.state_line = self.get_state_line(self.move_id, self.report_id)

    @api.onchange("move_line_id")
    def _onchange_move_line_id(self):
        if self.move_line_id:
            self.cuo_sequence = self.get_cuo_sequence(self.move_line_id)

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _build_line_warning(self, error_message):
        return _("CUO Number: %s - %s, ERROR: %s \n") % (
            self.cuo_number,
            self.cuo_sequence,
            error_message,
        )

    def write(self, vals):
        # Allow manual cleanup from list view: unchecking Has Error clears message.
        if "line_has_error" in vals and not vals.get("line_has_error"):
            vals = dict(vals)
            vals["line_error_message"] = ""
            vals["line_verified_at"] = fields.Datetime.now()
        return super(PleReportLine, self).write(vals)

    def _is_valid_yyyymm(self, value):
        if not value or len(value) != 6 or not value.isdigit():
            return False
        month = int(value[4:6])
        return 1 <= month <= 12

    def _date_to_yyyymm(self, date_value):
        return date_value and date_value.strftime("%Y%m") or ""

    def _is_valid_ruc(self, value):
        return bool(value) and value.isdigit() and len(value) == 11

    def _yyyymm_lte(self, left_yyyymm, right_yyyymm):
        if not self._is_valid_yyyymm(left_yyyymm):
            return False
        if not self._is_valid_yyyymm(right_yyyymm):
            return False
        return int(left_yyyymm) <= int(right_yyyymm)

    def convert_date_to_period(self, date=False):
        period = ""
        if date:
            period = date.strftime("%Y%m00")
        return period

    def get_state_line(self, move_id=False, report_id=False):
        """1. Obligatorio"""
        state = "0"
        return state

    def get_cuo_number(self, move_id=False):
        cuo_number = str(move_id.id).rjust(6, "0")
        return cuo_number

    def get_cuo_sequence(self, move_line_id=False):
        """Número correlativo del asiento contable identificado en el campo 2, cuando se utilice el Código Único de la Operación (CUO).
        El primer dígito debe ser:
        "A" para el asiento de apertura del ejercicio,
        "M" para los asientos de movimientos o ajustes del mes o
        "C" para el asiento de cierre del ejercicio.
        """
        cuo_sequence = ""
        type = "M"
        if move_line_id:
            cuo_sequence = "%s%s" % (type, move_line_id.cuo_sequence)
        return cuo_sequence
    
class PleReportFile(models.AbstractModel):
    _name = "ple.report.file"
    _description = "Report Files"

    name = fields.Char(string="Name", compute="_get_name_report")
    code_id = fields.Many2one("ple.report.code", "Code", required=True, index=True)
    compute_date = fields.Datetime(string="Compute Date", copy=False)
    txt_file = fields.Binary(string="TXT file", readonly=False)
    txt_file_name = fields.Char("TXT file name", default="TXT FIle")
    zip_file = fields.Binary(string="ZIP file", readonly=False)
    zip_file_name = fields.Char("ZIP file name", default="ZIP FIle")
    xlsx_file = fields.Binary(string="XLSX file", readonly=True)
    xlsx_file_name = fields.Char("XLSX file name", compute="_get_xlsx_file_name")
    period = fields.Char(string="Period")
    ple_report_type_id = fields.Many2one(
        "l10n_pe.ple.report.type", "PLE Report Type", required=True, index=True
    )
    report_id = fields.Many2one(
        "l10n_pe.ple.report",
        string="PLE report",
        index=True,
        bypass_search_access=True,
        ondelete="cascade",
    )
    name_custom = fields.Char(string="Name Custom")

    @api.depends("name_custom","code_id.name", "code_id.description")
    def _get_name_report(self):
        for file in self:
            file.name = "%s" % (file.name_custom or file.code_id.description,)

    @api.depends("code_id.name", "name", "period")
    def _get_xlsx_file_name(self):
        for file in self:
            file.xlsx_file_name = "%s %s %s.xlsx" % (
                file.code_id.name,
                file.name,
                file.period,
            )
