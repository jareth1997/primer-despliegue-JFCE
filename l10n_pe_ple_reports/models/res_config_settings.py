###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_pe_ple_token = fields.Char(
        "PLE token", related="company_id.l10n_pe_ple_token", readonly=False
    )
    l10n_pe_ple_token_expiration = fields.Date(
        "Expiration date", related="company_id.l10n_pe_ple_token_expiration"
    )
    l10n_pe_ple_token_status_code = fields.Integer(
        "Status code", related="company_id.l10n_pe_ple_token_status_code"
    )
    l10n_pe_ple_token_status_message = fields.Char(
        "Status message", related="company_id.l10n_pe_ple_token_status_message"
    )
    l10n_pe_ple_test = fields.Boolean(
        "Test mode", related="company_id.l10n_pe_ple_test", readonly=False
    )

    def l10n_pe_ple_check_expiration(self):
        for conf in self:
            if conf.company_id.l10n_pe_ple_token:
                conf.company_id.l10n_pe_ple_check_expiration()
        return True

    @api.onchange("l10n_pe_ple_token")
    def _onchange_l10n_pe_ple_token(self):
        if self.l10n_pe_ple_token:
            self.l10n_pe_ple_test = False
            self.company_id.l10n_pe_ple_check_expiration()
