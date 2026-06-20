# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Tablero POS",
    'version': '18.0.1.0.1',
    'category': 'Point of Sale',
    'summary': "Tablero detallado para Punto de Venta",
    'description': "Tablero de POS con métricas, filtros por fechas y gráficos",
    'author': 'Adderly Marte',
    'company': 'Renace Tech',
    'maintainer': 'Adderly Marte',
    'website': "https://renace.tech",
    'depends': ['hr', 'point_of_sale', 'web'],
    'data': [
        'views/pos_order_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'dashboard_pos/static/src/xml/pos_dashboard.xml',
            'dashboard_pos/static/src/js/pos_dashboard.js',
            'dashboard_pos/static/src/css/pos_dashboard.css',
            'dashboard_pos/static/lib/chartjs/chart.umd.min.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
