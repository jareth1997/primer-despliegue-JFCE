###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

import re

from odoo import fields, models
from odoo.tools.float_utils import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    # ==== Detraction fields ====
    l10n_pe_edi_detraction_payment_date = fields.Date(
        string="Detraction payment Date", help="Date of the Detraction payment"
    )
    l10n_pe_edi_detraction_payment_number = fields.Char(
        string="Detraction payment Number", help="Number of the Detraction payment"
    )

    # -------------------------------------------------------------------------
    # PLE METHODS
    # -------------------------------------------------------------------------

    def _get_country_code(self):
        self.ensure_one()
        country_code = (
            self.partner_id.country_id
            and (
                self.partner_id.country_id.l10n_pe_reports_country_residence_id
                and self.partner_id.country_id.l10n_pe_reports_country_residence_id.code
                or ""
            )
            or ""
        )
        return country_code

    def _get_currency_rate(self):
        self.ensure_one()
        currency_rate = 1
        origin_document = self.debit_origin_id or self.reversed_entry_id
        if self.invoice_currency_rate != 0.0 and not origin_document:
            currency_rate = 1 / self.invoice_currency_rate
        if origin_document:
            currency_rate = origin_document.invoice_currency_rate != 0.0 and 1 / origin_document.invoice_currency_rate or 1.0
        return currency_rate

    def compute_cuo_sequence(self):
        """Assign CUO Sequence"""
        for move in self:
            sequence = 1
            for line in move.line_ids:
                line.cuo_sequence = sequence
                sequence += 1

    def _get_sign(self):
        if self.move_type == "entry" or self.is_outbound():
            sign = 1
        if self.move_type in ["in_refund", "out_refund"]:
            sign = -1
        else:
            sign = 1
        return sign

    def _get_partner_document_type(self):
        partner_document_type = False
        if self.state != "cancel":
            partner_document_type = (
                self.partner_id.commercial_partner_id.l10n_latam_identification_type_id
                and self.partner_id.commercial_partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
                or ""
            )
        return partner_document_type

    def _get_partner_document_number(self):
        partner_document_number = False
        if self.state != "cancel":
            partner_document_number = (
                self.partner_id.commercial_partner_id.vat
                and self.partner_id.commercial_partner_id.vat
                or ""
            )
        return partner_document_number

    def _get_partner_name(self):
        partner_name = (
            self.partner_id.commercial_partner_id.name
            or self.partner_id.commercial_partner_id.name
        )
        if self.state == "cancel" and self.move_type in [
            "out_invoice",
            "out_refund",
            "out_receipt",
        ]:
            partner_name = False
        return partner_name

    def _get_company_document_type(self):
        company_document_type = False
        if self.state != "cancel":
            company_document_type = (
                self.company_id.partner_id.commercial_partner_id.l10n_latam_identification_type_id
                and self.company_id.partner_id.commercial_partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
                or ""
            )
        return company_document_type

    def _get_company_document_number(self):
        company_document_number = False
        if self.state != "cancel":
            company_document_number = self.company_id.vat and self.company_id.vat or ""
        return company_document_number

    def _get_amount_total_signed(self):
        """Get the Amount Total"""
        sign = self._get_sign()
        amount_total_signed = self.amount_total_signed
        if self.state == "cancel" and self.move_type in [
            "out_invoice",
            "out_refund",
            "out_receipt",
        ]:
            amount_total_signed = 0.00
        return abs(amount_total_signed) * sign

    def _get_amount_exportation(self):
        """Get the Amount exportation"""
        sign = self._get_sign()
        amount_exportation = sum(
            [
                x.debit - x.credit
                for x in self.line_ids
                if any(tax.l10n_pe_edi_tax_code in ["9995"] for tax in x.tax_ids)
            ]
        )
        if self.state == "cancel" and self.move_type in [
            "out_invoice",
            "out_refund",
            "out_receipt",
        ]:
            amount_exportation = 0.0
        return abs(amount_exportation) * sign

    def _get_amount_base(self):
        """Get the Amount Affected by IGV"""
        sign = self._get_sign()
        total_untaxed = 0.00
        # Affected by IGV
        for line in self.line_ids:
            if any(tax.l10n_pe_edi_tax_code in ["1000"] for tax in line.tax_ids):
                # Untaxed amount.
                total_untaxed += line.balance
        if self.state == "cancel" and self.move_type in [
            "out_invoice",
            "out_refund",
            "out_receipt",
        ]:
            total_untaxed = 0.00
        return abs(total_untaxed) * sign

    def _get_amount_discount(self):
        """Get the Amount Affected by IGV"""
        amount_discount = 0.00
        if self.state != "cancel":
            # Discount by amount Affected by IGV
            for line in self.line_ids:
                if any(tax.l10n_pe_edi_tax_code in ["1000"] for tax in line.tax_ids):
                    # If the amount is negative, is considerated as global discount
                    amount_discount += line.price_subtotal < 0 and line.balance or 0.00
                    # If the product is not free, it calculates the amount discount
                    amount_discount += line._get_amount_discount()
            return amount_discount

    def _get_amount_tax(self):
        """Get the Amount Tax by Group: IGV, ISC, EXO, INA, ICBPER and OTROS"""
        self.ensure_one()
        sign = self._get_sign()
        amount_free = sum(
            line.l10n_pe_edi_amount_free for line in self.line_ids.filtered(lambda x: x.display_type == "product")
        )
        amount_exonerated = sum(
            line.price_subtotal for line in self.line_ids.filtered(lambda x: x.display_type == "product")
        )
        amount_unaffected = sum(
            line.price_subtotal for line in self.line_ids.filtered(lambda x: x.display_type == "product")
        )
        amount_igv = sum(
            line.amount_currency for line in self.line_ids.filtered(lambda x: x.display_type == "tax") if line.tax_group_id.name == "IGV"
        )
        amount_isc = sum(
            line.amount_currency for line in self.line_ids.filtered(lambda x: x.display_type == "tax") if line.tax_group_id.name == "ISC"
        )
        amount_icbper = sum(
            line.amount_currency for line in self.line_ids.filtered(lambda x: x.display_type == "tax") if line.tax_group_id.name == "ICBPER"
        )
        if self.state == "cancel" and self.move_type in [
            "out_invoice",
            "out_refund",
            "out_receipt",
        ]:
            amount_free = 0.0
            amount_exonerated = 0.0
            amount_unaffected = 0.0
            amount_igv = 0.0
            amount_isc = 0.0
            amount_icbper = 0.0
        values = {
            "amount_free" : amount_free,
            "amount_exonerated" : amount_exonerated,
            "amount_unaffected" : amount_unaffected,
            "amount_igv" : sign * amount_igv,
            "amount_icbper" : sign * amount_icbper,
        }
        return values

    def _check_correlative_sintax(self, name):
        regex = r"^[A-Z][A-Z0-9]{3}[\-][0-9]{1,8}$"
        return re.match(regex, name)

    def _get_serie_number(self, name):
        is_valid = self._check_correlative_sintax(name)
        serie = ""
        number = ""
        if is_valid:
            name_split = name.split("-")
            serie = name_split[0]
            number = int(name_split[1])
        return serie, number

    def _get_reversed_entry(self):
        reversal_type = ""
        reversal_serie = ""
        reversal_number = ""
        reversal_date = ""
        if self.debit_origin_id:
            if self.debit_origin_id.move_type in [
                "in_invoice",
                "in_refund",
                "in_entry",
            ]:
                reversal_serie, reversal_number = self._get_serie_number(
                    self.debit_origin_id.ref
                )
            else:
                reversal_serie, reversal_number = self._get_serie_number(
                    self.debit_origin_id.name
                )
            reversal_type = (
                self.debit_origin_id.l10n_latam_document_type_id
                and self.debit_origin_id.l10n_latam_document_type_id.code
                or ""
            )
            reversal_date = self.debit_origin_id.invoice_date
        if self.reversed_entry_id:
            if self.reversed_entry_id.move_type in [
                "in_invoice",
                "in_refund",
                "in_entry",
            ]:
                reversal_serie, reversal_number = self._get_serie_number(
                    self.reversed_entry_id.ref
                )
            else:
                reversal_serie, reversal_number = self._get_serie_number(
                    self.reversed_entry_id.name
                )
            reversal_type = (
                self.reversed_entry_id.l10n_latam_document_type_id
                and self.reversed_entry_id.l10n_latam_document_type_id.code
                or ""
            )
            reversal_date = self.reversed_entry_id.invoice_date
        # Fallback: si no hay documento vinculado, usa los campos manuales de odoofact.
        # Mapea el tipo Nubefact ("1"/"2") al código SUNAT ("01"/"03") para el PLE.
        if not reversal_type and not reversal_serie and not reversal_number:
            origin_doc_type = getattr(self, "l10n_pe_edi_origin_doc_type", False)
            reversal_type = {"1": "01", "2": "03"}.get(origin_doc_type, origin_doc_type or "")
            reversal_serie = getattr(self, "l10n_pe_edi_origin_doc_serie", "") or ""
            reversal_number = getattr(self, "l10n_pe_edi_origin_doc_number", "") or ""
            reversal_date = getattr(self, "l10n_pe_edi_origin_doc_date", "") or ""
        return reversal_type, reversal_serie, reversal_number, reversal_date

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def action_post(self):
        res = super(AccountMove, self).action_post()
        self.compute_cuo_sequence()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cuo_sequence = fields.Integer(string="CUO sequence")

    def _get_amount_base(self):
        """Return the amount base from X (100 - Y)/100 = Z
        X: Base amount, Y: Discount, Z: Balance
        FORMULA:  X = Z*100/(100-Y)"""
        self.ensure_one()
        amount_base = self.balance * 100 / (100 - self.discount)
        return amount_base

    def _get_amount_discount(self):
        """Return the amount discount from X - X*Y/100 = Z
        X: Base amount, Y: Discount, Z: Balance
        FORMULA: X*Y/100 = X-Z"""
        self.ensure_one()
        amount_discount = self._get_amount_base() - self.balance
        return amount_discount
