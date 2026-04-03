###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

{
    "name": "Libros electronicos Peru - Base",
    "version": "19.0.1.0.3",
    "author": "OPeru",
    "category": "Accounting",
    "summary": "Peruvian electronic reports PLE - Base",
    "description": """
    Peruvian Localization
    Peruvian electronic reports PLE Base
    """,
    "depends": [
        "base",
        "account",
        "iap",
        "l10n_pe_edi_catalog",
    ],
    "data": [
        "security/ir.model.access.csv",
        'data/iap_service_ple_reports.xml',
        "data/config_parameter_endpoint.xml",
        "data/ir_cron_data.xml",
        "data/ple_report_category_data.xml",
        "views/account_move_views.xml",
        "views/res_country_views.xml",
        "views/res_company_views.xml",
        # "views/res_config_settings_views.xml",
        "views/ple_report_views.xml",
        "views/ple_report_dashboard_view.xml",
        "views/ple_template.xml",
        "views/ple_menuitem.xml",
    ],
    'assets': {
        'web.assets_backend': ['l10n_pe_ple_reports/static/src/scss/ple_empty_screen.scss']
    },
    "assets": {
        "web.assets_backend": [
            "l10n_pe_ple_reports/static/src/scss/ple_empty_screen.scss"
        ]
    },
    "application": True,
    "installable": True,
    "images": ["static/description/banner.png"],
    "license": "OPL-1",
    "sequence": 10,
    "post_init_hook": "post_init_hook",
}
