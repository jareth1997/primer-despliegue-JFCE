###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

from odoo.http import Controller, request, route


class BannerController(Controller):
    @route("/ple_credit_status", type="jsonrpc", auth="user")
    def credit_status(self):
        credit = request.env["iap.account"].get_credits("l10n_pe_ple")
        credit_url = request.env["iap.account"].get_credits_url("l10n_pe_ple")
        return {
            "html": request.env["ir.ui.view"]._render_template(
                "l10n_pe_ple_reports.ple_credit_status",
                {"credit": credit, "credit_url": credit_url},
            )
        }
