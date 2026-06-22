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
import pytz
import re
from datetime import datetime, timedelta
from odoo import api, models


class PosOrder(models.Model):
    """ Inherited class of pos dashboard to add features of dashboard"""
    _inherit = 'pos.order'
    
    def _is_mod_active(self, module_name, setting_key=None):
        """Check if a module is installed and (optionally) if its feature toggle is enabled."""
        # Use registry as source of truth for installation
        is_installed = module_name in self.env.registry
        if not is_installed:
            return False
        if setting_key:
            # Check system parameter, defaults to 'True' if not set but module is installed
            val = self.env['ir.config_parameter'].sudo().get_param(setting_key, 'True')
            return val.lower() in ('true', '1', 'yes')
        return True

    def _extract_filters(self, filters):
        start_dt = end_dt = None
        pos_ids = []
        session_ids = []
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        if isinstance(filters, dict):
            start = filters.get('start_date')
            end = filters.get('end_date')
            start_time = filters.get('start_time') or None
            end_time = filters.get('end_time') or None
            if start:
                try:
                    dt = datetime.strptime(start, '%Y-%m-%d')
                    if start_time:
                        try:
                            parts = [int(p) for p in str(start_time).split(':')]
                            hour = parts[0] if len(parts) > 0 else 0
                            minute = parts[1] if len(parts) > 1 else 0
                        except Exception:
                            hour = 0
                            minute = 0
                        dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    else:
                        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    local_dt = tz.localize(dt)
                    start_dt = local_dt.astimezone(pytz.UTC).replace(tzinfo=None)
                except Exception:
                    start_dt = None
            if end:
                try:
                    dt = datetime.strptime(end, '%Y-%m-%d')
                    if end_time:
                        try:
                            parts = [int(p) for p in str(end_time).split(':')]
                            hour = parts[0] if len(parts) > 0 else 23
                            minute = parts[1] if len(parts) > 1 else 59
                        except Exception:
                            hour = 23
                            minute = 59
                        dt = dt.replace(hour=hour, minute=minute, second=59, microsecond=0)
                    else:
                        dt = dt.replace(hour=23, minute=59, second=59, microsecond=0)
                    local_dt = tz.localize(dt)
                    end_dt = local_dt.astimezone(pytz.UTC).replace(tzinfo=None)
                except Exception:
                    end_dt = None
            pos_ids = filters.get('pos_ids') or filters.get('pos_config_ids') or []
            session_ids = filters.get('session_ids') or []
        # defaults to current day if no dates provided and no explicit sessions
        if not session_ids and (not start_dt or not end_dt):
            now_local = datetime.now(tz)
            start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
            if not start_dt:
                start_dt = start_local.astimezone(pytz.UTC).replace(tzinfo=None)
            if not end_dt:
                end_dt = end_local.astimezone(pytz.UTC).replace(tzinfo=None)
        return start_dt, end_dt, pos_ids, session_ids

    def _build_where_clause(self, filters):
        # Multi-compañía: limitar por compañías permitidas del usuario
        allowed_companies = self.env.companies.ids or [self.env.company.id]
        where = ["pos_order.company_id IN %s"]
        params = [tuple(allowed_companies)]
        start_dt, end_dt, pos_ids, session_ids = self._extract_filters(filters)
        if session_ids:
            # En pos.order el campo estándar de sesión es session_id
            where.append("pos_order.session_id IN %s")
            params.append(tuple(session_ids))
        else:
            if start_dt:
                where.append("pos_order.date_order >= %s")
                params.append(start_dt)
            if end_dt:
                where.append("pos_order.date_order <= %s")
                params.append(end_dt)
        if pos_ids:
            where.append("pos_order.config_id IN %s")
            params.append(tuple(pos_ids))
        return " AND ".join(where), params

    @api.model
    def get_department(self, option, filters=None):
        """ Function to get the order details grouped for charts, with optional filters """

        if option not in ('pos_hourly_sales', 'pos_monthly_sales', 'pos_year_sales'):
            option = 'pos_monthly_sales'
        where, params = self._build_where_clause(filters)
        user_tz = self.env.user.tz if self.env.user.tz else 'UTC'
        if option == 'pos_hourly_sales':
            tz = str(user_tz).replace("'", "''")
            query = (
                """select EXTRACT(hour FROM date_order at time zone 'utc' at time zone '{tz}') as date_month,
                           sum(amount_total) as sum
                       from pos_order where {where}
                       group by date_month order by date_month"""
            ).format(where=where, tz=tz)
            exec_params = params
            label = 'Horas'
        elif option == 'pos_monthly_sales':
            query = (
                """select date_order::date as date_month, sum(amount_total) as sum
                       from pos_order where {where}
                       group by date_month order by date_month"""
            ).format(where=where)
            exec_params = params
            label = 'Días'
        else:
            query = (
                """select TO_CHAR(date_order,'MON') as date_month, sum(amount_total) as sum
                       from pos_order where {where}
                       group by date_month"""
            ).format(where=where)
            exec_params = params
            label = 'Meses'
        self._cr.execute(query, tuple(exec_params))
        docs = self._cr.dictfetchall()
        order = []
        for record in docs:
            order.append(record.get('sum'))
        today = []
        for record in docs:
            today.append(record.get('date_month'))
        final = [order, today, label]
        return final

    def _get_dashboard_cost_expr(self, alias_po='pos_order', alias_pol='pos_order_line', alias_pp='product_product', alias_pt='product_template', alias_uu='uu'):
        """ Centralized cost expression logic for all dashboard queries.
            Dynamically detects if standard_price is on product_product or product_template.
        """
        # 1. Detect which table has standard_price and its type
        self.env.cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'product_product' AND column_name = 'standard_price'")
        res = self.env.cr.fetchone()
        if res:
            cost_alias = alias_pp
            data_type = res[0]
        else:
            self.env.cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'product_template' AND column_name = 'standard_price'")
            res = self.env.cr.fetchone()
            cost_alias = alias_pt
            data_type = res[0] if res else 'numeric'
            
        is_cost_json = data_type == 'jsonb'
        
        # 1. Base Cost Expression (Standard Price)
        if is_cost_json:
            base_cost_expr = f"({cost_alias}.standard_price ->> {alias_po}.company_id::text)::numeric"
        else:
            base_cost_expr = f"{cost_alias}.standard_price"

        if alias_uu:
            base_cost_expr = f"({base_cost_expr} * COALESCE({alias_uu}.factor_inv, 1.0))"

        # 2. Check for line_cost column (Odoo 18 / Custom)
        has_line_cost = 'line_cost' in self.env['pos.order.line']._fields
        if has_line_cost:
            base_cost_expr = f"COALESCE({alias_pol}.line_cost, {base_cost_expr}, 0)"
        else:
            base_cost_expr = f"COALESCE({base_cost_expr}, 0)"

        # 3. Max Robustness Fallback for Repairs
        # Use simple constant if module not present to avoid SQL crashes
        has_mobile = 'mobile_repair_ticket' in self.env.registry
        use_mobile_cost = self._is_mod_active('mobile_service', 'dashboard_pos.enable_mobile_cost')
        
        if has_mobile and use_mobile_cost:
            repair_fallback = f"""(SELECT total_parts_cost FROM mobile_repair_ticket 
                                  WHERE partner_id = {alias_po}.partner_id 
                                  AND ABS(amount_total - {alias_pol}.price_subtotal_incl) < 1.0
                                  AND create_date >= CURRENT_DATE - INTERVAL '3 days'
                                  ORDER BY id DESC LIMIT 1)"""
            return f"COALESCE({repair_fallback}, {base_cost_expr})"
        
        return base_cost_expr

    @api.model
    def get_details(self, filters=None):
        """ Function to get the payment details with optional filters """
        cr = self._cr
        where, params = self._build_where_clause(filters)

        # Use unified cost expression (dynamically detects pp/pt for cost)
        cost_expr = self._get_dashboard_cost_expr('pos_order', 'pos_order_line', 'product_product', 'product_template')
        
        pol_fields = self.env['pos.order.line']._fields
        found_cols = [c for c in ('sale_order_line_id', 'sale_line_id') if c in pol_fields]
        use_sale_id = bool(found_cols)
        sale_col = found_cols[0] if found_cols else 'sale_line_id'

        use_ticket_id = 'mobile_ticket_id' in self.env['pos.order']._fields

        pt_name_field = self.env['product.template']._fields.get('name')
        is_name_json = pt_name_field and pt_name_field.translate
        name_expr = "(product_template.name ->> %s)" if is_name_json else "product_template.name"

        user_lang = self.env.user.lang or 'en_US'
        # Exclusión de productos (configurable)
        kw_exclusion = ['anticipo', 'advance', 'down payment', 'deposito', 'depósito', 'adelanto', 'pdv']
        ICP = self.env['ir.config_parameter'].sudo()
        advance_pid_param = ICP.get_param('dashboard_pos.advance_product_id')
        advance_tmpl_param = ICP.get_param('dashboard_pos.advance_product_tmpl_id')
        excluded_param = ICP.get_param('dashboard_pos.excluded_product_ids')
        excluded_ids = set()
        try:
            if advance_pid_param:
                excluded_ids.add(int(advance_pid_param))
        except Exception:
            pass
        try:
            if advance_tmpl_param:
                tmpl_id = int(advance_tmpl_param)
                if tmpl_id:
                    variants = self.env['product.product'].search([('product_tmpl_id', '=', tmpl_id)]).ids
                    excluded_ids.update(variants)
        except Exception:
            pass
        if excluded_param:
            for tok in str(excluded_param).replace(';', ',').split(','):
                tok = tok.strip()
                if tok.isdigit():
                    excluded_ids.add(int(tok))
        if not excluded_ids:
            # Fallback amplio por keywords en nombre del producto o plantilla
            dom_names = ['|'] * (len(kw_exclusion) - 1)
            for kw in kw_exclusion:
                dom_names += [('name', 'ilike', kw)]
            tmpl_candidates = self.env['product.template'].search(dom_names) if kw_exclusion else self.env['product.template']
            if tmpl_candidates:
                variant_ids = self.env['product.product'].search([('product_tmpl_id', 'in', tmpl_candidates.ids)]).ids
                excluded_ids.update(variant_ids)
            # También buscar directamente en product.product por display_name
            dom_disp = ['|'] * (len(kw_exclusion) - 1)
            for kw in kw_exclusion:
                dom_disp += [('display_name', 'ilike', kw)]
            prod_candidates = self.env['product.product'].search(dom_disp)
            excluded_ids.update(prod_candidates.ids)
        def _name_excluded(prod):
            s = f"{prod.display_name or ''} {getattr(prod.product_tmpl_id, 'name', '')}".lower()
            return any(kw in s for kw in kw_exclusion)
        where_po = where.replace('pos_order.', 'po.')
        cr.execute(
            (
                """
                select (pm.name ->> %s) as method,
                       sum(pp.amount) as total,
                       aj.type as jtype,
                       COALESCE(pm.is_cash_count, false) as iscash
                from pos_payment pp
                inner join pos_payment_method pm on pm.id = pp.payment_method_id
                inner join pos_order po on po.id = pp.pos_order_id
                left join account_journal aj on aj.id = pm.journal_id
                where {where}
                group by pm.id, pm.name, aj.type, pm.is_cash_count
                """
            ).format(where=where_po),
            tuple([user_lang] + params),
        )
        payment_rows = cr.dictfetchall()
        cr.execute(
            (
                '''select hr_employee.name,sum(pos_order.amount_paid) as total,count(pos_order.id) as orders 
                   from pos_order inner join hr_employee on pos_order.user_id = hr_employee.user_id 
                   where {where}
                   GROUP BY hr_employee.name order by total DESC;'''
            ).format(where=where),
            tuple(params),
        )
        salesperson = cr.fetchall()
        total_sales = []
        for rec in salesperson:
            # rec is (name, amount, orders)
            amount = rec[1] or 0.0
            currency = self.env.company.currency_id
            total_sales.append({
                'name': rec[0],
                'amount': amount,
                'amount_str': f"{currency.name} {amount:,.2f}",
                'orders': rec[2]
            })

        start_dt, end_dt, pos_ids, session_ids = self._extract_filters(filters)
        sessions_domain = [('company_id', 'in', self.env.companies.ids or [self.env.company.id])]
        if pos_ids:
            sessions_domain.append(('config_id', 'in', pos_ids))
        if start_dt:
            sessions_domain.append(('start_at', '>=', start_dt))
        if end_dt:
            sessions_domain.append(('start_at', '<=', end_dt))
        sessions = self.env['pos.session'].search(sessions_domain, order="id desc", limit=100)
        sessions_list = []
        state_map = {
            'opened': 'Abierta',
            'opening_control': "Control de Apertura",
            'closing_control': "Control de Cierre",
            'closed': 'Cerrada'
        }
        for s in sessions:
            st = state_map.get(s.state, s.state)
            sessions_list.append({
                'id': s.id,
                'name': s.name,
                'state': s.state,
                'status': st,
                'config_id': s.config_id.id,
                'config_name': s.config_id.name,
            })
        currency_code = self.env.company.currency_id.name
        def fmt_money(a):
            try:
                return f"{currency_code} {float(a):,.2f}"
            except Exception:
                return f"{currency_code} {a}"
        # Agrupar efectivo de distintas cajas bajo una sola línea 'Efectivo'
        grouped = {}
        for r in payment_rows:
            raw = (r.get('method') or '').strip()
            method_norm = raw.lower()
            is_cash = bool(r.get('iscash')) or (r.get('jtype') == 'cash') or (method_norm == 'efectivo' or method_norm == 'cash')
            label = 'Efectivo' if is_cash else raw
            label = label.strip()
            grouped[label] = grouped.get(label, 0.0) + float(r.get('total') or 0.0)
        # Ordenar por total desc y formatear
        payments = [(k, fmt_money(v)) for k, v in sorted(grouped.items(), key=lambda x: x[1], reverse=True)]
        cash_method_total = grouped.get('Efectivo', 0.0)
        # Detalle por método de pago (para desplegar en el dashboard)
        cr.execute(
            (
                """
                select (pm.name ->> %s) as method,
                       pp.amount as amount,
                       po.date_order as date_order,
                       po.name as order_name,
                       COALESCE(pm.is_cash_count, false) as iscash,
                       aj.type as jtype,
                       rp.name as partner_name
                from pos_payment pp
                inner join pos_payment_method pm on pm.id = pp.payment_method_id
                inner join pos_order po on po.id = pp.pos_order_id
                left join account_journal aj on aj.id = pm.journal_id
                left join res_partner rp on rp.id = po.partner_id
                where {where}
                """
            ).format(where=where_po),
            tuple([user_lang] + params),
        )
        payment_detail_rows = cr.dictfetchall()
        payment_details_breakdown = {}
        for r in payment_detail_rows:
            raw = (r.get('method') or '').strip()
            method_norm = raw.lower()
            is_cash = bool(r.get('iscash')) or (r.get('jtype') == 'cash') or (method_norm == 'efectivo' or method_norm == 'cash')
            label = 'Efectivo' if is_cash else raw
            label = (label or '').strip() or 'Sin método'
            order_name = (r.get('order_name') or '').strip()
            partner_name = (r.get('partner_name') or '').strip()
            desc_parts = []
            if order_name:
                desc_parts.append(order_name)
            if partner_name:
                desc_parts.append(partner_name)
            description = " - ".join(desc_parts)
            entry = {
                'date': str(r.get('date_order')),
                'amount': float(r.get('amount') or 0.0),
                'amount_str': fmt_money(r.get('amount') or 0.0),
                'description': description,
            }
            payment_details_breakdown.setdefault(label, []).append(entry)
        # cash in/out usando movimientos de caja de sesiones (alineado a pos_rnc_report)
        start_dt, end_dt, pos_ids, session_ids = self._extract_filters(filters)
        allowed_companies = self.env.companies.ids or [self.env.company.id]
        order_domain = [('company_id', 'in', allowed_companies)]
        if session_ids:
            # En pos.order
            order_domain.append(('session_id', 'in', session_ids))
        else:
            if start_dt:
                order_domain.append(('date_order', '>=', start_dt))
            if end_dt:
                order_domain.append(('date_order', '<=', end_dt))
        if pos_ids:
            order_domain.append(('config_id', 'in', pos_ids))
        orders_in_period = self.env['pos.order'].search(order_domain)
        # En account.bank.statement.line sí existe pos_session_id
        absl_domain = [('company_id', 'in', allowed_companies), ('pos_session_id', '!=', False)]
        if pos_ids:
            absl_domain.append(('pos_session_id.config_id', 'in', pos_ids))
        if session_ids:
            absl_domain.append(('pos_session_id', 'in', session_ids))
        else:
            absl_model = self.env['account.bank.statement.line']
            date_field = 'date' if 'date' in absl_model._fields else 'create_date'
            date_is_date = date_field == 'date'
            if start_dt:
                absl_domain.append((date_field, '>=', start_dt.date() if date_is_date else start_dt))
            if end_dt:
                absl_domain.append((date_field, '<=', end_dt.date() if date_is_date else end_dt))
        absl_all = self.env['account.bank.statement.line'].search(absl_domain)
        def _is_pos_cash_move(line):
            s = f"{line.payment_ref or ''} {line.ref or ''} {line.name or ''}"
            s = ' '.join(s.split()).lower()
            if not s:
                return False
            pattern = re.compile(r"pos/\S*[-_/ ]?(en|in|out)\b", re.I)
            if pattern.search(s):
                return True
            keywords = [
                'cash in', 'cash out', 'cash-in', 'cash-out',
                'entrada', 'salida', 'ingreso', 'egreso', 'retiro',
                'entrada de efectivo', 'salida de efectivo'
            ]
            return any(k in s for k in keywords)
        absl = absl_all.filtered(lambda l: _is_pos_cash_move(l))
        cash_in = sum(l.amount for l in absl if l.amount > 0)
        cash_out = sum(-l.amount for l in absl if l.amount < 0)
        # detalles (mismos campos que usa pos_rnc_report): amount, date, reason
        currency_code = self.env.company.currency_id.name
        def format_amt(a):
            try:
                return f"{currency_code} {a:,.2f}"
            except Exception:
                return f"{currency_code} {a}"
        def extract_reason(line):
            # Prioritize payment_ref for human reasons in Odoo 18
            for src in (line.payment_ref, line.name, line.ref):
                s = (src or '').strip()
                if not s:
                    continue
                
                # Odoo 18 specific: Skip sequence-like patterns (e.g., EF2/2026/00446)
                # A sequence usually has '/' or '-' and NO spaces.
                if '/' in s and ' ' not in s and any(c.isdigit() for c in s):
                    continue

                # Refined Regex for Odoo 18:
                # Matches patterns like "POS/00600-out-Reason" or "POS/001-in-Reason"
                # It handles the sequence, the type (in/out), and the trailing hyphen/dash.
                s1 = re.sub(r"^pos/.*?[\-_](en|in|out)[\-_ ]*", "", s, flags=re.I).strip()
                
                # Cleanup common standalone keywords
                s2 = re.sub(r"^(cash\s*(in|out)|entrada|salida|ingreso|egreso|retiro)\b[:\- ]*", "", s1, flags=re.I).strip()
                
                if s2:
                    return s2
                if s1:
                    return s1
            
            # Final fallback: yield whatever is available if no human reason was extracted
            return (line.payment_ref or line.name or line.ref or '').strip()
        def _line_date(line):
            absl_model = self.env['account.bank.statement.line']
            date_field = 'date' if 'date' in absl_model._fields else 'create_date'
            val = getattr(line, date_field, None) or line.create_date
            return str(val)
        cash_in_details = [
            {
                'date': _line_date(l),
                'amount': l.amount,
                'amount_str': format_amt(l.amount),
                'reason': extract_reason(l),
            }
            for l in absl if l.amount > 0
        ]
        cash_out_details = [
            {
                'date': _line_date(l),
                'amount': l.amount,
                'amount_str': format_amt(l.amount),
                'reason': extract_reason(l),
            }
            for l in absl if l.amount < 0
        ]
        cash_in_details.sort(key=lambda x: x['date'], reverse=True)
        cash_out_details.sort(key=lambda x: x['date'], reverse=True)
        # top profit product (ORM: evita problemas jsonb*numeric)
        line_domain = [('order_id', 'in', orders_in_period.ids)]
        if excluded_ids:
            line_domain.append(('product_id', 'not in', list(excluded_ids)))
        lines = self.env['pos.order.line'].search(line_domain)
        profit_by_product = {}
        qty_by_product = {}
        sales_by_product = {}
        has_sol = 'sale_line_id' in self.env['pos.order.line']._fields
        has_ticket = 'mobile_ticket_id' in self.env['pos.order']._fields
        
        for ln in lines:
            if _name_excluded(ln.product_id):
                continue
        has_sol = any(f in self.env['pos.order.line']._fields for f in ['sale_order_line_id', 'sale_line_id'])
        sale_fld = 'sale_order_line_id' if 'sale_order_line_id' in self.env['pos.order.line']._fields else 'sale_line_id'
        
        for ln in lines:
            pid = ln.product_id.id
            # Robust cost lookup chain
            cost = getattr(ln, 'line_cost', 0.0)
            cost_is_ref_uom = False
            if not cost and has_sol:
                sol = getattr(ln, sale_fld, False)
                if sol:
                    cost = getattr(sol, 'purchase_price', 0.0) or getattr(sol, 'workshop_cost', 0.0)
            
            if not cost and has_ticket:
                # Fallback to repair ticket parts cost if it's a repair service
                is_svc = any(n in (ln.product_id.name or '') for n in ['Servicio de Reparación', 'Servicio Técnico'])
                if is_svc and ln.order_id.mobile_ticket_id:
                    cost = ln.order_id.mobile_ticket_id.total_parts_cost
            
            if not cost:
                cost = ln.product_id.standard_price or 0.0
                cost_is_ref_uom = True
            
            if cost_is_ref_uom and ln.product_id.uom_id and ln.product_uom_id:
                try:
                    cost = ln.product_id.uom_id._compute_price(cost, ln.product_uom_id)
                except Exception:
                    cost = cost * (ln.product_uom_id.factor_inv or 1.0)
            
            # --- Ajuste PSM: Beneficio cero para envíos ---
            price = ln.price_unit or 0.0
            is_delivery = any(kw in (ln.product_id.name or '').lower() for kw in ['envio', 'envío', 'delivery', 'mensajeria'])
            if is_delivery:
                cost = price # Forzar margen cero
                
            profit_by_product[pid] = profit_by_product.get(pid, 0.0) + (ln.qty * (price - cost))
            qty_ref = ln.qty
            if ln.product_id.uom_id and ln.product_uom_id:
                try:
                    qty_ref = ln.product_uom_id._compute_quantity(ln.qty, ln.product_id.uom_id)
                except Exception:
                    qty_ref = ln.qty * (ln.product_uom_id.factor_inv or 1.0)
            qty_by_product[pid] = qty_by_product.get(pid, 0.0) + qty_ref
            sales_by_product[pid] = sales_by_product.get(pid, 0.0) + ln.price_subtotal_incl
        # Purga final por IDs excluidos o nombres
        if excluded_ids:
            for pid in list(profit_by_product.keys()):
                if pid in excluded_ids:
                    profit_by_product.pop(pid, None)
                    qty_by_product.pop(pid, None)
        for pid in list(profit_by_product.keys()):
            prod = self.env['product.product'].browse(pid)
            if _name_excluded(prod):
                profit_by_product.pop(pid, None)
                qty_by_product.pop(pid, None)
        top_profit_product = {'name': '', 'qty': '0', 'profit': 0.0}
        for pid, pr in sorted(profit_by_product.items(), key=lambda kv: kv[1], reverse=True):
            if excluded_ids and pid in excluded_ids:
                continue
            prod = self.env['product.product'].browse(pid)
            if _name_excluded(prod):
                continue
            uom_name = prod.uom_id.name if prod.uom_id else ''
            sales = sales_by_product.get(pid, 0.0)
            pct = (pr / sales * 100.0) if sales else 0.0
            top_profit_product = {
                'name': prod.display_name,
                'qty': f"{qty_by_product.get(pid, 0.0):g} {uom_name}",
                'profit': f"{fmt_money(pr)} ({pct:.1f}%)",
                'product_id': pid,
            }
            break
        # Salvaguarda: si el nombre aún coincide con keywords de anticipo, limpiar
        if (top_profit_product.get('name') or '') and any(kw in top_profit_product['name'].lower() for kw in kw_exclusion):
            top_profit_product = {'name': '', 'qty': '0', 'profit': 0.0}
        # top products table: name, qty, amount (ventas con impuestos para acercarse al reporte)
        # Exclusión por nombre en SQL (además de IDs)
        exclude_names_sql = ""
        exclude_names_params = []
        if kw_exclusion:
            for kw in kw_exclusion:
                exclude_names_sql += f" and lower({name_expr}) not like %s"
                if is_name_json:
                    exclude_names_params.append(user_lang)
                exclude_names_params.append(f"%{kw}%")

        # Dynamic Sorting for Top 10
        sort_by = (filters or {}).get('top_products_sort_by')
        sort_field = 'qty'
        if sort_by == 'amount':
            sort_field = 'amount'
        elif sort_by == 'profit':
            sort_field = 'profit'

        query = (
            '''select {name_expr} as product_name,
                      product_template.id as tmpl_id,
                      sum(pos_order_line.qty * COALESCE(uu.factor_inv, 1.0) / COALESCE(tuu.factor_inv, 1.0)) as qty,
                      sum(pos_order_line.price_subtotal_incl) as amount,
                      sum(pos_order_line.qty * (pos_order_line.price_unit - 
                          CASE WHEN lower(product_template.name::text) ilike '%%envio%%' 
                                 OR lower(product_template.name::text) ilike '%%envío%%'
                                 OR lower(product_template.name::text) ilike '%%delivery%%'
                               THEN pos_order_line.price_unit 
                               ELSE {cost_expr} END)) as profit
               from pos_order_line 
               inner join product_product on product_product.id=pos_order_line.product_id 
               inner join product_template on product_product.product_tmpl_id = product_template.id 
               inner join pos_order on pos_order.id = pos_order_line.order_id
               left join uom_uom uu on uu.id = pos_order_line.product_uom_id
               left join uom_uom tuu on tuu.id = product_template.uom_id
               {join_sale}
               {join_ticket}
               where {where}
               {exclude}
               {exclude_names}
               group by product_template.id, product_template.name
               order by {sort_field} desc nulls last
               limit 10'''
        ).format(where=where, name_expr=name_expr, cost_expr=cost_expr, sort_field=sort_field, join_sale=(f"left join sale_order_line sol on sol.id = pos_order_line.{sale_col}" if use_sale_id else ""), join_ticket=("left join mobile_repair_ticket mrt on mrt.id = pos_order.mobile_ticket_id" if use_ticket_id else ""), exclude=('and product_product.id not in %s' if excluded_ids else ''), exclude_names=exclude_names_sql)
        
        exec_params = ([user_lang] if is_name_json else []) + params + ([tuple(excluded_ids)] if excluded_ids else []) + exclude_names_params
        self._cr.execute(query, tuple(exec_params))
        top_products_rows = self._cr.dictfetchall()
        currency_code = self.env.company.currency_id.name
        tmpl_ids = [int(r.get('tmpl_id')) for r in top_products_rows if r.get('tmpl_id')]
        templates_by_id = {t.id: t for t in self.env['product.template'].sudo().browse(tmpl_ids)}
        top_products = []
        for r in top_products_rows:
            profit = r.get('profit') or 0.0
            amount = r.get('amount') or 0.0
            pct = (profit / amount * 100.0) if amount else 0.0
            top_products.append({
                'name': r.get('product_name') or '',
                'qty': r.get('qty') or 0.0,
                'uom_name': templates_by_id.get(int(r.get('tmpl_id'))).uom_id.name if r.get('tmpl_id') and templates_by_id.get(int(r.get('tmpl_id'))) and templates_by_id.get(int(r.get('tmpl_id'))).uom_id else '',
                'amount': fmt_money(amount),
                'amount_raw': float(amount),
                'profit': f"{fmt_money(profit)} ({pct:.1f}%)",
                'profit_raw': float(profit),
                'image_url': f"/web/image/product.template/{int(r.get('tmpl_id'))}/image_128" if r.get('tmpl_id') else '',
            })
        return {
            'payment_details': payments,
            'salesperson': total_sales,
            # compat: antes se usaba 'selling_product'; ahora también exponemos 'sessions'
            'selling_product': sessions_list,
            'sessions': sessions_list,
            'cash_in': fmt_money(cash_in),
            'cash_out': fmt_money(cash_out),
            'expected_close': fmt_money(cash_method_total - cash_out),
            'cash_in_details': cash_in_details,
            'cash_out_details': cash_out_details,
            'payment_details_breakdown': payment_details_breakdown,
            'top_profit_product': {
                'name': top_profit_product['name'],
                'qty': top_profit_product['qty'],
                'profit': top_profit_product['profit'] if isinstance(top_profit_product['profit'], str) else fmt_money(top_profit_product['profit']),
                'product_id': top_profit_product.get('product_id') if isinstance(top_profit_product, dict) else None,
                'image_url': (f"/web/image/product.product/{top_profit_product.get('product_id')}/image_128" if isinstance(top_profit_product, dict) and top_profit_product.get('product_id') else ''),
            },
            'top_products': top_products,
        }

    @api.model
    def get_refund_details(self, filters=None):
        """ Function to get summary metrics with optional filters """
        allowed_companies = self.env.companies.ids or [self.env.company.id]
        domain = [('company_id', 'in', allowed_companies)]
        start_dt, end_dt, pos_ids, session_ids = self._extract_filters(filters)
        if session_ids:
            # En pos.order
            domain.append(('session_id', 'in', session_ids))
        else:
            if start_dt:
                domain.append(('date_order', '>=', start_dt))
            if end_dt:
                domain.append(('date_order', '<=', end_dt))
        if pos_ids:
            domain.append(('config_id', 'in', pos_ids))
        orders = self.env['pos.order'].search(domain)

        currency = self.env.company.currency_id
        def fmt(amt):
            s = f"{abs(amt):,.2f}"
            code = currency.name or ''
            return f"{code} {s}"
        # Exclusión de productos (configurable)
        ICP = self.env['ir.config_parameter'].sudo()
        advance_pid_param = ICP.get_param('dashboard_pos.advance_product_id')
        advance_tmpl_param = ICP.get_param('dashboard_pos.advance_product_tmpl_id')
        excluded_param = ICP.get_param('dashboard_pos.excluded_product_ids')
        excluded_ids = set()
        try:
            if advance_pid_param:
                excluded_ids.add(int(advance_pid_param))
        except Exception:
            pass
        try:
            if advance_tmpl_param:
                tmpl_id = int(advance_tmpl_param)
                if tmpl_id:
                    variants = self.env['product.product'].search([('product_tmpl_id', '=', tmpl_id)]).ids
                    excluded_ids.update(variants)
        except Exception:
            pass
        if excluded_param:
            for tok in str(excluded_param).replace(';', ',').split(','):
                tok = tok.strip()
                if tok.isdigit():
                    excluded_ids.add(int(tok))
        if not excluded_ids:
            keywords = ['anticipo', 'advance', 'down payment', 'deposito', 'depósito', 'adelanto', 'pdv']
            dom_names = ['|'] * (len(keywords) - 1)
            for kw in keywords:
                dom_names += [('name', 'ilike', kw)]
            tmpl_candidates = self.env['product.template'].search(dom_names) if keywords else self.env['product.template']
            if tmpl_candidates:
                variant_ids = self.env['product.product'].search([('product_tmpl_id', 'in', tmpl_candidates.ids)]).ids
                excluded_ids.update(variant_ids)
            dom_disp = ['|'] * (len(keywords) - 1)
            for kw in keywords:
                dom_disp += [('display_name', 'ilike', kw)]
            prod_candidates = self.env['product.product'].search(dom_disp)
            excluded_ids.update(prod_candidates.ids)

        total_orders = len(orders)
        total_sales_amount = sum(o.amount_total for o in orders if o.amount_total > 0)
        total_tax = sum(o.amount_tax for o in orders)
        refund_orders = orders.filtered(lambda o: o.amount_total < 0)
        refund_count = len(refund_orders)
        refund_total_amount = sum(-o.amount_total for o in refund_orders)

        lines = orders.mapped('lines') if hasattr(orders, 'lines') else self.env['pos.order.line']
        # Nombre y IDs
        kw_exclusion = ['anticipo', 'advance', 'down payment', 'deposito', 'depósito', 'adelanto', 'pdv']
        def _name_excluded(prod):
            s = f"{prod.display_name or ''} {getattr(prod.product_tmpl_id, 'name', '')}".lower()
            return any(kw in s for kw in kw_exclusion)
        if excluded_ids:
            lines = lines.filtered(lambda l: l.product_id.id not in excluded_ids and not _name_excluded(l.product_id))
        else:
            lines = lines.filtered(lambda l: not _name_excluded(l.product_id))
        total_discount = 0.0
        total_profit = 0.0
        has_sol = any(f in self.env['pos.order.line']._fields for f in ['sale_order_line_id', 'sale_line_id'])
        sale_fld = 'sale_order_line_id' if 'sale_order_line_id' in self.env['pos.order.line']._fields else 'sale_line_id'
        has_ticket = 'mobile_ticket_id' in self.env['pos.order']._fields
        
        for l in lines:
            total_discount += (l.price_unit * l.qty * (l.discount or 0.0) / 100.0)
            total_discount += getattr(l, 'price_extra', 0.0)
            cost = getattr(l, 'line_cost', 0.0)
            cost_is_ref_uom = False
            if not cost and has_sol:
                sol = getattr(l, sale_fld, False)
                if sol:
                    cost = getattr(sol, 'purchase_price', 0.0) or getattr(sol, 'workshop_cost', 0.0)
            
            if not cost and has_ticket and l.order_id.mobile_ticket_id:
                is_svc = any(n in (l.product_id.name or '') for n in ['Servicio de Reparación', 'Servicio Técnico'])
                if is_svc:
                    cost = l.order_id.mobile_ticket_id.total_parts_cost
            
            if not cost:
                cost = l.product_id.standard_price or 0.0
                cost_is_ref_uom = True
            
            if cost_is_ref_uom and l.product_id.uom_id and l.product_uom_id:
                try:
                    cost = l.product_id.uom_id._compute_price(cost, l.product_uom_id)
                except Exception:
                    cost = cost * (l.product_uom_id.factor_inv or 1.0)
            
            # --- Ajuste PSM: Beneficio cero para envíos ---
            price = l.price_unit or 0.0
            is_delivery = any(kw in (l.product_id.name or '').lower() for kw in ['envio', 'envío', 'delivery', 'mensajeria'])
            if is_delivery:
                cost = price

            # Alineado a pos_rnc_report: profit = qty * (price_unit - cost unit)
            total_profit += l.qty * (price - cost)

        # Closing total as sum of payments in the period and POS selection
        payment_domain = [('pos_order_id', 'in', orders.ids)]
        payments = self.env['pos.payment'].search(payment_domain)
        closing_total = sum(p.amount for p in payments)

        session_domain = [('company_id', 'in', allowed_companies)]
        if pos_ids:
            session_domain.append(('config_id', 'in', pos_ids))
        if session_ids:
            session_domain.append(('id', 'in', session_ids))
        pos_session = self.env['pos.session'].search(session_domain)
        total_session = len(pos_session)

        # Tendencias vs ayer (mismo POS y 1 día anterior al inicio)
        y_start = (start_dt or datetime.utcnow()).replace(hour=0, minute=0, second=0, microsecond=0)
        y_start = y_start - timedelta(days=1)
        y_end = y_start.replace(hour=23, minute=59, second=59)
        y_domain = [('company_id', 'in', allowed_companies), ('date_order', '>=', y_start), ('date_order', '<=', y_end)]
        if pos_ids:
            y_domain.append(('config_id', 'in', pos_ids))
        if session_ids:
            # En pos.order
            y_domain.append(('session_id', 'in', session_ids))
        y_orders = self.env['pos.order'].search(y_domain)
        y_sales = sum(o.amount_total for o in y_orders if o.amount_total > 0)
        y_lines = y_orders.mapped('lines')
        y_profit = 0.0
        for l in y_lines:
            cost = getattr(l, 'line_cost', 0.0)
            cost_is_ref_uom = False
            if not cost and has_sol:
                sol = getattr(l, sale_fld, False)
                if sol:
                    cost = getattr(sol, 'purchase_price', 0.0) or getattr(sol, 'workshop_cost', 0.0)
            if not cost and has_ticket and l.order_id.mobile_ticket_id:
                is_svc = any(n in (l.product_id.name or '') for n in ['Servicio de Reparación', 'Servicio Técnico'])
                if is_svc:
                    cost = l.order_id.mobile_ticket_id.total_parts_cost
            if not cost:
                cost = l.product_id.standard_price or 0.0
                cost_is_ref_uom = True
                
            if cost_is_ref_uom and l.product_id.uom_id and l.product_uom_id:
                try:
                    cost = l.product_id.uom_id._compute_price(cost, l.product_uom_id)
                except Exception:
                    cost = cost * (l.product_uom_id.factor_inv or 1.0)
                
            y_profit += l.qty * ((l.price_unit or 0.0) - cost)
        def pct(curr, prev):
            try:
                return 0.0 if not prev else ((curr - prev) / prev) * 100.0
            except Exception:
                return 0.0
        sale_trend_pct = pct(total_sales_amount, y_sales)
        profit_trend_pct = pct(total_profit, y_profit)
        orders_trend_pct = pct(total_orders, len(y_orders))
        pct_margin = (total_profit / total_sales_amount * 100.0) if total_sales_amount else 0.0
        profit_signed = f"{currency.name or ''} {total_profit:,.2f} ({pct_margin:.1f}%)"
        return {
            'total_sale': fmt(total_sales_amount),
            'total_order_count': total_orders,
            'total_refund_count': refund_count,
            'total_session': total_session,
            'today_refund_total': fmt(refund_total_amount),
            'today_sale': total_orders,
            'tax_total': fmt(total_tax),
            'discount_total': fmt(total_discount),
            'profit_total': profit_signed,
            'closing_total': fmt(closing_total),
            'avg_ticket': fmt(total_sales_amount / total_orders if total_orders else 0.0),
            'trend': {
                'sales_pct': sale_trend_pct,
                'profit_pct': profit_trend_pct,
                'orders_pct': orders_trend_pct,
            }
        }

    @api.model
    def get_the_top_customer(self, filters=None):
        """ To get the top Customer details with optional filters"""
        where, params = self._build_where_clause(filters)
        query = (
            '''select res_partner.name as customer,pos_order.partner_id,sum(pos_order.amount_paid) as amount_total from pos_order 
               inner join res_partner on res_partner.id = pos_order.partner_id where {where}
               GROUP BY pos_order.partner_id, res_partner.name  ORDER BY amount_total  DESC LIMIT 10;'''
        ).format(where=where)
        self._cr.execute(query, tuple(params))
        docs = self._cr.dictfetchall()

        order = []
        for record in docs:
            order.append(record.get('amount_total'))
        day = []
        for record in docs:
            day.append(record.get('customer'))
        final = [order, day]
        return final

    @api.model
    def get_the_top_products(self, filters=None):
        """ Function to get the top products with optional filters"""
        where, params = self._build_where_clause(filters)
        user_lang = self.env.user.lang or 'en_US'
        query = (
            '''select DISTINCT(product_template.name)->>%s as product_name,
                      sum(pos_order_line.qty * COALESCE(uu.factor_inv, 1.0) / COALESCE(tuu.factor_inv, 1.0)) as total_quantity 
               from pos_order_line 
               inner join product_product on product_product.id=pos_order_line.product_id 
               inner join product_template on product_product.product_tmpl_id = product_template.id 
               inner join pos_order on pos_order.id = pos_order_line.order_id
               left join uom_uom uu on uu.id = pos_order_line.product_uom_id
               left join uom_uom tuu on tuu.id = product_template.uom_id
               where {where} group by product_template.id, product_template.name ORDER 
               BY total_quantity DESC Limit 10 '''
        ).format(where=where)
        self._cr.execute(query, tuple([user_lang] + params))
        top_product = self._cr.dictfetchall()
        total_quantity = []
        for record in top_product:
            total_quantity.append(record.get('total_quantity'))
        product_name = []
        for record in top_product:
            product_name.append(record.get('product_name'))
        final = [total_quantity, product_name]
        return final

    @api.model
    def get_the_top_categories(self, filters=None):
        """ Function to get the top Product categories with optional filters"""
        where, params = self._build_where_clause(filters)
        query = (
            '''select DISTINCT(product_category.complete_name) as product_category,
                      sum(pos_order_line.qty * COALESCE(uu.factor_inv, 1.0) / COALESCE(tuu.factor_inv, 1.0)) as total_quantity 
               from pos_order_line 
               inner join product_product on product_product.id=pos_order_line.product_id  
               inner join product_template on product_product.product_tmpl_id = product_template.id 
               inner join product_category on product_category.id =product_template.categ_id 
               inner join pos_order on pos_order.id = pos_order_line.order_id
               left join uom_uom uu on uu.id = pos_order_line.product_uom_id
               left join uom_uom tuu on tuu.id = product_template.uom_id
               where {where} group by product_category.id, product_category.complete_name ORDER BY total_quantity DESC '''
        ).format(where=where)
        self._cr.execute(query, tuple(params))
        top_product = self._cr.dictfetchall()
        total_quantity = []
        for record in top_product:
            total_quantity.append(record.get('total_quantity'))
        product_categ = []
        for record in top_product:
            product_categ.append(record.get('product_category'))
        final = [total_quantity, product_categ]
        return final

    @api.model
    def get_pos_configs(self):
        allowed_companies = self.env.companies.ids or [self.env.company.id]
        configs = self.env['pos.config'].search([('company_id', 'in', allowed_companies)])
        return [{'id': cfg.id, 'name': cfg.name} for cfg in configs]

    @api.model
    def get_categories(self):
        """ Get all active product categories for filters """
        # Use product.category (matches pc alias in get_detailed_sales query)
        categories = self.env['product.category'].search_read([], ['id', 'name'], order='name asc')
        return categories

    @api.model
    def get_detailed_sales(self, filters=None, search_term=None, category_ids=None, view_mode=None):
        """ Get aggregated sales metrics grouped by Category > Product (Universal Compatibility) """
        user_lang = self.env.user.lang or 'en_US'
        where, params = self._build_where_clause(filters)
        
        # 1. Determine Product Name Field (JSONB vs Char)
        # Odoo 16/17+ with jsonb translations: name is a logic field backed by JSON column?
        # Actually in SQL: 
        # - Old Odoo: pt.name is VARCHAR (translated via ir_translation)
        # - New Odoo (17+): pt.name is JSONB
        # Safe interaction: Use COALESCE or try to detect.
        # Detection via IR Model Fields:
        pt_name_field = self.env['ir.model.fields'].search([('model', '=', 'product.template'), ('name', '=', 'name')], limit=1)
        is_name_json = pt_name_field.ttype == 'json' or pt_name_field.ttype == 'jsonb'
        
        if is_name_json:
            name_expr = "(pt.name ->> %s)"
            search_name_expr = "(pt.name ->> %s)"
            # Param needed for name extraction
            name_params = [user_lang]
        else:
            # Standard Char/Text field (Postgres handles casts, but better be safe)
            # If using ir_translation, Odoo handles it in ORM but in SQL we see the raw value (often English/Source).
            # For simplicity in pure SQL on old versions without joining ir_translation, we accept raw name.
            # Ideally utilize `COALESCE(t.value, pt.name)` but that requires joining ir_translation.
            # For now, let's use the raw column.
            name_expr = "pt.name"
            search_name_expr = "pt.name"
            name_params = [] # No lang param needed for raw char column

        # Use unified cost expression for detailed sales
        # Names of aliases must match the query: po, pol, pp, pt
        cost_expr = self._get_dashboard_cost_expr('po', 'pol', 'pp', 'pt')

        # Now for Name
        self.env.cr.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'product_template' AND column_name = 'name'")
        res_name = self.env.cr.fetchone()
        is_name_json = res_name and res_name[0] == 'jsonb'

        if is_name_json:
            name_sel_expr = "(pt.name ->> %s)"
            name_where_expr = "(pt.name ->> %s)"
            # We must prepend user_lang to params IF we use this expr.
            # But wait, search_term params are distinct from SELECT params.
        else:
            name_sel_expr = "pt.name"
            name_where_expr = "pt.name"

        # Construct Params
        # Search Term
        if search_term:
            if is_name_json:
                 # We need lang for the name extraction in WHERE
                 where += " AND (" + name_where_expr + " ILIKE %s OR pc.name ILIKE %s)"
                 params = [user_lang, f"%{search_term}%", f"%{search_term}%"] + params 
                 # Note: self._build_where_clause returns params. We need to be careful with order.
                 # Let's rebuild params.
                 # Actually, simpler to just append and use indexed params? No, %s is positional.
                 # Let's handle params carefully.
                 pass
            else:
                 where += " AND (" + name_where_expr + " ILIKE %s OR pc.name ILIKE %s)"
                 # No lang param
                 pass

        # Adjust params list for search term
        # _build_where_clause(filters) returns [start_date, end_date...] likely.
        # We need to insert search params at the end of WHERE clause params.
        
        # Let's rewrite param logic for clarity
        base_where, base_params = self._build_where_clause(filters)
        query_params = list(base_params) # Copy
        
        if search_term:
            if is_name_json:
                where_clause = f" AND ({name_where_expr} ILIKE %s OR pc.name ILIKE %s)"
                query_params.extend([user_lang, f"%{search_term}%", f"%{search_term}%"])
            else:
                where_clause = f" AND ({name_where_expr} ILIKE %s OR pc.name ILIKE %s)"
                query_params.extend([f"%{search_term}%", f"%{search_term}%"])
            base_where += where_clause

        # Category Filter
        if category_ids:
            if isinstance(category_ids, (list, tuple)) and len(category_ids) > 0:
                base_where += " AND pc.id IN %s"
                query_params.append(tuple(category_ids))

        base_where += " AND pos_order.amount_total > 0"

        # Fix alias
        where_po = base_where.replace('pos_order.', 'po.')
        
        currency = self.env.company.currency_id

        # Query 1: Category Summary
        # Does NOT use product name, only joins.
        # Cost expr is used.
        cat_query = (
            f"""
            SELECT 
                pc.id as category_id,
                pc.name as category,
                sum(pol.qty * COALESCE(uu.factor_inv, 1.0) / COALESCE(tuu.factor_inv, 1.0)) as qty,
                sum(pol.price_subtotal_incl) as total,
                sum(pol.price_subtotal_incl - (pol.qty * 
                    CASE WHEN lower(pt.name::text) ilike '%%envio%%' 
                           OR lower(pt.name::text) ilike '%%envío%%'
                           OR lower(pt.name::text) ilike '%%delivery%%'
                         THEN pol.price_unit 
                         ELSE {cost_expr} END)) as profit
            FROM pos_order_line pol
            JOIN pos_order po ON po.id = pol.order_id
            JOIN product_product pp ON pp.id = pol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            LEFT JOIN product_category pc ON pc.id = pt.categ_id
            LEFT JOIN uom_uom uu ON uu.id = pol.product_uom_id
            LEFT JOIN uom_uom tuu ON tuu.id = pt.uom_id
            WHERE {{where}}
            GROUP BY pc.id, pc.name
            ORDER BY total DESC
            """
        ).format(where=where_po)
        
        self.env.cr.execute(cat_query, tuple(query_params))
        cat_results = self.env.cr.dictfetchall()
        
        category_summary = []
        for r in cat_results:
            profit = r.get('profit') or 0.0
            total = r.get('total') or 0.0
            category_summary.append({
                'category_id': r.get('category_id'),
                'category': r.get('category') or 'Sin Categoría',
                'qty': f"{r.get('qty') or 0.0:g}",
                'total': total,
                'total_str': f"{currency.name} {total:,.2f}",
                'profit': profit,
                'profit_str': f"{currency.name} {profit:,.2f}",
            })

        # Query 2: Products or Real Time Feed
        # USES product name (dynamic sel_expr)
        
        prod_sel_params = []
        if is_name_json:
            prod_sel_params = [user_lang]
        
        # 3. Dynamic Messenger & Salesperson Support
        use_messenger = self._is_mod_active('pos_messenger_manager', 'dashboard_pos.enable_messenger')
        
        messenger_select = ""
        messenger_join = ""
        if use_messenger:
            messenger_select = ", mup.name as messenger_name, po.delivery_status"
            messenger_join = """
                LEFT JOIN res_users mu ON mu.id = po.messenger_id
                LEFT JOIN res_partner mup ON mup.id = mu.partner_id
            """

        # Determine mode
        if view_mode:
            is_realtime = (view_mode == 'realtime')
        else:
            is_realtime = not category_ids
        
        if is_realtime:
            # Real Time Feed (Individual Lines)
            # Combine params: [Select Params] + [Where Params]
            final_prod_params = prod_sel_params + query_params
            
            feed_query = f"""
                SELECT 
                    pol.id as line_id,
                    po.id as order_id,
                    po.date_order,
                    po.name as order_name,
                    pc.id as category_id,
                    pc.name as category,
                    {name_sel_expr} as product_name,
                    pt.id as tmpl_id,
                    pp.id as product_id,
                    pol.qty as qty,
                    pol.price_subtotal_incl as total,
                    (pol.price_subtotal_incl - (pol.qty * 
                        CASE WHEN lower(pt.name::text) ilike '%%envio%%' 
                               OR lower(pt.name::text) ilike '%%envío%%'
                               OR lower(pt.name::text) ilike '%%delivery%%'
                             THEN pol.price_unit 
                             ELSE {cost_expr} END)) as profit,
                    COALESCE(sup.name, rup.name, '') as salesperson,
                    COALESCE(sup.id, rup.id) as salesperson_partner_id,
                    pa.name as partner_name,
                    pa.comment as partner_comment
                    {messenger_select}
                FROM pos_order_line pol
                JOIN pos_order po ON po.id = pol.order_id
                JOIN product_product pp ON pp.id = pol.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN res_users su ON su.id = po.salesman_id
                LEFT JOIN res_partner sup ON sup.id = su.partner_id
                LEFT JOIN res_users ru ON ru.id = po.user_id
                LEFT JOIN res_partner rup ON rup.id = ru.partner_id
                LEFT JOIN res_partner pa ON pa.id = po.partner_id
                LEFT JOIN uom_uom uu ON uu.id = pol.product_uom_id
                {messenger_join}
                WHERE {where_po}
                ORDER BY po.date_order DESC
                """

            self.env.cr.execute(feed_query, tuple(final_prod_params))
            feed_results = self.env.cr.dictfetchall()
            
            # Prefetch lines
            line_ids = [r.get('line_id') for r in feed_results if r.get('line_id')]
            lines_by_id = {l.id: l for l in self.env['pos.order.line'].sudo().browse(line_ids)}
            
            products = []
            user_tz = self.env.user.tz or 'UTC'
            tz = pytz.timezone(user_tz)
            
            for r in feed_results:
                profit = r.get('profit') or 0.0
                total = r.get('total') or 0.0
                
                ln = lines_by_id.get(r.get('line_id'))
                uom_name = ln.product_uom_id.name if ln and ln.product_uom_id else ''
                
                utc_dt = r.get('date_order')
                if utc_dt:
                    local_dt = pytz.utc.localize(utc_dt).astimezone(tz)
                    time_str = local_dt.strftime("%I:%M %p")
                    weekday = local_dt.strftime("%A")
                    
                    days_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    days_es = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                    try:
                        idx = days_en.index(weekday)
                        weekday = days_es[idx]
                    except:
                        pass
                        
                    formatted_time = f"Hora {time_str} {weekday}"
                else:
                    formatted_time = ""

                pct = (profit / total * 100.0) if total else 0.0
                products.append({
                    'line_id': r.get('line_id'),
                    'order_id': r.get('order_id'),
                    'date_order': r.get('date_order'),
                    'formatted_time': formatted_time,
                    'order_name': r.get('order_name'),
                    'salesperson': r.get('salesperson') or '',
                    'salesperson_image_url': f"/web/image/res.partner/{r['salesperson_partner_id']}/image_128" if r.get('salesperson_partner_id') else '',
                    'category_id': r.get('category_id'),
                    'category': r.get('category') or 'Sin Categoría',
                    'partner_name': r.get('partner_name') or '',
                    'partner_comment': r.get('partner_comment') or '',
                    'product': r.get('product_name') or 'Unknown',
                    'uom_name': uom_name,
                    'image_url': f"/web/image/product.template/{r['tmpl_id']}/image_128" if r.get('tmpl_id') else '',
                    'order_count': 1,
                    'qty': r.get('qty') or 0,
                    'total': total,
                    'total_str': f"{currency.name} {total:,.2f}",
                    'profit': profit,
                    'profit_str': f"{currency.name} {profit:,.2f} ({pct:.1f}%)",
                    'messenger': r.get('messenger_name') or '',
                    'delivery_status': r.get('delivery_status') or 'none',
                })
        
        else:
            final_prod_params = prod_sel_params + query_params
            
            prod_query = f"""
                SELECT 
                    pc.id as category_id,
                    pc.name as category,
                    {name_sel_expr} as product_name,
                    pt.id as tmpl_id,
                    pp.id as product_id,
                    pol.product_uom_id as uom_id,
                    count(DISTINCT po.id) as order_count,
                    sum(pol.qty) as qty,
                    sum(pol.price_subtotal_incl) as total,
                    sum(pol.qty * (pol.price_unit - 
                        CASE WHEN lower(pt.name::text) ilike '%%envio%%' 
                               OR lower(pt.name::text) ilike '%%envío%%'
                               OR lower(pt.name::text) ilike '%%delivery%%'
                             THEN pol.price_unit 
                             ELSE {cost_expr} END)) as profit
                FROM pos_order_line pol
                JOIN pos_order po ON po.id = pol.order_id
                JOIN product_product pp ON pp.id = pol.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                LEFT JOIN uom_uom uu ON uu.id = pol.product_uom_id
                WHERE {where_po}
                GROUP BY pc.id, pc.name, pt.name, pt.id, pp.id, pol.product_uom_id
                ORDER BY total DESC
                """
            
            self.env.cr.execute(prod_query, tuple(final_prod_params))
            prod_results = self.env.cr.dictfetchall()
            
            # Prefetch products & UoMs
            product_ids = [r.get('product_id') for r in prod_results if r.get('product_id')]
            products_by_id = {p.id: p for p in self.env['product.product'].sudo().browse(product_ids)}
            uom_ids = [r.get('uom_id') for r in prod_results if r.get('uom_id')]
            uoms_by_id = {u.id: u for u in self.env['uom.uom'].sudo().browse(uom_ids)}
            
            products = []
            for r in prod_results:
                profit = r.get('profit') or 0.0
                total = r.get('total') or 0.0
                
                prod = products_by_id.get(r.get('product_id'))
                uom = uoms_by_id.get(r.get('uom_id'))
                uom_name = uom.name if uom else (prod.uom_id.name if prod and prod.uom_id else '')
                
                pct = (profit / total * 100.0) if total else 0.0
                products.append({
                    'category_id': r.get('category_id'),
                    'category': r.get('category') or 'Sin Categoría',
                    'product_id': r.get('product_id'),
                    'product': r.get('product_name') or 'Unknown',
                    'uom_id': r.get('uom_id'),
                    'uom_name': uom_name,
                    'image_url': f"/web/image/product.template/{r['tmpl_id']}/image_128" if r.get('tmpl_id') else '',
                    'order_count': r.get('order_count') or 0,
                    'qty': r.get('qty') or 0,
                    'total': total,
                    'total_str': f"{currency.name} {total:,.2f}",
                    'profit': profit,
                    'profit_str': f"{currency.name} {profit:,.2f} ({pct:.1f}%)",
                })
            
        return {
            'view_mode': 'realtime' if is_realtime else 'aggregated',
            'category_summary': category_summary,
            'products': products,
        }


class PosSession(models.Model):
    _inherit = 'pos.session'

    def dashboard_close_session(self):
        """Cerrar sesiones POS desde el dashboard.

        - Si la sesión está en opening_control u opened, pasar a closing_control.
        - Si está en closing_control, llamar al cierre definitivo.
        """
        for session in self:
            if session.state in ('opening_control', 'opened'):
                session.action_pos_session_closing_control()
            if session.state == 'closing_control':
                session.action_pos_session_close()
        return True
