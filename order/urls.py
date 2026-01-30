from django.urls import path
from .views_ajax import get_metal_stock_balance
from .views import (





















































































































































































































































































































































































{% endblock %}</script>{% endif %}});    }        }            }                }                    }                        return 'रु' + value.toLocaleString('en-IN');                    callback: function(value) {                ticks: {                beginAtZero: true,            y: {        scales: {        },            }                }                    }                               ' (' + (percent >= 0 ? '+' : '') + percent.toFixed(2) + '%)';                        return 'रु' + value.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2}) +                         const percent = profitLossData[context.dataIndex].percent;                        const value = context.parsed.y;                    label: function(context) {                callbacks: {            tooltip: {            },                display: false            legend: {        plugins: {        maintainAspectRatio: true,        responsive: true,    options: {    },        }]            borderWidth: 2            borderColor: profitLossData.map(d => d.value >= 0 ? '#10b981' : '#ef4444'),            backgroundColor: profitLossData.map(d => d.value >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'),            data: profitLossData.map(d => d.value),            label: 'Profit/Loss',        datasets: [{        labels: profitLossData.map(d => d.date),    data: {    type: 'bar',new Chart(profitLossCtx, {const profitLossCtx = document.getElementById('profitLossChart').getContext('2d');// Profit/Loss Chart});    }        }            }                }                    }                        return 'रु' + value.toLocaleString('en-IN');                    callback: function(value) {                ticks: {                position: 'left',                beginAtZero: false,            y: {        scales: {        },            }                }                    }                        return context.dataset.label + ': रु' + context.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2}) + '/tola';                    label: function(context) {                callbacks: {            tooltip: {            },                }                    font: { size: 12, weight: 'bold' }                    padding: 15,                    usePointStyle: true,                labels: {                position: 'top',            legend: {        plugins: {        },            intersect: false            mode: 'index',        interaction: {        maintainAspectRatio: true,        responsive: true,    options: {    },        ]            }                yAxisID: 'y'                tension: 0.4,                borderWidth: 3,                backgroundColor: 'rgba(156, 163, 175, 0.1)',                borderColor: '#9ca3af',                data: chartData.map(d => d.silver_rate),                label: 'Silver Rate',            {            },                yAxisID: 'y'                tension: 0.4,                borderWidth: 3,                backgroundColor: 'rgba(245, 158, 11, 0.1)',                borderColor: '#f59e0b',                data: chartData.map(d => d.gold_rate),                label: 'Gold Rate',            {        datasets: [        labels: chartData.map(d => d.date),    data: {    type: 'line',new Chart(rateTrendCtx, {const rateTrendCtx = document.getElementById('rateTrendChart').getContext('2d');// Rate Trend Chart});    }        }            }                }                    }                        return 'रु' + value.toLocaleString('en-IN');                    callback: function(value) {                ticks: {                beginAtZero: true,            y: {        scales: {        },            }                }                    }                        return context.dataset.label + ': रु' + context.parsed.y.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});                    label: function(context) {                callbacks: {            tooltip: {            },                }                    font: { size: 12, weight: 'bold' }                    padding: 15,                    usePointStyle: true,                labels: {                position: 'top',            legend: {        plugins: {        },            intersect: false            mode: 'index',        interaction: {        maintainAspectRatio: true,        responsive: true,    options: {    },        ]            }                fill: false                tension: 0.4,                borderWidth: 4,                backgroundColor: 'rgba(16, 185, 129, 0.1)',                borderColor: '#10b981',                data: chartData.map(d => d.total_value),                label: 'Total Value',            {            },                fill: true                tension: 0.4,                borderWidth: 3,                backgroundColor: 'rgba(139, 92, 246, 0.1)',                borderColor: '#8b5cf6',                data: chartData.map(d => d.diamond_value),                label: 'Diamond Value',            {            },                fill: true                tension: 0.4,                borderWidth: 3,                backgroundColor: 'rgba(156, 163, 175, 0.1)',                borderColor: '#9ca3af',                data: chartData.map(d => d.silver_value),                label: 'Silver Value',            {            },                fill: true                tension: 0.4,                borderWidth: 3,                backgroundColor: 'rgba(245, 158, 11, 0.1)',                borderColor: '#f59e0b',                data: chartData.map(d => d.gold_value),                label: 'Gold Value',            {        datasets: [        labels: chartData.map(d => d.date),    data: {    type: 'line',new Chart(stockValueCtx, {const stockValueCtx = document.getElementById('stockValueChart').getContext('2d');// Stock Value Chartconst profitLossData = {{ profit_loss_data|safe }};const chartData = {{ chart_data|safe }};{% if chart_data %}<script><script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script><!-- Chart.js --></div>    {% endif %}    </div>        <strong>No rate data available.</strong> Daily rates need to be recorded to generate charts.        <i class="bi bi-info-circle me-2"></i>    <div class="alert alert-info text-center">    {% else %}    </div>        <canvas id="profitLossChart" height="80"></canvas>        </div>            <i class="bi bi-currency-exchange me-2"></i>Profit & Loss Trend        <div class="chart-title">    <div class="chart-container">    <!-- Profit/Loss Chart -->    </div>        <canvas id="rateTrendChart" height="80"></canvas>        </div>            <i class="bi bi-graph-up me-2"></i>Daily Rate Trends (Per Tola)        <div class="chart-title">    <div class="chart-container">    <!-- Rate Trend Chart -->    </div>        <canvas id="stockValueChart" height="80"></canvas>        </div>            <i class="bi bi-bar-chart-line me-2"></i>Stock Value by Metal Type        <div class="chart-title">    <div class="chart-container">    <!-- Stock Value Chart -->    {% if chart_data %}    </div>        {% endif %}        </div>            </div>                </div>                    {% if total_change_percent >= 0 %}+{% endif %}{{ total_change_percent|floatformat:2 }}%                <div class="stat-subvalue {% if total_change_percent >= 0 %}positive{% else %}negative{% endif %}">                </div>                    {% if total_change >= 0 %}+{% endif %}रु{{ total_change|floatformat:2 }}                <div class="stat-value {% if total_change >= 0 %}positive{% else %}negative{% endif %}">                <div class="stat-label">{{ days }}-Day Change</div>            <div class="stat-card change">        <div class="col-lg-3 col-md-6 col-sm-6">        </div>            </div>                <div class="stat-subvalue">As of {{ latest.date }}</div>                <div class="stat-value">रु{{ latest.total_value|floatformat:2 }}</div>                <div class="stat-label">Current Value</div>            <div class="stat-card total">        <div class="col-lg-3 col-md-6 col-sm-6">        {% if latest %}        </div>            </div>                <div class="stat-subvalue">{{ diamond_count }} ornaments<br>{{ diamond_stone_weight|floatformat:3 }}g stones</div>                <div class="stat-value">{{ diamond_metal_weight|floatformat:3 }}g</div>                <div class="stat-label">Diamond Stock</div>            <div class="stat-card diamond">        <div class="col-lg-2 col-md-4 col-sm-6">        </div>            </div>                <div class="stat-subvalue">{{ silver_count }} ornaments</div>                <div class="stat-value">{{ silver_weight|floatformat:3 }}g</div>                <div class="stat-label">Silver Stock</div>            <div class="stat-card silver">        <div class="col-lg-2 col-md-4 col-sm-6">        </div>            </div>                <div class="stat-subvalue">{{ gold_count }} ornaments</div>                <div class="stat-value">{{ gold_weight|floatformat:3 }}g</div>                <div class="stat-label">Gold Stock</div>            <div class="stat-card gold">        <div class="col-lg-2 col-md-4 col-sm-6">    <div class="row g-3 mb-4">    <!-- Summary Statistics -->    </div>        </form>            </div>                </select>                    <option value="90" {% if days == 90 %}selected{% endif %}>Last 90 Days</option>                    <option value="60" {% if days == 60 %}selected{% endif %}>Last 60 Days</option>                    <option value="30" {% if days == 30 %}selected{% endif %}>Last 30 Days</option>                    <option value="15" {% if days == 15 %}selected{% endif %}>Last 15 Days</option>                    <option value="7" {% if days == 7 %}selected{% endif %}>Last 7 Days</option>                <select name="days" class="form-select" onchange="this.form.submit()">                <label class="form-label fw-bold">Time Period:</label>            <div class="col-auto">        <form method="get" class="row g-3 align-items-end">    <div class="filter-section">    <!-- Filter Section -->    </div>        <p class="mb-0 opacity-90">Track stock value changes based on daily gold, silver, and diamond rates</p>        </h1>            <i class="bi bi-graph-up-arrow me-2"></i>Daily Profit & Loss Report        <h1 class="mb-2">    <div class="report-header"><div class="container-fluid mt-4"></style>    }        box-shadow: 0 2px 10px rgba(0,0,0,0.08);        margin-bottom: 20px;        padding: 20px;        border-radius: 12px;        background: white;    .filter-section {    .negative { color: #ef4444; }    .positive { color: #10b981; }    }        margin-bottom: 20px;        color: #1f2937;        font-weight: 700;        font-size: 18px;    .chart-title {    }        box-shadow: 0 2px 10px rgba(0,0,0,0.08);        margin-bottom: 20px;        padding: 25px;        border-radius: 12px;        background: white;    .chart-container {    }        margin-top: 5px;        color: #6b7280;        font-size: 14px;    .stat-subvalue {    }        color: #1f2937;        font-weight: 700;        font-size: 24px;    .stat-value {    }        margin-bottom: 8px;        text-transform: uppercase;        font-weight: 600;        color: #6b7280;        font-size: 12px;    .stat-label {    .stat-card.change { border-color: #3b82f6; }    .stat-card.total { border-color: #10b981; }    .stat-card.diamond { border-color: #8b5cf6; }    .stat-card.silver { border-color: #9ca3af; }    .stat-card.gold { border-color: #f59e0b; }    }        box-shadow: 0 8px 20px rgba(0,0,0,0.15);        transform: translateY(-5px);    .stat-card:hover {    }        height: 100%;        border-left: 4px solid;        transition: all 0.3s;        text-align: center;        box-shadow: 0 2px 10px rgba(0,0,0,0.08);        padding: 20px;        border-radius: 12px;        background: white;    .stat-card {    }        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);        margin-bottom: 30px;        border-radius: 15px;        padding: 30px;        color: white;        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);    .report-header {<style>    OrderListView,
    OrderCreateView,
    OrderUpdateView,
    OrderDeleteView,
    SearchOrnamentsAPI,
    CreateOrnamentInlineView,
    CreateSaleFromOrderView,
    SalesListView,
    SaleUpdateView,
    SaleDeleteView,
    order_print_view,
    order_export_excel,
    order_import_excel,
    order_ornaments_export_excel,
    order_payments_export_excel,
    order_ornaments_import_excel,
    order_payments_import_excel,
)
from .reports import (
    OrderDashboardReport,
    OrderSalesAnalysis,
    OrderPaymentAnalysis,
    OrderMetalAnalysis,
    OrderCustomerAnalysis,
    FastSlowMoversReport,
    StockAgingReport,
    MarginByCategoryReport,
    PaymentMixDiscountsReport,
    DebtorAgingReport,
    MonthlySalesReport,
    DailyProfitLossReport,
)

app_name = 'order'

urlpatterns = [
    path('ajax/metal-stock-balance/', get_metal_stock_balance, name='ajax_metal_stock_balance'),
    path('', OrderListView.as_view(), name='list'),
    path('create/', OrderCreateView.as_view(), name='create'),
    path('update/<int:pk>/', OrderUpdateView.as_view(), name='update'),
    path('delete/<int:pk>/', OrderDeleteView.as_view(), name='delete'),
    path('print/', order_print_view, name='print_view'),
    path('export-excel/', order_export_excel, name='export_excel'),
    path('import-excel/', order_import_excel, name='import_excel'),
    path('export-order-ornaments/', order_ornaments_export_excel, name='export_order_ornaments'),
    path('export-order-payments/', order_payments_export_excel, name='export_order_payments'),
    path('import-order-ornaments/', order_ornaments_import_excel, name='import_order_ornaments'),
    path('import-order-payments/', order_payments_import_excel, name='import_order_payments'),
    path('sales/', SalesListView.as_view(), name='sales_list'),
    path('sales/create-from-order/<int:pk>/', CreateSaleFromOrderView.as_view(), name='create_sale_from_order'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale_update'),
    path('sales/<int:pk>/delete/', SaleDeleteView.as_view(), name='sale_delete'),
    path('api/search-ornaments/', SearchOrnamentsAPI.as_view(), name='search_ornaments'),
    path('api/create-ornament-inline/', CreateOrnamentInlineView.as_view(), name='create_ornament_inline'),
    # Report URLs
    path('reports/dashboard/', OrderDashboardReport.as_view(), name='dashboard_report'),
    path('reports/sales/', OrderSalesAnalysis.as_view(), name='sales_report'),
    path('reports/payments/', OrderPaymentAnalysis.as_view(), name='payment_report'),
    path('reports/metals/', OrderMetalAnalysis.as_view(), name='metal_report'),
    path('reports/customers/', OrderCustomerAnalysis.as_view(), name='customer_report'),
    path('reports/fast-slow-movers/', FastSlowMoversReport.as_view(), name='fast_slow_movers_report'),
    path('reports/stock-aging/', StockAgingReport.as_view(), name='stock_aging_report'),
    path('reports/margin-by-category/', MarginByCategoryReport.as_view(), name='margin_report'),
    path('reports/payment-mix-discounts/', PaymentMixDiscountsReport.as_view(), name='payment_mix_report'),
    path('reports/debtor-aging/', DebtorAgingReport.as_view(), name='debtor_aging_report'),
    path('reports/monthly-sales/', MonthlySalesReport.as_view(), name='monthly_sales_report'),
    path('reports/daily-profit-loss/', DailyProfitLossReport.as_view(), name='daily_profit_loss_report'),
]