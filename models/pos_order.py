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
import logging
import base64
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """Dashboard POS - Modelo extendido para análisis de ventas"""
    _inherit = 'pos.order'

    @api.model
    def get_department(self, option):
        """ Función para obtener los detalles de pedidos por compañía con integración contable usando el ORM de Odoo"""

        company_id = self.env.company.id
        pos_orders = self.search([('company_id', '=', company_id)])

        if not pos_orders:
            return [[], [], [], 'DÍAS']

        if option == 'pos_daily_sales':
            # Agrupar por día (últimos 30 días)
            daily_data = defaultdict(lambda: {'pos_amount': 0, 'accounting_amount': 0})
            today = datetime.now().date()
            start_date = today - timedelta(days=30)

            for order in pos_orders.filtered(lambda o: o.date_order.date() >= start_date):
                day = order.date_order.date()
                daily_data[day]['pos_amount'] += order.amount_total
                if order.account_move:
                    daily_data[day]['accounting_amount'] += order.account_move.amount_total

            order = [daily_data[day]['pos_amount'] for day in sorted(daily_data.keys())]
            accounting_totals = [daily_data[day]['accounting_amount'] for day in sorted(daily_data.keys())]
            today = [str(day) for day in sorted(daily_data.keys())]
            label = 'DÍAS'

        elif option == 'pos_weekly_sales':
            # Agrupar por semana (últimas 12 semanas)
            weekly_data = defaultdict(lambda: {'pos_amount': 0, 'accounting_amount': 0})
            today = datetime.now().date()
            start_date = today - timedelta(weeks=12)

            for order in pos_orders.filtered(lambda o: o.date_order.date() >= start_date):
                week = order.date_order.isocalendar()[1]
                year = order.date_order.year
                week_key = f"{year}-S{week}"
                weekly_data[week_key]['pos_amount'] += order.amount_total
                if order.account_move:
                    weekly_data[week_key]['accounting_amount'] += order.account_move.amount_total

            order = [weekly_data[week]['pos_amount'] for week in sorted(weekly_data.keys())]
            accounting_totals = [weekly_data[week]['accounting_amount'] for week in sorted(weekly_data.keys())]
            today = sorted(weekly_data.keys())
            label = 'SEMANAS'

        elif option == 'pos_biweekly_sales':
            # Agrupar por quincena (últimas 12 quincenas)
            biweekly_data = defaultdict(lambda: {'pos_amount': 0, 'accounting_amount': 0})
            today = datetime.now().date()
            start_date = today - timedelta(days=180)

            for order in pos_orders.filtered(lambda o: o.date_order.date() >= start_date):
                day = order.date_order.day
                month = order.date_order.month
                year = order.date_order.year
                quinc = 'Q1' if day <= 15 else 'Q2'
                quinc_key = f"{year}-{month:02d}-{quinc}"
                biweekly_data[quinc_key]['pos_amount'] += order.amount_total
                if order.account_move:
                    biweekly_data[quinc_key]['accounting_amount'] += order.account_move.amount_total

            order = [biweekly_data[quinc]['pos_amount'] for quinc in sorted(biweekly_data.keys())]
            accounting_totals = [biweekly_data[quinc]['accounting_amount'] for quinc in sorted(biweekly_data.keys())]
            today = sorted(biweekly_data.keys())
            label = 'QUINCENAS'

        elif option == 'pos_monthly_sales':
            # Agrupar por mes (último año)
            monthly_data = defaultdict(lambda: {'pos_amount': 0, 'accounting_amount': 0})

            for order in pos_orders.filtered(lambda o: o.date_order.year == datetime.now().year):
                month = order.date_order.strftime('%Y-%m')
                monthly_data[month]['pos_amount'] += order.amount_total
                if order.account_move:
                    monthly_data[month]['accounting_amount'] += order.account_move.amount_total

            order = [monthly_data[month]['pos_amount'] for month in sorted(monthly_data.keys())]
            accounting_totals = [monthly_data[month]['accounting_amount'] for month in sorted(monthly_data.keys())]
            today = sorted(monthly_data.keys())
            label = 'MESES'

        else:
            # Por defecto, mostrar diario
            daily_data = defaultdict(lambda: {'pos_amount': 0, 'accounting_amount': 0})
            today_date = datetime.now().date()
            start_date = today_date - timedelta(days=30)

            for order in pos_orders.filtered(lambda o: o.date_order.date() >= start_date):
                day = order.date_order.date()
                daily_data[day]['pos_amount'] += order.amount_total
                if order.account_move:
                    daily_data[day]['accounting_amount'] += order.account_move.amount_total

            order = [daily_data[day]['pos_amount'] for day in sorted(daily_data.keys())]
            accounting_totals = [daily_data[day]['accounting_amount'] for day in sorted(daily_data.keys())]
            today = [str(day) for day in sorted(daily_data.keys())]
            label = 'DÍAS'

        final = [order, accounting_totals, today, label]
        return final

    @api.model
    def get_details(self):
        """ Función para obtener los detalles de pago con integración contable utilizando el ORM de Odoo"""
        company_id = self.env.company.id

        # Obtener detalles de pago utilizando el ORM de Odoo
        payment_methods = self.env['pos.payment.method'].search([])
        payment_details = []

        for method in payment_methods:
            pos_payments = self.env['pos.payment'].search([
                ('payment_method_id', '=', method.id)
            ])
            pos_amount = sum(pos_payments.mapped('amount'))

            # Obtener el monto conciliado en contabilidad si está disponible
            accounting_amount = 0
            # Por ahora, se usan las facturas vinculadas a pedidos POS como monto contable
            # Esto brinda la integración principal sin consultas de conciliación complejas
            pos_orders_with_payments = self.env['pos.order'].search([
                ('company_id', '=', company_id),
                ('payment_ids.payment_method_id', '=', method.id)
            ])
            for order in pos_orders_with_payments:
                if order.account_move:
                    accounting_amount += order.account_move.amount_total

            payment_details.append((method.name, pos_amount, accounting_amount))

        # Ordenar por monto POS de forma descendente
        payment_details.sort(key=lambda x: x[1], reverse=True)

        # Obtener detalles de vendedores utilizando el ORM de Odoo
        employees = self.env['hr.employee'].search([])
        salesperson = []

        for employee in employees:
            if not employee.user_id:
                continue

            pos_orders = self.env['pos.order'].search([
                ('user_id', '=', employee.user_id.id),
                ('company_id', '=', company_id)
            ])
            if not pos_orders:
                continue

            pos_total = sum(pos_orders.mapped('amount_paid'))
            orders_count = len(pos_orders)

            # Obtener total contable si está disponible
            accounting_total = 0
            for order in pos_orders:
                if order.account_move:
                    accounting_total += order.account_move.amount_total

            salesperson.append((
                employee.name,
                pos_total,
                orders_count,
                accounting_total
            ))

        # Ordenar por total POS de forma descendente
        salesperson.sort(key=lambda x: x[1], reverse=True)

        # Obtener los productos más vendidos utilizando el ORM de Odoo
        order_lines = self.env['pos.order.line'].search([
            ('company_id', '=', company_id)
        ])
        product_quantities = defaultdict(lambda: {'pos_quantity': 0, 'accounting_quantity': 0})

        for line in order_lines:
            template = line.product_id.product_tmpl_id
            product_quantities[template]['pos_quantity'] += line.qty

            # Obtener cantidades contables si están disponibles
            if hasattr(line, 'account_move_line_ids'):
                for move_line in line.account_move_line_ids:
                    product_quantities[template]['accounting_quantity'] += move_line.quantity

        # Obtener los 10 productos principales
        top_products = sorted(
            product_quantities.items(),
            key=lambda x: x[1]['pos_quantity'],
            reverse=True
        )[:10]

        selling_product = []
        for template, quantities in top_products:
            selling_product.append({
                'product_name': template.name,
                'quantity': quantities['pos_quantity']
            })

        # Obtener información de sesiones utilizando el ORM de Odoo
        sessions = self.env['pos.config'].search([])
        sessions_list = []

        for session in sessions:
            # Obtener todos los pedidos POS de esta sesión mediante las sesiones POS
            pos_sessions = self.env['pos.session'].search([
                ('config_id', '=', session.id)
            ])
            order_ids = []
            for pos_session in pos_sessions:
                order_ids.extend(pos_session.order_ids.ids)

            account_moves = self.env['pos.order'].browse(order_ids).mapped('account_move') if order_ids else self.env['account.move'].browse([])

            # Filtrar asientos vacíos en caso de que algunos pedidos aún no estén contabilizados
            account_moves = account_moves.filtered(lambda move: move)

            # Obtener el estado de la sesión más reciente
            session_state = 'closed'
            if pos_sessions:
                # Obtener el estado de la sesión más reciente
                latest_session = max(pos_sessions, key=lambda s: s.start_at or s.create_date)
                session_state = latest_session.state

            status_dict = {
                'opened': _('Abierto'),
                'opening_control': _("Control de Apertura")
            }

            status = status_dict.get(session_state, _('Cerrado'))

            sessions_list.append({
                'session': session.name,
                'status': status,
                'accounting_moves': len(account_moves)
            })

        # Formatear detalles de pago con la moneda
        payments = []
        for name, pos_amount, accounting_amount in payment_details:
            company = self.env.company
            if company.currency_id.position == 'after':
                pos_formatted = "%s %s" % (pos_amount, company.currency_id.symbol)
                accounting_formatted = "%s %s" % (accounting_amount, company.currency_id.symbol)
            else:
                pos_formatted = "%s %s" % (company.currency_id.symbol, pos_amount)
                accounting_formatted = "%s %s" % (company.currency_id.symbol, accounting_amount)

            payments.append((name, pos_formatted, accounting_formatted))

        # Obtener configuraciones POS disponibles para filtros dinámicos
        configs = self.env['pos.config'].search([('company_id', '=', company_id)])
        config_options = [{'id': config.id, 'name': config.display_name} for config in configs]

        # Formatear detalles de vendedores con la moneda
        total_sales = []
        for name, pos_amount, orders, accounting_amount in salesperson:
            company = self.env.company
            if company.currency_id.position == 'after':
                pos_formatted = "%s %s" % (pos_amount, company.currency_id.symbol)
                accounting_formatted = "%s %s" % (accounting_amount, company.currency_id.symbol)
            else:
                pos_formatted = "%s %s" % (company.currency_id.symbol, pos_amount)
                accounting_formatted = "%s %s" % (company.currency_id.symbol, accounting_amount)

            total_sales.append((name, pos_formatted, orders, accounting_formatted))

        return {
            'payment_details': payments,
            'salesperson': total_sales,
            'selling_product': selling_product,
            'sessions': sessions_list,
            'configs': config_options,
        }

    def _normalize_datetime(self, value):
        """Normaliza un valor de fecha/hora a formato Odoo"""
        if not value:
            return False
        if isinstance(value, datetime):
            return fields.Datetime.to_string(value)
        if isinstance(value, str):
            candidate = value.strip()
            if 'T' in candidate:
                candidate = candidate.replace('T', ' ')
            if len(candidate) == 16:
                candidate = f"{candidate}:00"
            try:
                python_dt = datetime.strptime(candidate, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    python_dt = datetime.fromisoformat(value)
                except ValueError:
                    try:
                        python_dt = fields.Datetime.from_string(value)
                    except Exception as e:
                        _logger.warning(f"No se pudo parsear fecha '{value}': {e}")
                        return False
            return fields.Datetime.to_string(python_dt)
        return False

    @api.model
    def get_dynamic_sales_details(self, filters):
        """
        Obtener detalle dinámico de ventas para el tablero.
        Inspirado en pos.details.wizard pero optimizado para el dashboard.
        """
        filters = filters or {}
        company_id = self.env.company.id

        # Normalizar fechas
        start_date = self._normalize_datetime(filters.get('start_date'))
        end_date = self._normalize_datetime(filters.get('end_date'))
        config_ids = filters.get('config_ids') or []

        # Construir dominio base
        domain = [
            ('company_id', '=', company_id),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ]
        
        if start_date:
            domain.append(('date_order', '>=', start_date))
        if end_date:
            domain.append(('date_order', '<=', end_date))
        if config_ids:
            domain.append(('config_id', 'in', config_ids))

        # Buscar órdenes
        try:
            orders = self.search(domain, order='date_order desc')
        except Exception as e:
            _logger.error(f"Error al buscar órdenes: {e}")
            orders = self.env['pos.order'].browse([])
            
        currency = self.env.company.currency_id

        # Calcular totales usando métodos optimizados
        all_lines = orders.mapped('lines')
        
        # Filtrar líneas excluyendo productos de "Anticipo"
        # Buscar productos que contengan "anticipo" en su nombre (case-insensitive)
        lines = all_lines.filtered(
            lambda line: line.product_id and 
            'anticipo' not in line.product_id.display_name.lower()
        )
        
        _logger.info(f"Total lines: {len(all_lines)}, Filtered lines (sin anticipo): {len(lines)}")
        
        # Totales básicos (excluyendo anticipos)
        total_quantity = sum(lines.mapped('qty'))
        total_amount = sum(lines.mapped('price_subtotal_incl'))  # Solo líneas sin anticipo
        tax_amount = sum(line.price_subtotal_incl - line.price_subtotal for line in lines)
        untaxed_amount = total_amount - tax_amount

        # Calcular por producto (similar a pos.details.wizard)
        # Usar ID del producto como clave para mejor eficiencia
        product_totals = defaultdict(lambda: {
            'quantity': 0.0,
            'amount': 0.0,
            'discount': 0.0,
            'cost': 0.0,
            'product_obj': None
        })
        
        total_profit = 0.0
        
        for line in lines:
            product = line.product_id
            if not product:
                continue
                
            product_id = product.id
            
            # Guardar referencia al objeto producto
            if not product_totals[product_id]['product_obj']:
                product_totals[product_id]['product_obj'] = product
            
            # Cantidad y monto
            product_totals[product_id]['quantity'] += line.qty
            product_totals[product_id]['amount'] += line.price_subtotal_incl
            
            # Descuento
            if line.discount:
                discount_value = (line.qty * line.price_unit) * (line.discount / 100.0)
                product_totals[product_id]['discount'] += discount_value
            
            # Costo y ganancia
            # Usa standard_price (costo estándar del producto)
            cost = (product.standard_price or 0.0) * line.qty
            product_totals[product_id]['cost'] += cost
            
            # Ganancia = Precio de venta - Costo
            profit = line.price_subtotal_incl - cost
            total_profit += profit
        
        # Producto más vendido
        top_product_name = _('N/A')
        top_product_qty = 0.0
        top_product_image = False
        top_product_id = False
        
        if product_totals:
            # Encontrar el producto con mayor cantidad
            top_product_id, top_data = max(
                product_totals.items(),
                key=lambda x: x[1]['quantity']
            )
            top_product_obj = top_data['product_obj']
            
            if top_product_obj:
                top_product_name = top_product_obj.display_name
                top_product_qty = top_data['quantity']
                # Obtener la imagen del producto (image_128 para mejor rendimiento)
                # La imagen ya viene en base64 desde Odoo
                if top_product_obj.image_128:
                    # Convertir bytes a string si es necesario
                    if isinstance(top_product_obj.image_128, bytes):
                        top_product_image = base64.b64encode(top_product_obj.image_128).decode('utf-8')
                    else:
                        # Ya es string en base64
                        top_product_image = top_product_obj.image_128
                else:
                    top_product_image = False
                
                _logger.info(f"Top product: {top_product_name}, has image: {bool(top_product_image)}")

        # Datos de productos ordenados por cantidad (descendente)
        products_data = [
            {
                'key': product_id,
                'product_name': values['product_obj'].display_name if values['product_obj'] else _('Sin producto'),
                'quantity': values['quantity'],
                'amount': values['amount'],
                'discount': values['discount'],
                'cost': values['cost'],
                'profit': values['amount'] - values['cost'],
            }
            for product_id, values in sorted(
                product_totals.items(),
                key=lambda item: item[1]['quantity'],
                reverse=True
            )
        ]

        # Agrupar impuestos (similar a pos.details.wizard)
        tax_groups = defaultdict(lambda: {'base': 0.0, 'tax': 0.0})
        for line in lines:
            tax_amount_line = line.price_subtotal_incl - line.price_subtotal
            if not line.tax_ids_after_fiscal_position:
                label = _('Exento')
            else:
                label = ', '.join(line.tax_ids_after_fiscal_position.mapped('name'))
            tax_groups[label]['base'] += line.price_subtotal
            tax_groups[label]['tax'] += tax_amount_line

        taxes_data = [
            {
                'name': name,
                'base': values['base'],
                'tax': values['tax'],
            }
            for name, values in tax_groups.items()
        ]

        # Métodos de pago agrupados
        payments = orders.mapped('payment_ids')
        payment_groups = []
        if payments:
            payment_methods = payments.mapped('payment_method_id')
            for method in payment_methods:
                method_payments = payments.filtered(lambda p: p.payment_method_id == method)
                payment_groups.append({
                    'method': method.name,
                    'amount': sum(method_payments.mapped('amount')),
                    'count': len(method_payments),
                })

        # Descuentos totales
        discount_lines = lines.filtered(lambda l: l.discount > 0)
        discount_total = sum(
            (line.qty * line.price_unit) * (line.discount / 100.0)
            for line in discount_lines
        )

        # Facturas relacionadas
        invoices = [
            {
                'invoice': order.account_move.name,
                'order': order.name,
                'amount': order.account_move.amount_total,
            }
            for order in orders if order.account_move
        ]

        # Sesiones relacionadas
        sessions = orders.mapped('session_id')
        sessions_data = [
            {
                'name': session.name,
                'opening': session.cash_register_balance_start or 0.0,
                'expected': session.cash_register_balance_end or 0.0,
                'counted': session.cash_register_balance_end_real or 0.0,
                'difference': session.cash_register_difference or 0.0,
                'transactions': len(session.order_ids),
            }
            for session in sessions
        ]

        # Log para debugging
        _logger.info(
            f"Dashboard data calculated: {len(orders)} orders, "
            f"{len(lines)} lines, Total: {total_amount:.2f}, "
            f"Profit: {total_profit:.2f}"
        )

        return {
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'config_ids': config_ids,
            },
            'summary': {
                'total_quantity': total_quantity,
                'total_amount': total_amount,
                'tax_amount': tax_amount,
                'untaxed_amount': untaxed_amount,
                'top_product_name': top_product_name,
                'top_product_qty': top_product_qty,
                'top_product_image': top_product_image,
                'top_product_id': top_product_id,
                'total_profit': total_profit,
                'orders_count': len(orders),
            },
            'products': products_data,
            'taxes': taxes_data,
            'payments': payment_groups,
            'discounts': {
                'count': len(discount_lines),
                'amount': discount_total,
            },
            'invoices': invoices,
            'sessions': sessions_data,
            'currency': {
                'symbol': currency.symbol,
                'position': currency.position,
                'decimal_places': currency.decimal_places,
            }
        }

    @api.model
    def get_refund_details(self):
        """ Función para obtener los detalles de devoluciones con integración contable"""
        default_date = datetime.today().date()
        company_id = self.env.company.id

        # Obtener pedidos POS con información de devoluciones
        pos_order = self.env['pos.order'].search([('company_id', '=', company_id)])

        total = 0
        today_refund_total = 0
        total_order_count = 0
        total_refund_count = 0
        today_sale = 0
        total_pos_amount = 0
        total_accounting_amount = 0

        for rec in pos_order:
            pos_amount = rec.amount_total or 0
            total_pos_amount += pos_amount
            total_order_count += 1

            if rec.date_order.date() == default_date:
                today_sale += 1

            if pos_amount < 0.0:
                total_refund_count += 1
                if rec.date_order.date() == default_date:
                    today_refund_total += 1

            # Obtener el monto contable para este pedido POS
            if rec.account_move:
                accounting_move = self.env['account.move'].browse(rec.account_move.id)
                accounting_amount = accounting_move.amount_total or 0
                total_accounting_amount += accounting_amount

        # Usar el mayor valor entre POS o contabilidad para mostrar
        total = max(total_pos_amount, total_accounting_amount)

        magnitude = 0
        while abs(total) >= 1000:
            magnitude += 1
            total /= 1000.0
        # add more suffixes if you need them
        val = '%.2f%s' % (total, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])

        # Obtener información de sesiones con conciliación contable
        pos_session = self.env['pos.session'].search([('company_id', '=', company_id)])
        total_session = 0
        reconciled_sessions = 0

        for record in pos_session:
            total_session += 1
            # Comprobar si la sesión ha sido conciliada en contabilidad
            if record.move_id:
                reconciled_sessions += 1

        return {
            'total_sale': val,
            'total_order_count': total_order_count,
            'total_refund_count': total_refund_count,
            'total_session': total_session,
            'reconciled_sessions': reconciled_sessions,
            'today_refund_total': today_refund_total,
            'today_sale': today_sale,
        }

    @api.model
    def get_the_top_customer(self):
        """ Obtener los principales clientes con integración contable mediante el ORM de Odoo"""
        company_id = self.env.company.id

        # Obtener clientes con sus totales POS y contables
        partners = self.env['res.partner'].search([])
        customer_data = []

        for partner in partners:
            pos_orders = self.env['pos.order'].search([
                ('partner_id', '=', partner.id),
                ('company_id', '=', company_id)
            ])
            if not pos_orders:
                continue

            pos_amount = sum(pos_orders.mapped('amount_paid'))

            # Obtener total contable si está disponible
            accounting_amount = 0
            for order in pos_orders:
                if order.account_move:
                    accounting_amount += order.account_move.amount_total

            customer_data.append({
                'customer': partner.name,
                'pos_amount': pos_amount,
                'accounting_amount': accounting_amount
            })

        # Ordenar por monto POS de forma descendente y tomar los 10 primeros
        customer_data.sort(key=lambda x: x['pos_amount'], reverse=True)
        top_customers = customer_data[:10]

        order = [customer['pos_amount'] for customer in top_customers]
        accounting_totals = [customer['accounting_amount'] for customer in top_customers]
        day = [customer['customer'] for customer in top_customers]

        return [order, accounting_totals, day]

    @api.model
    def get_the_top_products(self):
        """ Función para obtener los productos destacados con integración contable mediante el ORM de Odoo"""
        company_id = self.env.company.id

        # Obtener líneas de pedido y agregar cantidades
        order_lines = self.env['pos.order.line'].search([
            ('company_id', '=', company_id)
        ])

        product_quantities = defaultdict(lambda: {'pos_quantity': 0, 'accounting_quantity': 0})

        for line in order_lines:
            template = line.product_id.product_tmpl_id
            product_quantities[template]['pos_quantity'] += line.qty

            # Obtener cantidades contables si están disponibles
            if hasattr(line, 'account_move_line_ids'):
                for move_line in line.account_move_line_ids:
                    product_quantities[template]['accounting_quantity'] += move_line.quantity

        # Convertir a lista y ordenar por cantidad POS
        products_list = [
            (template, data)
            for template, data in product_quantities.items()
        ]
        products_list.sort(key=lambda x: x[1]['pos_quantity'], reverse=True)

        # Tomar los 10 principales
        top_products = products_list[:10]

        total_quantity = [data['pos_quantity'] for template, data in top_products]
        accounting_quantities = [data['accounting_quantity'] for template, data in top_products]
        product_name = [template.name for template, data in top_products]

        return [total_quantity, accounting_quantities, product_name]

    @api.model
    def get_the_top_categories(self):
        """ Función para obtener las principales categorías de productos con integración contable mediante el ORM de Odoo"""
        company_id = self.env.company.id

        # Obtener líneas de pedido y agregar cantidades por categoría
        order_lines = self.env['pos.order.line'].search([
            ('company_id', '=', company_id)
        ])

        category_quantities = defaultdict(lambda: {'pos_quantity': 0, 'accounting_quantity': 0})

        for line in order_lines:
            if line.product_id and line.product_id.product_tmpl_id.categ_id:
                category = line.product_id.product_tmpl_id.categ_id
                category_quantities[category]['pos_quantity'] += line.qty

                # Obtener cantidades contables si están disponibles
                if hasattr(line, 'account_move_line_ids'):
                    for move_line in line.account_move_line_ids:
                        category_quantities[category]['accounting_quantity'] += move_line.quantity

        # Convertir a lista y ordenar por cantidad POS
        categories_list = [
            (category, data['pos_quantity'], data['accounting_quantity'])
            for category, data in category_quantities.items()
        ]
        categories_list.sort(key=lambda x: x[1], reverse=True)

        # Tomar todas las categorías (sin límite como en productos)
        total_quantity = [category[1] for category in categories_list]
        accounting_quantities = [category[2] for category in categories_list]
        product_categ = [category[0].complete_name for category in categories_list]

        return [total_quantity, accounting_quantities, product_categ]
