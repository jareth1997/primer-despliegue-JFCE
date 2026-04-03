# -*- coding: utf-8 -*-
{
    'name': 'Chatter Visibility & Position Control',
    'version': '19.0.1.0.1',
    'category': 'Productivity',
    'summary': 'Control chatter visibility and position in form views with browser-persisted preferences',
    'description': """
Chatter Visibility & Position Control
======================================

Enhanced control over the chatter panel in Odoo form views.

Key Features:
-------------
* **Show/Hide Toggle**: Instantly show or hide the chatter panel with a single click
* **Position Control**: Move chatter to Right (default), Bottom
* **Smart Button**: Control button appears only in form views
* **Persistent Preferences**: Your settings are saved in browser and restored automatically
* **User-Friendly**: Intuitive dropdown menu for easy control
* **Responsive Design**: Smooth transitions and animations

Perfect for users who want to customize their workspace and maximize screen real estate.

Usage:
------
1. Open any form view
2. Look for the chatter control button in the top navigation bar
3. Toggle visibility or change position as needed
4. Your preferences are automatically saved

Technical:
----------
* Uses localStorage for preference persistence
* Lightweight JavaScript implementation
* No database modifications required
* Compatible with all standard Odoo models with chatter

    """,
    'author': 'LotusTech Odoo',
    'website': 'https://www.youtube.com/@LotusTechOdoo',
    'license': 'OPL-1',
    'depends': ['web', 'mail'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'chatter_visibility/static/src/js/chatter_visibility.js',
            'chatter_visibility/static/src/xml/chatter_visibility.xml',
            'chatter_visibility/static/src/scss/chatter_visibility.scss',
        ],
    },
    'images': [
        'static/description/banner.gif',
        # 'static/description/icon.png',
        # 'static/description/screenshot_1.png',
        # 'static/description/screenshot_2.png',
        # 'static/description/screenshot_3.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    # 'price': 12.00,
    'currency': 'USD',
}
