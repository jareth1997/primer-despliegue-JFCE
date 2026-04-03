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

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# Mapping: ISO alpha-2 country code → SUNAT Tabla 35 code
# Entries without a valid/current ISO code (e.g. URSS, YUGOSLAVIA, dissolved
# territories) are intentionally omitted.
_ISO_TO_TABLE35 = {
    "AF": "9013",  # AFGANISTAN
    "AL": "9017",  # ALBANIA
    "DE": "9023",  # ALEMANIA
    "AM": "9026",  # ARMENIA
    "AW": "9027",  # ARUBA
    "BA": "9029",  # BOSNIA-HERZEGOVINA
    "BF": "9031",  # BURKINA FASO
    "AD": "9037",  # ANDORRA
    "AO": "9040",  # ANGOLA
    "AI": "9041",  # ANGUILLA
    "AG": "9043",  # ANTIGUA Y BARBUDA
    "SA": "9053",  # ARABIA SAUDITA
    "DZ": "9059",  # ARGELIA
    "AR": "9063",  # ARGENTINA
    "AU": "9069",  # AUSTRALIA
    "AT": "9072",  # AUSTRIA
    "AZ": "9074",  # AZERBAIJAN
    "BS": "9077",  # BAHAMAS
    "BH": "9080",  # BAHREIN
    "BD": "9081",  # BANGLADESH
    "BB": "9083",  # BARBADOS
    "BE": "9087",  # BELGICA
    "BZ": "9088",  # BELICE
    "BM": "9090",  # BERMUDAS
    "BY": "9091",  # BELARUS
    "MM": "9093",  # MYANMAR
    "BO": "9097",  # BOLIVIA
    "BW": "9101",  # BOTSWANA
    "BR": "9105",  # BRASIL
    "BN": "9108",  # BRUNEI DARUSSALAM
    "BG": "9111",  # BULGARIA
    "BI": "9115",  # BURUNDI
    "BT": "9119",  # BUTAN
    "CV": "9127",  # CABO VERDE
    "KY": "9137",  # CAIMAN, ISLAS
    "KH": "9141",  # CAMBOYA
    "CM": "9145",  # CAMERUN
    "CA": "9149",  # CANADA
    "VA": "9159",  # SANTA SEDE
    "CC": "9165",  # COCOS (KEELING), ISLAS
    "CO": "9169",  # COLOMBIA
    "KM": "9173",  # COMORAS
    "CG": "9177",  # CONGO
    "CK": "9183",  # COOK, ISLAS
    "KP": "9187",  # COREA (NORTE)
    "KR": "9190",  # COREA (SUR)
    "CI": "9193",  # COSTA DE MARFIL
    "CR": "9196",  # COSTA RICA
    "HR": "9198",  # CROACIA
    "CU": "9199",  # CUBA
    "TD": "9203",  # CHAD
    "CL": "9211",  # CHILE
    "CN": "9215",  # CHINA
    "TW": "9218",  # TAIWAN (FORMOSA)
    "CY": "9221",  # CHIPRE
    "BJ": "9229",  # BENIN
    "DK": "9232",  # DINAMARCA
    "DM": "9235",  # DOMINICA
    "EC": "9239",  # ECUADOR
    "EG": "9240",  # EGIPTO
    "SV": "9242",  # EL SALVADOR
    "ER": "9243",  # ERITREA
    "AE": "9244",  # EMIRATOS ARABES UNIDOS
    "ES": "9245",  # ESPAÑA
    "SK": "9246",  # ESLOVAQUIA
    "SI": "9247",  # ESLOVENIA
    "US": "9249",  # ESTADOS UNIDOS
    "EE": "9251",  # ESTONIA
    "ET": "9253",  # ETIOPIA
    "FO": "9259",  # FEROE, ISLAS
    "PH": "9267",  # FILIPINAS
    "FI": "9271",  # FINLANDIA
    "FR": "9275",  # FRANCIA
    "BV": "9001",  # BOUVET ISLAND
    "FK": "9003",  # FALKLAND ISLANDS (MALVINAS)
    "TF": "9005",  # FRENCH SOUTHERN TERRITORIES
    "HM": "9006",  # HEARD AND MC DONALD ISLANDS
    "YT": "9007",  # MAYOTTE
    "GS": "9008",  # SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS
    "SJ": "9009",  # SVALBARD AND JAN MAYEN ISLANDS
    "UM": "9010",  # UNITED STATES MINOR OUTLYING ISLANDS
    "GA": "9281",  # GABON
    "GM": "9285",  # GAMBIA
    "GE": "9287",  # GEORGIA
    "GH": "9289",  # GHANA
    "GI": "9293",  # GIBRALTAR
    "GD": "9297",  # GRANADA
    "GR": "9301",  # GRECIA
    "GL": "9305",  # GROENLANDIA
    "GP": "9309",  # GUADALUPE
    "GU": "9313",  # GUAM
    "GT": "9317",  # GUATEMALA
    "GF": "9325",  # GUAYANA FRANCESA
    "GG": "9327",  # GUERNSEY
    "GN": "9329",  # GUINEA
    "GQ": "9331",  # GUINEA ECUATORIAL
    "GW": "9334",  # GUINEA-BISSAU
    "GY": "9337",  # GUYANA
    "HT": "9341",  # HAITI
    "HN": "9345",  # HONDURAS
    "HK": "9351",  # HONG KONG
    "HU": "9355",  # HUNGRIA
    "IN": "9361",  # INDIA
    "ID": "9365",  # INDONESIA
    "IQ": "9369",  # IRAK
    "IR": "9372",  # IRAN
    "IE": "9375",  # IRLANDA
    "IM": "9378",  # ISLA DEL MAN
    "IS": "9379",  # ISLANDIA
    "CX": "9381",  # ISLAS DE CHRISTMAS
    "IL": "9383",  # ISRAEL
    "IT": "9386",  # ITALIA
    "JM": "9391",  # JAMAICA
    "JP": "9399",  # JAPON
    "JE": "9401",  # JERSEY
    "JO": "9403",  # JORDANIA
    "KZ": "9406",  # KAZAJSTAN
    "KE": "9410",  # KENIA
    "KI": "9411",  # KIRIBATI
    "KG": "9412",  # KIRGUIZISTAN
    "KW": "9413",  # KUWAIT
    "LA": "9420",  # LAOS
    "LS": "9426",  # LESOTHO
    "LV": "9429",  # LETONIA
    "LB": "9431",  # LIBANO
    "LR": "9434",  # LIBERIA
    "LY": "9438",  # LIBIA
    "LI": "9440",  # LIECHTENSTEIN
    "LT": "9443",  # LITUANIA
    "LU": "9445",  # LUXEMBURGO
    "MO": "9447",  # MACAO
    "MK": "9448",  # MACEDONIA (NORTE)
    "MG": "9450",  # MADAGASCAR
    "MY": "9455",  # MALAYSIA
    "MW": "9458",  # MALAWI
    "MV": "9461",  # MALDIVAS
    "ML": "9464",  # MALI
    "MT": "9467",  # MALTA
    "MP": "9469",  # MARIANAS DEL NORTE, ISLAS
    "MH": "9472",  # MARSHALL, ISLAS
    "MA": "9474",  # MARRUECOS
    "MQ": "9477",  # MARTINICA
    "MU": "9485",  # MAURICIO
    "MR": "9488",  # MAURITANIA
    "MX": "9493",  # MEXICO
    "FM": "9494",  # MICRONESIA
    "MD": "9496",  # MOLDAVIA
    "MN": "9497",  # MONGOLIA
    "MC": "9498",  # MONACO
    "MS": "9501",  # MONTSERRAT
    "MZ": "9505",  # MOZAMBIQUE
    "NA": "9507",  # NAMIBIA
    "NR": "9508",  # NAURU
    "NP": "9517",  # NEPAL
    "NI": "9521",  # NICARAGUA
    "NE": "9525",  # NIGER
    "NG": "9528",  # NIGERIA
    "NU": "9531",  # NIUE, ISLA
    "NF": "9535",  # NORFOLK, ISLA
    "NO": "9538",  # NORUEGA
    "NC": "9542",  # NUEVA CALEDONIA
    "PG": "9545",  # PAPUASIA NUEVA GUINEA
    "NZ": "9548",  # NUEVA ZELANDA
    "VU": "9551",  # VANUATU
    "OM": "9556",  # OMAN
    "NL": "9573",  # PAISES BAJOS
    "PK": "9576",  # PAKISTAN
    "PW": "9578",  # PALAU, ISLAS
    "PS": "9579",  # TERRITORIO AUTONOMO DE PALESTINA
    "PA": "9580",  # PANAMA
    "PY": "9586",  # PARAGUAY
    "PE": "9589",  # PERU
    "PN": "9593",  # PITCAIRN, ISLA
    "PF": "9599",  # POLINESIA FRANCESA
    "PL": "9603",  # POLONIA
    "PT": "9607",  # PORTUGAL
    "PR": "9611",  # PUERTO RICO
    "QA": "9618",  # QATAR
    "GB": "9628",  # REINO UNIDO
    "CF": "9640",  # REPUBLICA CENTROAFRICANA
    "CZ": "9644",  # REPUBLICA CHECA
    "SZ": "9645",  # SWAZILANDIA (ESWATINI)
    "DO": "9647",  # REPUBLICA DOMINICANA
    "RE": "9660",  # REUNION
    "ZW": "9665",  # ZIMBABWE
    "RO": "9670",  # RUMANIA
    "RW": "9675",  # RUANDA
    "RU": "9676",  # RUSIA
    "SB": "9677",  # SALOMON, ISLAS
    "EH": "9685",  # SAHARA OCCIDENTAL
    "WS": "9687",  # SAMOA OCCIDENTAL
    "AS": "9690",  # SAMOA NORTEAMERICANA
    "KN": "9695",  # SAN CRISTOBAL Y NIEVES
    "SM": "9697",  # SAN MARINO
    "PM": "9700",  # SAN PEDRO Y MIQUELON
    "VC": "9705",  # SAN VICENTE Y LAS GRANADINAS
    "SH": "9710",  # SANTA ELENA
    "LC": "9715",  # SANTA LUCIA
    "ST": "9720",  # SANTO TOME Y PRINCIPE
    "SN": "9728",  # SENEGAL
    "SC": "9731",  # SEYCHELLES
    "SL": "9735",  # SIERRA LEONA
    "SG": "9741",  # SINGAPUR
    "SY": "9744",  # SIRIA
    "SO": "9748",  # SOMALIA
    "LK": "9750",  # SRI LANKA
    "ZA": "9756",  # SUDAFRICA
    "SD": "9759",  # SUDAN
    "SE": "9764",  # SUECIA
    "CH": "9767",  # SUIZA
    "SR": "9770",  # SURINAM
    "TJ": "9774",  # TADJIKISTAN
    "TH": "9776",  # TAILANDIA
    "TZ": "9780",  # TANZANIA
    "DJ": "9783",  # DJIBOUTI
    "IO": "9787",  # TERRITORIO BRITANICO DEL OCEANO INDICO
    "TL": "9788",  # TIMOR DEL ESTE
    "TG": "9800",  # TOGO
    "TK": "9805",  # TOKELAU
    "TO": "9810",  # TONGA
    "TT": "9815",  # TRINIDAD Y TOBAGO
    "TN": "9820",  # TUNICIA
    "TC": "9823",  # TURCAS Y CAICOS, ISLAS
    "TM": "9825",  # TURKMENISTAN
    "TR": "9827",  # TURQUIA
    "TV": "9828",  # TUVALU
    "UA": "9830",  # UCRANIA
    "UG": "9833",  # UGANDA
    "UY": "9845",  # URUGUAY
    "UZ": "9847",  # UZBEKISTAN
    "VE": "9850",  # VENEZUELA
    "VN": "9855",  # VIET NAM
    "VG": "9863",  # VIRGENES, ISLAS (BRITANICAS)
    "VI": "9866",  # VIRGENES, ISLAS (NORTEAMERICANAS)
    "FJ": "9870",  # FIJI
    "WF": "9875",  # WALLIS Y FORTUNA, ISLAS
    "YE": "9880",  # YEMEN
    "CD": "9888",  # ZAIRE → República Democrática del Congo
    "ZM": "9890",  # ZAMBIA
}


def _compute_cuo_sequence(env):
    """This hook is assign the CUO number to the journal items from peruvian companies."""
    # Filter Peruvian companies (country_id is not stored, must filter in Python)
    all_companies = env["res.company"].search([])
    company_ids = all_companies.filtered(lambda c: c.country_id.code == "PE")
    
    if not company_ids:
        return
    
    # Use SQL for massive performance improvement
    # This assigns CUO sequence using a window function, much faster than ORM
    env.cr.execute("""
        WITH numbered_lines AS (
            SELECT 
                aml.id,
                ROW_NUMBER() OVER (PARTITION BY aml.move_id ORDER BY aml.id) as seq
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            WHERE am.state = 'posted'
            AND am.company_id IN %s
        )
        UPDATE account_move_line aml
        SET cuo_sequence = nl.seq
        FROM numbered_lines nl
        WHERE aml.id = nl.id
    """, (tuple(company_ids.ids),))
    
    env.cr.commit()


def _assign_table35_to_countries(env):
    """Assign l10n_pe_edi.table.35 entries to res.country records.

    Uses active_test=False so archived countries are also updated without
    raising errors.  Any missing table-35 record or country is silently
    skipped so the hook never blocks module installation / upgrade.
    """
    _logger.info("Assigning SUNAT Tabla 35 codes to res.country records...")
    # active_test=False handles archived countries gracefully
    Country = env["res.country"].with_context(active_test=False)
    Table35 = env["l10n_pe_edi.table.35"]
    assigned = 0
    for iso_code, sunat_code in _ISO_TO_TABLE35.items():
        try:
            country = Country.search([("code", "=", iso_code)], limit=1)
            if not country:
                continue
            table35 = Table35.search([("code", "=", sunat_code)], limit=1)
            if not table35:
                _logger.warning(
                    "Tabla 35 record with code %s not found; skipping ISO %s.",
                    sunat_code,
                    iso_code,
                )
                continue
            country.l10n_pe_reports_country_residence_id = table35.id
            assigned += 1
        except Exception as exc:
            _logger.warning(
                "Could not assign Tabla 35 code %s to country %s: %s",
                sunat_code,
                iso_code,
                exc,
            )
    _logger.info("Finished: %d countries assigned to Tabla 35.", assigned)


def post_init_hook(env):
    _compute_cuo_sequence(env)
    _assign_table35_to_countries(env)
