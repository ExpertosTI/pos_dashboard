/** @odoo-module **/
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { onWillStart, onMounted, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
const actionRegistry = registry.category("actions");
export class PosDashboard extends Component{
//Initializes the PosDashboard component,
    setup() {
            super.setup(...arguments);
            this.orm = useService('orm')
            this.user = user;
            this.actionService = useService("action");
            this.state = useState({
                payment_details : [],
                top_salesperson : [],
                selling_product : [],
                total_sale: [],
                total_order_count: [],
                total_refund_count : [],
                total_session:[],
                today_refund_total:[],
                today_sale:[],
                sessions_list: [],
                configs: [],
                filter_start: null,
                filter_end: null,
                selected_configs: [],
                detailed_report: {
                    summary: {},
                    products: [],
                    taxes: [],
                    payments: [],
                    discounts: {},
                    invoices: [],
                    sessions: [],
                    currency: {},
                },
            });
            // When the component is about to start, fetch data in tiles
            onWillStart(async () => {
                await this.fetch_data();
            });
            //When the component is mounted, render various charts
            onMounted(async () => {
                await this.render_top_customer_graph();
                await this.render_top_product_graph();
                await this.render_product_category_graph();
                await this.onclick_pos_sales('pos_daily_sales');
            });
    }
    async fetch_data() {
    //  Function to fetch all the pos details
        var result = await this.orm.call('pos.order','get_refund_details',[])
             this.state.total_sale = result['total_sale'],
             this.state.total_order_count = result['total_order_count']
             this.state.total_refund_count = result['total_refund_count']
             this.state.total_session = result['total_session']
             this.state.today_refund_total = result['today_refund_total']
             this.state.today_sale = result['today_sale']
        var data =  await this.orm.call('pos.order','get_details',[])
             this.state.payment_details = data['payment_details']
             this.state.top_salesperson = data['salesperson']
             this.state.selling_product = data['selling_product']
             this.state.sessions_list = data['sessions'] || []
             this.state.configs = data['configs'] || []
             if (!this.state.filter_start) {
                this.state.filter_start = this.getDefaultStartDate()
             }
             if (!this.state.filter_end) {
                this.state.filter_end = this.getDefaultEndDate()
             }
             if (!this.state.selected_configs.length && this.state.configs.length) {
                this.state.selected_configs = this.state.configs.map((config) => config.id)
             }
             await this.loadDetailedReport()
    }
    getDefaultStartDate(){
        const date = new Date();
        date.setHours(0,0,0,0);
        return this.toInputDateTime(date);
    }
    getDefaultEndDate(){
        const date = new Date();
        return this.toInputDateTime(date);
    }
    toInputDateTime(date){
        const pad = (value) => value.toString().padStart(2,'0');
        const year = date.getFullYear();
        const month = pad(date.getMonth()+1);
        const day = pad(date.getDate());
        const hours = pad(date.getHours());
        const minutes = pad(date.getMinutes());
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    async loadDetailedReport(){
        const payload = {
            start_date: this.state.filter_start,
            end_date: this.state.filter_end,
            config_ids: this.state.selected_configs,
        }
        const data = await this.orm.call('pos.order','get_dynamic_sales_details',[payload])
        this.state.detailed_report = data
        
        // Debug: Log de imagen del producto más vendido
        if (data.summary && data.summary.top_product_image) {
            console.log('🖼️ Imagen del producto más vendido recibida:', {
                producto: data.summary.top_product_name,
                tiene_imagen: !!data.summary.top_product_image,
                longitud: data.summary.top_product_image ? data.summary.top_product_image.length : 0
            });
        } else {
            console.warn('⚠️ No se recibió imagen del producto más vendido');
        }
    }
    async applyFilters(){
        await this.loadDetailedReport()
    }
    onChangeStart(event){
        this.state.filter_start = event.target.value
    }
    onChangeEnd(event){
        this.state.filter_end = event.target.value
    }
    onToggleConfig(event){
        const configId = parseInt(event.target.dataset.configId)
        const current = new Set(this.state.selected_configs)
        if (current.has(configId)){
            current.delete(configId)
        } else {
            current.add(configId)
        }
        this.state.selected_configs = Array.from(current)
    }
    formatCurrency(amount){
        if (amount === undefined || amount === null){
            return ''
        }
        const currency = this.state.detailed_report.currency || {}
        const symbol = currency.symbol || ''
        const decimals = currency.decimal_places !== undefined ? currency.decimal_places : 2
        const position = currency.position || 'before'
        const numeric = Number(amount || 0)
        const formatted = numeric.toFixed(decimals)
        return position === 'after' ? `${formatted} ${symbol}` : `${symbol} ${formatted}`
    }
    formatNumber(value, decimals=2){
        return Number(value || 0).toFixed(decimals)
    }
    pos_order_today (e){
    // Obtener los detalles de las órdenes de hoy
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                 self.actionService.doAction({
                    name: _t("Pedidos de Hoy"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['date_order','<=', date],['date_order', '>=', yesterday]],
                    target: 'current'
                }, options)
            }
        });
    }
    pos_refund_orders (e){
    // Obtener los detalles de las órdenes reembolsadas
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Reembolsos"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['amount_total', '<', 0.0]],
                    target: 'current'
                }, options)
            }
        });
    }
    pos_refund_today_orders (e){
    // Obtener los detalles de los reembolsos de hoy
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Refund Orders"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['amount_total', '<', 0.0],['date_order','<=', date],['date_order', '>=', yesterday]],
                    target: 'current'
                }, options)
            }
        });
    }
     pos_order (e){
    // Obtener el detalle de todas las órdenes
        var self = this;
        var date = new Date();
        var yesterday = new Date(date.getTime());
        yesterday.setDate(date.getDate() - 1);
        e.stopPropagation();
        e.preventDefault();
        this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Pedidos Totales"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.order',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'current'
                }, options)
            }
        });
    }
    pos_session (e){
    // Obtener el detalle por sesión
        var self = this;
        e.stopPropagation();
        e.preventDefault();
         this.user.hasGroup('hr.group_hr_user').then(function(has_group){
            if(has_group){
                var options = {
                    on_reverse_breadcrumb: self.on_reverse_breadcrumb,
                };
                self.actionService.doAction({
                    name: _t("Sesiones"),
                    type: 'ir.actions.act_window',
                    res_model: 'pos.session',
                    view_mode: 'tree,form,calendar',
                    view_type: 'form',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'current'
                }, options)
            }
        });
    }
    onclick_pos_sales (events){
    // Obtener la gráfica de ventas
       var option = typeof events === 'string' ? events : $(events.target).val();
       var self = this
        var ctx = $("#canvas_1");
        this.orm.call('pos.order', 'get_department',[option])
            .then(function (arrays) {
          var data = {
            labels: arrays[2],
            datasets: [
              {
                label: arrays[3],
                data: arrays[0],
                backgroundColor: [
                  "rgba(255, 99, 132,1)",
                  "rgba(54, 162, 235,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },
            ]
          };
    //options
          var options = {
            responsive: true,
            title: {
              display: true,
              position: "top",
              text: _t("DETALLE DE VENTAS"),
              fontSize: 18,
              fontColor: "#111"
            },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
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
    render_top_customer_graph(){
    // Renderizar el gráfico de clientes principales
       var self = this
       var ctx = $(".top_customer");
       this.orm.call('pos.order', 'get_the_top_customer')
        .then(function (arrays) {
          var data = {
            labels: arrays[2],
            datasets: [
              {
                label: "",
                data: arrays[0],
                backgroundColor: [
                  "rgb(148, 22, 227)",
                  "rgba(54, 162, 235)",
                  "rgba(75, 192, 192)",
                  "rgba(153, 102, 255)",
                  "rgba(10,20,30)"
                ],
                borderColor: [
                 "rgba(255, 99, 132,)",
                  "rgba(54, 162, 235,)",
                  "rgba(75, 192, 192,)",
                  "rgba(153, 102, 255,)",
                  "rgba(10,20,30,)"
                ],
                borderWidth: 1
              },

            ]
          };
    //options
          var options = {
            responsive: true,
             scales: {
          x: {
            title: {
              display: true,
              text: _t("Clientes principales"),
              position: "top",
              fontSize: 24,
              color: "#111"
            }
          }
        },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            }
          };
          //create Chart class object
          var chart = new Chart(ctx, {
            type: "pie",
            data: data,
            options: options
          });

        });
        }
    render_top_product_graph (){
     // Renderizar el gráfico de productos principales
       var self = this
        var ctx = $(".top_selling_product");
       this.orm.call('pos.order', 'get_the_top_products')
            .then(function (arrays) {
          var data = {

            labels: arrays[2],
            datasets: [
              {
                label: _t("Cantidad"),
                data: arrays[0],
                backgroundColor: [
                  "rgba(255, 99, 132,1)",
                  "rgba(54, 162, 235,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },

            ]
          };
    //options
          var options = {
            responsive: true,
            indexAxis: 'y',
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
             scales: {
          x: {
            title: {
              display: true,
              text: _t("Productos principales"),
              position: "top",
              fontSize: 24,
              color: "#111"
            }
          }
        },
          };
          //create Chart class object
          var chart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
          });
        });
        }
    render_product_category_graph (){
        // Renderizar el gráfico por categoría
           var self = this
        var ctx = $(".top_product_categories");
        this.orm.call('pos.order', 'get_the_top_categories')
            .then(function (arrays) {
          var data = {
            labels: arrays[2],
            datasets: [
              {
                label: _t("Cantidad"),
                data: arrays[0],
                backgroundColor: [
                  "rgba(255, 99, 132,1)",
                  "rgba(54, 162, 235,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(255, 99, 132, 0.2)",
                  "rgba(54, 162, 235, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },
            ]
          };
    //options
          var options = {
            responsive: true,
             scales: {
          x: {
            title: {
              display: true,
              text: _t("Categorías principales"),
              position: "top",
              fontSize: 24,
              color: "#111"
            }
          }
        },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            indexAxis: 'y',
          };
          //create Chart class object
          var chart = new Chart(ctx, {
            type: "bar",
            data: data,
            options: options
          });
        });
        }
}
PosDashboard.template = 'PosDashboard'
registry.category("actions").add("pos_order_menu", PosDashboard)
