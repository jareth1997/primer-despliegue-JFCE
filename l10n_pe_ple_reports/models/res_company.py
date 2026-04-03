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

from odoo import api, fields, models
from odoo.tools.translate import _, LazyTranslate
_lt = LazyTranslate(__name__, default_lang='en_US')

from odoo.addons.iap import jsonrpc

DEFAULT_IAP_ENDPOINT = "https://iap.odoofact.pe"

_logger = logging.getLogger(__name__)

# List codes for IAP token status
SUCCESS = 10
ERROR_TOKEN_RENEWED = 11
ERROR_INTERNAL = 1
ERROR_NOT_ACTIVE = 2
ERROR_EXPIRED = 3
ERROR_INVALID_SERVICE_TOKEN = 4
ERROR_TOKEN_ALREADY_USED = 5
ERROR_NO_TOKEN_FOR_SERVICE = 6

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
}


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_pe_ple_token = fields.Char("PLE token")
    l10n_pe_ple_token_expiration = fields.Date("Expiration date")
    l10n_pe_ple_token_status_code = fields.Integer("Status code")
    l10n_pe_ple_token_status_message = fields.Char(
        "Status message", compute="_compute_token_error_message"
    )
    l10n_pe_ple_test = fields.Boolean("Test mode", default=True)

    @api.depends("l10n_pe_ple_token_status_code")
    def _compute_token_error_message(self):
        for record in self:
            print(
                "record.l10n_pe_ple_token_status_code: ",
                record.l10n_pe_ple_token_status_code,
            )
            if record.l10n_pe_ple_token_status_code:
                if SUCCESS == record.l10n_pe_ple_token_status_code:
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[SUCCESS]
                elif ERROR_NOT_ACTIVE == record.l10n_pe_ple_token_status_code:
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[
                        ERROR_NOT_ACTIVE
                    ]
                elif ERROR_EXPIRED == record.l10n_pe_ple_token_status_code:
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[
                        ERROR_EXPIRED
                    ]
                elif (
                    ERROR_INVALID_SERVICE_TOKEN == record.l10n_pe_ple_token_status_code
                ):
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[
                        ERROR_INVALID_SERVICE_TOKEN
                    ]
                elif ERROR_TOKEN_ALREADY_USED == record.l10n_pe_ple_token_status_code:
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[
                        ERROR_TOKEN_ALREADY_USED
                    ]
                elif ERROR_NO_TOKEN_FOR_SERVICE == record.l10n_pe_ple_token_status_code:
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[
                        ERROR_NO_TOKEN_FOR_SERVICE
                    ]
                else:
                    record.l10n_pe_ple_token_status_message = ERROR_MESSAGES[
                        ERROR_INTERNAL
                    ]
            else:
                record.l10n_pe_ple_token_status_message = ""

    @api.model
    def run_check_expiration(self):
        """This method is called from a cron job to calculate the token expiration date."""
        records = (
            self.env["res.company"]
            .search([])
            .filtered(lambda x: x.country_id and x.country_id.code == "PE")
        )
        print("l10n_pe_ple_check_expiration GO: ", records)
        if records:
            for record in records:
                print("l10n_pe_ple_check_expiration GO:")
                record.l10n_pe_ple_check_expiration()

    @api.onchange("l10n_pe_ple_token")
    def _onchange_l10n_pe_ple_token(self):
        if self.l10n_pe_ple_token:
            self.l10n_pe_ple_test = False

    def l10n_pe_ple_check_expiration(self):
        for company in self:
            if company.l10n_pe_ple_token:
                ir_params = self.env["ir.config_parameter"].sudo()
                default_endpoint = (
                    self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("odoofact_iap_endpoint", DEFAULT_IAP_ENDPOINT)
                )
                iap_server_url = ir_params.get_param(
                    "l10n_pe_edi_endpoint", default_endpoint
                )
                dbuuid = (
                    self.env["ir.config_parameter"].sudo().get_param("database.uuid")
                )
                params = {
                    "client_service_token": company.l10n_pe_ple_token,
                    "company_name": company.name,
                    "vat": company.vat,
                    "dbuuid": dbuuid,
                    "service": "ple",
                }
                result = jsonrpc(
                    iap_server_url + "/iap/get_token_status", params=params
                )
                print("Result data: ", result)
                if result.get("status_code", False):
                    # Save the new data
                    company.write(
                        {
                            "l10n_pe_ple_token_expiration": result.get(
                                "token_expiration_date", ""
                            ),
                            "l10n_pe_ple_token_status_code": result.get(
                                "status_code", ERROR_INTERNAL
                            ),
                        }
                    )
                else:
                    company.write(
                        {
                            "l10n_pe_ple_token_expiration": "",
                            "l10n_pe_ple_token_status_code": result.get(
                                "status_code", ERROR_INTERNAL
                            ),
                        }
                    )
        return True
