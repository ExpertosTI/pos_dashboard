/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
const actionRegistry = registry.category("actions");

function getLocalISODate(date) {
  const d = date || new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function isDesktopLayout() {
  if (typeof window === 'undefined' || !window.matchMedia) {
    return true;
  }
  return window.matchMedia('(min-width: 992px)').matches;
}

// Paleta suficiente para hasta 15 segmentos en cualquier gráfica
const CHART_COLORS = [
  '#ef4444','#3b82f6','#10b981','#f59e0b','#8b5cf6',
  '#06b6d4','#f97316','#84cc16','#ec4899','#64748b',
  '#0ea5e9','#a855f7','#22c55e','#eab308','#14b8a6',
];
function chartColors(n) {
  const cols = [];
  for (let i = 0; i < n; i++) cols.push(CHART_COLORS[i % CHART_COLORS.length]);
  return cols;
}

export class PosDashboard extends Component {
  //Initializes the PosDashboard component,
  setup() {
    super.setup(...arguments);
    this.orm = useService('orm')
    this.user = user;
    this.actionService = useService("action");
    this.startDateRef = useRef('start_date');
    this.endDateRef = useRef('end_date');
    this.startTimeRef = useRef('start_time');
    this.endTimeRef = useRef('end_time');
    this.posSelectRef = useRef('pos_select');
    this.posChecksRef = useRef('pos_checks');
    this.sessionSelectRef = useRef('session_select');
    this.refreshHandle = null;
    this.state = useState({
      payment_details: [],
      top_salesperson: [],
      selling_product: [],
      total_sale: [],
      total_order_count: [],
      total_refund_count: [],
      total_session: [],
      today_refund_total: [],
      today_sale: [],
      pos_configs: [],
      sessions: [],
      tax_total: [],
      discount_total: [],
      profit_total: [],
      closing_total: [],
      avg_ticket: '',
      cash_in: '',
      cash_out: '',
      expected_close: '',
      top_products: [],
      top_profit_product: { name: '', qty: 0, profit: '' },
      trend: { sales_pct: 0, profit_pct: 0, orders_pct: 0 },
      expandTopProducts: false,
      expandCashIn: false,
      expandCashOut: false,
      expandedPaymentMethod: null,
      cash_in_details: [],
      cash_out_details: [],
      payment_details_breakdown: {},
      filters: {
        start_date: null,
        end_date: null,
        start_time: null,
        end_time: null,
        session_ids: [],
        top_products_sort_by: 'qty', // Initial sort
      },
      currentTab: 'cuadres',
      salesSearchTerm: '',
      detailed_sales: [],
      category_summary: [],
      categories: [],
      selectedCategories: [],
      view_mode: 'aggregated',
      recentMonths: this._getRecentMonths(),
      activeDateRange: 'today',
    });
    // When the component is about to start, fetch data in tiles
    onWillStart(async () => {
      const today = new Date();
      const iso = getLocalISODate(today);
      this.state.filters.start_date = iso;
      this.state.filters.end_date = iso;
      await this.load_pos_configs();
      await this.fetch_data();
    });
    //When the component is mounted, render various charts
    onMounted(async () => {
      const today = new Date();
      const iso = getLocalISODate(today);
      if (this.startDateRef.el && !this.startDateRef.el.value) { this.startDateRef.el.value = iso; }
      if (this.endDateRef.el && !this.endDateRef.el.value) { this.endDateRef.el.value = iso; }
      if (this.startTimeRef.el && !this.startTimeRef.el.value) { this.startTimeRef.el.value = "00:00"; }
      if (this.endTimeRef.el && !this.endTimeRef.el.value) { this.endTimeRef.el.value = "23:59"; }
      // marcar POS todos seleccionados en el DOM
      if (this.posSelectRef.el && this.state.pos_configs.length) {
        const set = new Set(this.state.filters.pos_ids || [])
        Array.from(this.posSelectRef.el.options).forEach(opt => { opt.selected = set.has(Number(opt.value)); })
      }
      const chipsEl = this.posChecksRef.el;
      if (chipsEl && isDesktopLayout()) {
        const set = new Set(this.state.filters.pos_ids || [])
        chipsEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
          const id = Number(cb.getAttribute('data-pos') || cb.dataset.pos || cb.value)
          cb.checked = set.has(id)
        })
      }
      if (this.sessionSelectRef.el) {
        const sessIds = this.state.filters.session_ids || [];
        this.sessionSelectRef.el.value = (sessIds.length ? String(sessIds[0]) : "");
      }
      await this.render_top_customer_graph();
      await this.render_top_product_graph();
      await this.render_product_category_graph();
      await this.render_salesperson_graph(); // NEW
      await this.onclick_pos_sales();
      await this.applyFilters();
      this.refreshHandle = setInterval(() => { this.applyFilters(); }, 15000);
    });
    onWillUnmount(() => { if (this.refreshHandle) { clearInterval(this.refreshHandle); this.refreshHandle = null; } });
  }

  // NEW: Quick Filter Logic
  async setDateRange(range) {
    const today = new Date();
    let start = new Date(today);
    let end = new Date(today);

    if (range === 'today') {
      // already set
    } else if (range === 'yesterday') {
      start.setDate(today.getDate() - 1);
      end.setDate(today.getDate() - 1);
    } else if (range === 'this_week') {
      // Monday of current week
      const day = today.getDay() || 7; 
      start.setDate(today.getDate() - (day - 1));
      // End is Sunday or today? Usually "this week" in a dashboard shows until today.
      // But if they want a full week fixed range:
      end.setDate(start.getDate() + 6);
    } else if (range === 'last_fortnight') {
      // Last 15 days
      start.setDate(today.getDate() - 15);
    } else if (range === 'this_month') {
      start.setDate(1);
      end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (range === 'last_month') {
      start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      end = new Date(today.getFullYear(), today.getMonth(), 0);
    }

    const s_iso = getLocalISODate(start);
    const e_iso = getLocalISODate(end);

    if (this.startDateRef.el) this.startDateRef.el.value = s_iso;
    if (this.endDateRef.el) this.endDateRef.el.value = e_iso;

    this.state.activeDateRange = range;
    await this.applyFilters();
  }

  async selectMonth(ev) {
    const value = ev.target.value;
    if (!value) return;
    const [year, month] = value.split('-').map(v => parseInt(v));
    const start = new Date(year, month, 1);
    const end = new Date(year, month + 1, 0);

    if (this.startDateRef.el) this.startDateRef.el.value = getLocalISODate(start);
    if (this.endDateRef.el) this.endDateRef.el.value = getLocalISODate(end);

    await this.applyFilters();
  }

  _getRecentMonths() {
    const months = [];
    const date = new Date();
    const monthNames = [
      _t("Enero"), _t("Febrero"), _t("Marzo"), _t("Abril"),
      _t("Mayo"), _t("Junio"), _t("Julio"), _t("Agosto"),
      _t("Septiembre"), _t("Octubre"), _t("Noviembre"), _t("Diciembre")
    ];

    for (let i = 0; i < 18; i++) {
        const d = new Date(date.getFullYear(), date.getMonth() - i, 1);
        const y = d.getFullYear();
        const m = d.getMonth();
        months.push({
            id: `${y}-${m}`,
            label: `${monthNames[m]} ${y}`
        });
    }
    return months;
  }

  async load_pos_configs() {
    const configs = await this.orm.call('pos.order', 'get_pos_configs', [])
    this.state.pos_configs = configs || []
    // por defecto, todos seleccionados
    this.state.filters.pos_ids = (configs || []).map(c => c.id)
    // Fetch categories regardless of layout
    await this.fetch_categories();
  }
  async fetch_categories() {
    try {
      const cats = await this.orm.call('pos.order', 'get_categories', []);
      this.state.categories = cats || [];
    } catch (e) {
      console.error("Error fetching categories", e);
    }
  }
  getFilters() {
    const startEl = this.startDateRef.el;
    const endEl = this.endDateRef.el;
    const startTimeEl = this.startTimeRef.el;
    const endTimeEl = this.endTimeRef.el;
    const posEl = this.posSelectRef.el;
    const chipsEl = this.posChecksRef.el;
    const sessEl = this.sessionSelectRef.el;
    const start_date = startEl && startEl.value ? startEl.value : null;
    const end_date = endEl && endEl.value ? endEl.value : null;
    const start_time = startTimeEl && startTimeEl.value ? startTimeEl.value : null;
    const end_time = endTimeEl && endTimeEl.value ? endTimeEl.value : null;
    let pos_ids = [];
    let session_ids = [];
    if (chipsEl && isDesktopLayout()) {
      pos_ids = Array.from(chipsEl.querySelectorAll('input[type="checkbox"]:checked')).map(cb => Number(cb.getAttribute('data-pos') || cb.dataset.pos || cb.value));
    } else if (posEl) {
      pos_ids = Array.from(posEl.selectedOptions || []).map(o => Number(o.value));
    }
    if (sessEl && sessEl.value) {
      const v = Number(sessEl.value);
      if (!isNaN(v) && v > 0) {
        session_ids = [v];
      }
    }
    const top_products_sort_by = this.state.filters.top_products_sort_by || 'qty';
    return { start_date, end_date, start_time, end_time, pos_ids, session_ids, top_products_sort_by };
  }
  async applyFilters(ev) {
    if (ev && (ev.target === this.startDateRef.el || ev.target === this.endDateRef.el)) {
        this.state.activeDateRange = 'custom';
    }
    this.state.filters = this.getFilters();
    await this.fetch_data();
    await this.render_top_customer_graph();
    await this.render_top_product_graph();
    await this.render_product_category_graph();
    await this.render_salesperson_graph(); // Update chart
    await this.onclick_pos_sales();
    if (this.state.currentTab === 'ventas') {
      await this.fetch_sales_data();
    }
  }
  async setTab(tab) {
    this.state.currentTab = tab;
    if (tab === 'ventas') {
      await this.fetch_sales_data();
    }
  }
  async searchSales(ev) {
    this.state.salesSearchTerm = ev.target.value;
    await this.fetch_sales_data();
  }
  async fetch_sales_data() {
    const filters = this.state.filters;
    const term = this.state.salesSearchTerm;
    const catIds = this.state.selectedCategories;
    const result = await this.orm.call('pos.order', 'get_detailed_sales', [filters, term, catIds]);
    this.state.category_summary = result?.category_summary || [];
    this.state.detailed_sales = result?.products || [];
    this.state.view_mode = result?.view_mode || 'aggregated';
  }
  async toggleCategory(catId) {
    const current = this.state.selectedCategories;
    const idx = current.indexOf(catId);
    if (idx >= 0) {
      current.splice(idx, 1);
    } else {
      current.push(catId);
    }
    this.state.selectedCategories = [...current];
    await this.fetch_sales_data();
  }
  selectAllPOS() {
    const chipsEl = this.posChecksRef.el;
    const selEl = this.posSelectRef.el;
    const ids = (this.state.pos_configs || []).map(c => Number(c.id));
    if (chipsEl && isDesktopLayout()) {
      chipsEl.querySelectorAll('input[type="checkbox"]').forEach(cb => { cb.checked = true; });
    }
    if (selEl) {
      Array.from(selEl.options || []).forEach(opt => { opt.selected = true; });
    }
    this.applyFilters();
  }
  clearAllPOS() {
    const chipsEl = this.posChecksRef.el;
    const selEl = this.posSelectRef.el;
    if (chipsEl && isDesktopLayout()) {
      chipsEl.querySelectorAll('input[type="checkbox"]').forEach(cb => { cb.checked = false; });
    }
    if (selEl) {
      Array.from(selEl.options || []).forEach(opt => { opt.selected = false; });
    }
    this.applyFilters();
  }
  async fetch_data() {
    //  Function to fetch all the pos details
    const filters = this.state.filters
    var result = await this.orm.call('pos.order', 'get_refund_details', [filters])
    this.state.total_sale = result['total_sale']
    this.state.total_order_count = result['total_order_count']
    this.state.total_refund_count = result['total_refund_count']
    this.state.total_session = result['total_session']
    this.state.today_refund_total = result['today_refund_total']
    this.state.today_sale = result['today_sale']
    this.state.tax_total = result['tax_total']
    this.state.discount_total = result['discount_total']
    this.state.profit_total = result['profit_total']
    this.state.closing_total = result['closing_total']
    this.state.avg_ticket = result['avg_ticket'] || '' // New KPI
    this.state.trend = result['trend'] || { sales_pct: 0, profit_pct: 0, orders_pct: 0 }
    var data = await this.orm.call('pos.order', 'get_details', [filters])
    this.state.payment_details = data['payment_details']
    this.state.payment_details_breakdown = data['payment_details_breakdown'] || {}
    this.state.expandedPaymentMethod = null
    this.state.top_salesperson = data['salesperson'] // Now list of dicts
    this.state.selling_product = data['selling_product']
    this.state.sessions = data['sessions'] || data['selling_product'] || []
    this.state.cash_in = data['cash_in']
    this.state.cash_out = data['cash_out']
    this.state.expected_close = data['expected_close']
    this.state.top_products = data['top_products'] || []
    this.state.top_profit_product = data['top_profit_product'] || { name: '', qty: 0, profit: '' }
    this.state.cash_in_details = data['cash_in_details'] || []
    this.state.cash_out_details = data['cash_out_details'] || []
  }
  async setTopProductsSort(criteria) {
    this.state.filters.top_products_sort_by = criteria;
    await this.applyFilters();
  }
  toggleTopProducts() { this.state.expandTopProducts = !this.state.expandTopProducts }
  toggleCashIn() { this.state.expandCashIn = !this.state.expandCashIn }
  toggleCashOut() { this.state.expandCashOut = !this.state.expandCashOut }
  
  onSearchCashOut(ev) {
    if (ev) {
        ev.stopPropagation();
        ev.preventDefault();
    }
    const filters = this.state.filters;
    const domain = [['amount', '<', 0]];
    
    if (filters.start_date) {
        domain.push(['date', '>=', filters.start_date]);
    }
    if (filters.end_date) {
        domain.push(['date', '<=', filters.end_date]);
    }
    
    // Check for sessions
    if (filters.session_ids && filters.session_ids.length) {
        // In Odoo 18, we might want to filter by the specific statement lines of these sessions
        // For now, the date range is the most reliable cross-version filter for "Cash Out"
    }

    this.actionService.doAction({
        name: _t("Detalle de Salidas de Efectivo"),
        type: 'ir.actions.act_window',
        res_model: 'account.bank.statement.line',
        domain: domain,
        views: [[false, 'list'], [false, 'form']],
        view_mode: 'list,form',
        target: 'current',
        context: { 'search_default_group_by_date': 1 }
    });
  }
  togglePaymentDetails(ev) {
    const target = ev && ev.currentTarget;
    if (!target) { return; }
    const method = (target.dataset && target.dataset.method) || null;
    if (!method) { return; }
    if (this.state.expandedPaymentMethod === method) {
      this.state.expandedPaymentMethod = null;
    } else {
      this.state.expandedPaymentMethod = method;
    }
  }
  trendClass(v) {
    if (v > 0) return 'up';
    if (v < 0) return 'down';
    return 'flat';
  }
  fmtPct(v) {
    if (v === null || v === undefined) return '—';
    const n = Number(v);
    if (!isFinite(n) || Math.abs(n) < 0.0001) return '—';
    const arrow = n > 0 ? '↑' : '↓';
    return `${arrow} ${Math.abs(n).toFixed(1)}% vs. ayer`;
  }
  openOrder(orderId, e) {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    if (!orderId) {
      return;
    }
    this.actionService.doAction({
      name: _t("Orden"),
      type: 'ir.actions.act_window',
      res_model: 'pos.order',
      res_id: orderId,
      views: [[false, 'form']],
      target: 'current'
    })
  }
  pos_order_today(e) {
    //To get the details of today's order
    var self = this;
    var date = new Date();
    var yesterday = new Date(date.getTime());
    yesterday.setDate(date.getDate() - 1);
    e.stopPropagation();
    e.preventDefault();
    this.user.hasGroup('hr.group_hr_user').then(function (has_group) {
      if (has_group) {
        var options = {
          on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
        self.actionService.doAction({
          name: _t("Órdenes de Hoy"),
          type: 'ir.actions.act_window',
          res_model: 'pos.order',
          view_mode: 'tree,form,calendar',
          view_type: 'form',
          views: [[false, 'list'], [false, 'form']],
          domain: [['date_order', '<=', date], ['date_order', '>=', yesterday]],
          target: 'current'
        }, options)
      }
    });
  }
  async closeSelectedSession(e) {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    const sessEl = this.sessionSelectRef.el;
    const val = sessEl && sessEl.value ? Number(sessEl.value) : 0;
    if (!val) {
      if (typeof window !== 'undefined') {
        window.alert(_t("Seleccione una sesión POS para cerrar."));
      }
      return;
    }
    const sessions = this.state.sessions || [];
    const sess = sessions.find(s => Number(s.id) === val);
    if (!sess) {
      return;
    }
    const st = sess.state || '';
    if (st === 'closed') {
      if (typeof window !== 'undefined') {
        window.alert(_t("La sesión seleccionada ya está cerrada."));
      }
      return;
    }
    if (typeof window !== 'undefined') {
      const ok = window.confirm(_t("¿Desea cerrar la sesión seleccionada?"));
      if (!ok) {
        return;
      }
    }
    try {
      await this.orm.call('pos.session', 'dashboard_close_session', [[val]]);
    } catch (err) {
      console.error(err);
      if (typeof window !== 'undefined') {
        window.alert(_t("No se pudo cerrar la sesión POS."));
      }
      return;
    }
    await this.applyFilters();
  }
  pos_refund_orders(e) {
    //   To get the details of refund orders
    var self = this;
    var date = new Date();
    var yesterday = new Date(date.getTime());
    yesterday.setDate(date.getDate() - 1);
    e.stopPropagation();
    e.preventDefault();
    this.user.hasGroup('hr.group_hr_user').then(function (has_group) {
      if (has_group) {
        var options = {
          on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
        self.actionService.doAction({
          name: _t("Órdenes Reembolsadas"),
          type: 'ir.actions.act_window',
          res_model: 'pos.order',
          view_mode: 'tree,form,calendar',
          view_type: 'form',
          views: [[false, 'list'], [false, 'form']],
          domain: [['amount_total', '<', 0.0]],
          target: 'current'
        }, options)
      }
    });
  }
  pos_refund_today_orders(e) {
    //  To get the details of today's order
    var self = this;
    var date = new Date();
    var yesterday = new Date(date.getTime());
    yesterday.setDate(date.getDate() - 1);
    e.stopPropagation();
    e.preventDefault();
    this.user.hasGroup('hr.group_hr_user').then(function (has_group) {
      if (has_group) {
        var options = {
          on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
        self.actionService.doAction({
          name: _t("Reembolsos de Hoy"),
          type: 'ir.actions.act_window',
          res_model: 'pos.order',
          view_mode: 'tree,form,calendar',
          view_type: 'form',
          views: [[false, 'list'], [false, 'form']],
          domain: [['amount_total', '<', 0.0], ['date_order', '<=', date], ['date_order', '>=', yesterday]],
          target: 'current'
        }, options)
      }
    });
  }
  pos_order(e) {
    //    To get total orders details
    var self = this;
    var date = new Date();
    var yesterday = new Date(date.getTime());
    yesterday.setDate(date.getDate() - 1);
    e.stopPropagation();
    e.preventDefault();
    this.user.hasGroup('hr.group_hr_user').then(function (has_group) {
      if (has_group) {
        var options = {
          on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
        self.actionService.doAction({
          name: _t("Órdenes"),
          type: 'ir.actions.act_window',
          res_model: 'pos.order',
          view_mode: 'tree,form,calendar',
          view_type: 'form',
          views: [[false, 'list'], [false, 'form']],
          target: 'current'
        }, options)
      }
    });
  }
  pos_session(e) {
    //    To get the Session wise details
    var self = this;
    e.stopPropagation();
    e.preventDefault();
    this.user.hasGroup('hr.group_hr_user').then(function (has_group) {
      if (has_group) {
        var options = {
          on_reverse_breadcrumb: self.on_reverse_breadcrumb,
        };
        self.actionService.doAction({
          name: _t("Sesiones"),
          type: 'ir.actions.act_window',
          res_model: 'pos.session',
          view_mode: 'tree,form,calendar',
          view_type: 'form',
          views: [[false, 'list'], [false, 'form']],
          target: 'current'
        }, options)
      }
    });
  }
  onclick_pos_sales(events) {
    //  To get the Sale bar chart
    var self = this
    var option = null;
    if (events && events.target) {
      option = events.target.value;
    }
    if (!option) {
      var el = document.getElementById('pos_sales');
      option = el ? el.value : 'pos_hourly_sales';
    }
    var canvas = document.getElementById('canvas_1');
    var ctx = canvas ? canvas.getContext('2d') : null;
    if (!ctx) { return; }
    const filters = this.state.filters
    this.orm.call('pos.order', 'get_department', [option, filters])
      .then(function (arrays) {
        var cols = chartColors(arrays[0].length);
        var data = {
          labels: arrays[1],
          datasets: [
            {
              label: arrays[2],
              data: arrays[0],
              backgroundColor: cols,
              borderColor: cols.map(c => c + 'cc'),
              borderWidth: 1
            },
          ]
        };
        //options
        var options = {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: false },
            legend: {
              display: true,
              position: "bottom",
              labels: { color: "#333", font: { size: 12 } }
            }
          }
        };
        //create Chart class object
        if (window.myCharts != undefined)
          window.myCharts.destroy();
        window.myCharts = new Chart(ctx, {
          type: "bar",
          data: data,
          options: options
        });

      });
  }
  render_top_customer_graph() {
    //      To render the top customer pie chart
    var self = this
    var el = document.querySelector('.top_customer');
    if (!el) { return; }
    var ctx = el.getContext('2d');
    if (!ctx) { return; }
    const filters = this.state.filters
    this.orm.call('pos.order', 'get_the_top_customer', [filters])
      .then(function (arrays) {
        var cols = chartColors(arrays[0].length);
        var data = {
          labels: arrays[1],
          datasets: [
            {
              label: "",
              data: arrays[0],
              backgroundColor: cols,
              borderColor: '#fff',
              borderWidth: 2
            },
          ]
        };
        //options
        var options = {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: "right",
              labels: { color: "#333", font: { size: 11 }, boxWidth: 12 }
            }
          }
        };
        //create Chart class object
        if (window.custChart) window.custChart.destroy();
        window.custChart = new Chart(ctx, {
          type: "pie",
          data: data,
          options: options
        });

      });
  }
  render_top_product_graph() {
    //   To render the top product graph
    var self = this
    var el = document.querySelector('.top_selling_product');
    if (!el) { return; }
    var ctx = el.getContext('2d');
    if (!ctx) { return; }
    const filters = this.state.filters
    this.orm.call('pos.order', 'get_the_top_products', [filters])
      .then(function (arrays) {
        var cols = chartColors(arrays[0].length);
        var data = {
          labels: arrays[1],
          datasets: [
            {
              label: "Cantidad",
              data: arrays[0],
              backgroundColor: cols,
              borderColor: cols.map(c => c + 'cc'),
              borderWidth: 1
            },
          ]
        };
        //options
        var options = {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {
            legend: { display: false }
          }
        };
        if (window.prodChart) window.prodChart.destroy();
        window.prodChart = new Chart(ctx, {
          type: "bar",
          data: data,
          options: options
        });
      });
  }
  render_product_category_graph() {
    //    To render the product category graph
    var self = this
    var el = document.querySelector('.top_product_categories');
    if (!el) { return; }
    var ctx = el.getContext('2d');
    if (!ctx) { return; }
    const filters = this.state.filters
    this.orm.call('pos.order', 'get_the_top_categories', [filters])
      .then(function (arrays) {
        var cols = chartColors(arrays[0].length);
        var data = {
          labels: arrays[1],
          datasets: [
            {
              label: "Cantidad",
              data: arrays[0],
              backgroundColor: cols,
              borderColor: cols.map(c => c + 'cc'),
              borderWidth: 1
            },
          ]
        };
        //options
        var options = {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: {
            legend: { display: false }
          }
        };
        if (window.catChart) window.catChart.destroy();
        window.catChart = new Chart(ctx, {
          type: "bar",
          data: data,
          options: options
        });
      });
  }

  // NEW: Salesperson Graph
  render_salesperson_graph() {
    var el = document.querySelector('.top_salesperson');
    if (!el) { return; }
    var ctx = el.getContext('2d');
    if (!ctx) { return; }
    // Data is already in this.state.top_salesperson (List of dicts: name, amount, orders)
    // Slices for top 10
    var da = (this.state.top_salesperson || []).slice(0, 10);
    var labels = da.map(x => x.name);
    var amounts = da.map(x => x.amount);

    var data = {
      labels: labels,
      datasets: [
        {
          label: "Ventas",
          data: amounts,
          backgroundColor: "rgba(54, 162, 235, 0.7)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1
        },
      ]
    };
    var options = {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: "Ventas por Vendedor" }
        }
      },
      indexAxis: 'y', // Horizontal bars
    };
    if (window.sellerChart) window.sellerChart.destroy();
    window.sellerChart = new Chart(ctx, {
      type: "bar",
      data: data,
      options: options
    });
  }
}
PosDashboard.template = 'PosDashboard'
registry.category("actions").add("pos_order_menu", PosDashboard)
