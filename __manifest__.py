# -*- coding: utf-8 -*-
################################################################################
#
#    Renace Tech
#    Copyright (C) 2025 Renace Tech (<https://renace.tech>).
#    Author: Adderly Marte (adderly@renace.tech)
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
    'name': "Dashboard POS Avanzado",
    'version': '18.0.1.0.1',
    'category': 'Punto de Venta',
    'summary': """Dashboard avanzado para análisis de ventas POS con métricas en tiempo real""",
    'description': """
        Dashboard POS Avanzado
        ======================
        
        Características principales:
        - Métricas en tiempo real (Ventas, Artículos, Ganancias)
        - Producto más vendido con imagen
        - Filtros dinámicos por fecha y configuración POS
        - Análisis de vendedores y métodos de pago
        - Gráficos interactivos de ventas
        - Diseño responsive y moderno
        - Integración completa con contabilidad
    """,
    'author': 'Adderly Marte - Renace Tech',
    'company': 'Renace Tech',
    'maintainer': 'Renace Tech',
    'website': "https://renace.tech",
    'depends': ['hr', 'point_of_sale', 'web', 'account'],
    'data': [
        'views/pos_order_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'dashboard_pos/static/src/xml/pos_dashboard.xml',
            'dashboard_pos/static/src/js/pos_dashboard.js',
            'dashboard_pos/static/src/css/pos_dashboard.css',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js'
        ],
    },
    'license': "AGPL-3",
    'installable': True,
    'application': False,
    'auto_install': False,
}
