"""
Migration 19.0.1.0.2
- Add l10n_pe.ple.report.category model (new table, handled by Odoo ORM)
- Add category_id and system_type columns to l10n_pe.ple.report.type
- Assign category and system_type to all pre-existing report types by sequence

Sequences handled:
  51  → CONT / ple   (Libro Diario)
  53  → CONT / ple   (Libro Diario Detalle Plan Contable)
  61  → CONT / ple   (Libro Mayor)
  81  → COMP / ple   (PLE Registro de Compras)
  82  → COMP / ple   (PLE Registro de Compras No Domiciliados)
  84  → COMP / sire  (SIRE RCE)
  85  → COMP / sire  (SIRE RCE No Domiciliados)
  141 → VENT / ple   (PLE Registro de Ventas e Ingresos)
  144 → VENT / sire  (SIRE RVIE)
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

_SEQUENCE_MAP = {
    51:  ("l10n_pe_ple_reports.ple_category_contables", "ple"),
    53:  ("l10n_pe_ple_reports.ple_category_contables", "ple"),
    61:  ("l10n_pe_ple_reports.ple_category_contables", "ple"),
    81:  ("l10n_pe_ple_reports.ple_category_compras",   "ple"),
    82:  ("l10n_pe_ple_reports.ple_category_compras",   "ple"),
    84:  ("l10n_pe_ple_reports.ple_category_compras",   "sire"),
    85:  ("l10n_pe_ple_reports.ple_category_compras",   "sire"),
    141: ("l10n_pe_ple_reports.ple_category_ventas",    "ple"),
    144: ("l10n_pe_ple_reports.ple_category_ventas",    "sire"),
}


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    updated_total = 0

    for sequence, (cat_xmlid, sys_type) in _SEQUENCE_MAP.items():
        try:
            category = env.ref(cat_xmlid)
        except Exception:
            _logger.warning(
                "Migration 19.0.1.0.2: category '%s' not found, skipping sequence %s.",
                cat_xmlid, sequence,
            )
            continue
        records = env["l10n_pe.ple.report.type"].search([("sequence", "=", sequence)])
        records.write({"category_id": category.id, "system_type": sys_type})
        updated_total += len(records)
        _logger.info(
            "Migration 19.0.1.0.2: seq=%s → %s / %s (%d record(s)).",
            sequence, cat_xmlid, sys_type, len(records),
        )

    # Fallback: any remaining record without system_type gets 'ple'
    fallback = env["l10n_pe.ple.report.type"].search([("system_type", "=", False)])
    if fallback:
        fallback.write({"system_type": "ple"})
        _logger.info(
            "Migration 19.0.1.0.2: fallback system_type='ple' set for %d record(s).",
            len(fallback),
        )

    _logger.info(
        "Migration 19.0.1.0.2: finished — %d report type(s) updated.", updated_total
    )
