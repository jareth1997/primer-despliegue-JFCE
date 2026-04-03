###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################


from odoo import fields, models
from odoo.tools import _
from odoo.exceptions import UserError


class PleReportCategory(models.Model):
    _name = "l10n_pe.ple.report.category"
    _description = "PLE Report Category"
    _order = "sequence, name"

    name = fields.Char(string="Name", required=True, translate=True)
    code = fields.Char(string="Code", required=True, size=8)
    sequence = fields.Integer(string="Sequence", default=10)
    color = fields.Integer(string="Color Index", default=0)
    description = fields.Char(string="Description", translate=True)
    report_type_ids = fields.One2many(
        "l10n_pe.ple.report.type",
        "category_id",
        string="Report Types",
    )


class PleReportType(models.Model):
    _name = "l10n_pe.ple.report.type"
    _description = "PLE Report Type"
    _order = "sequence"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Description", size=128, index=True, required=True, default="New"
    )
    color = fields.Integer("Color Index", default=0)
    category_id = fields.Many2one(
        "l10n_pe.ple.report.category",
        string="Category",
        index=True,
        tracking=True,
    )
    system_type = fields.Selection(
        selection=[
            ("ple", "PLE"),
            ("sire", "SIRE"),
            ("manual", "Manual / Computarizado"),
        ],
        string="System Type",
        default="ple",
        required=True,
        tracking=True,
        help="Indicates how this book is submitted: electronically via PLE, via SIRE, or kept manually/computerized without electronic submission to SUNAT.",
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    opportunity_eeff_code = fields.Selection(
        selection=[
            ("00", "00- Mensual"),
            ("01", "01- Al 31 de diciembre"),
            ("02", "02- Al 31 de enero, por modificacion del porcentaje"),
            ("03", "03- Al 30 de junio, por modificacion del coeficiente o porcentaje"),
            (
                "04",
                "04- Al ultimo dia del mes que sustentara la suspension o modificacion del coeficiente (distinto al 31 de enero o 30 de junio)",
            ),
            (
                "05",
                "05- Al día anterior a la entrada en vigencia de la fusión, escisión y demás formas de reorganización de sociedades o empresas o extinción de la persona jurídica",
            ),
            (
                "06",
                "06- A la fecha del balance de liquidación, cierre o cese definitivo del deudor tributario",
            ),
            ("07", "07- A la fecha de presentación para libre propósito"),
        ],
        string="Code Opportunity EEFF",
        required=True,
        copy=False,
        default="00",
        tracking=True,
    )
    sequence = fields.Integer(
        help="Used to order Journals in the dashboard view", default=10
    )
    show_on_dashboard = fields.Boolean(
        string="Show Report type on dashboard",
        help="Whether this Report type should be displayed on the dashboard or not",
        default=True,
    )
    code_ids = fields.Many2many(
        "ple.report.code",
        "ple_report_type_code_rel",
        "ple_id",
        "code_id",
        string="Codes",
        help="Used to categorize and filter displayed Reports",
        tracking=True,
    )
    allowed_document_type_ids = fields.Many2many(
        "l10n_latam.document.type",
        "ple_report_type_document_type_rel",
        "ple_report_type_id",
        "document_type_id",
        string="Allowed Document Types",
        help="If empty, all document types are allowed for this report type.",
        tracking=True,
    )

    # -------------------------------------------------------------------------
    # DASHBOARD METHODS
    # -------------------------------------------------------------------------

    # Capture de action for the report
    def _get_action_report(self):
        action = False
        return action

    def action_view_reports(self):
        action = self._get_action_report()
        if not action:
            raise UserError(
                _(
                    "There is not a valid View for listing the Reports. Please contact with the Adiministrator or Update the module that contains this Report."
                )
            )
        action["context"] = {
            "default_ple_report_type_id": self.id,
        }
        action["domain"] = [("ple_report_type_id", "=", self.id)]
        return action


class PleReportCode(models.Model):
    _name = "ple.report.code"
    _description = "PLE report Codes"
    _order = "sequence asc"

    name = fields.Char("Name", required=True, translate=True)
    code = fields.Char(
        string="Short Code",
        required=True,
        help="The PLE reports entries of this PLE type will also be named using this prefix by default.",
    )
    description = fields.Char("Description")
    sequence = fields.Integer("Sequence", default=10, index=True, required=True)
    ple_type_ids = fields.Many2many(
        "l10n_pe.ple.report.type",
        "ple_report_type_code_rel",
        "code_id",
        "ple_id",
        string="PLE report types",
    )
    color = fields.Integer(
        string="Color Index", help="Color to apply to this tag (including in website)."
    )
