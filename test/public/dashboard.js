/**
 * ╔═══════════════════════════════════════════════════════════════╗
 * ║        Dashboard Logic - Journal Analytics                    ║
 * ║        TRADEPLUS V5.0 - Multi-Broker Trading Journal          ║
 * ╚═══════════════════════════════════════════════════════════════╝
 */

let chartInstances = {};
let gridInstances = {};
let dashboardData = null;

/**
 * CARGAR DATOS DESDE API
 */
async function loadDashboardData() {
    try {
        const response = await fetch('/api/journal');
        const data = await response.json();
        
        dashboardData = {
            trades: data.trades || [],
            stats: data.stats || {},
            timestamp: data.timestamp
        };

        console.log('✅ Dashboard datos cargados:', dashboardData.trades.length, 'trades');
        
        // Procesar datos
        processTradeData();
        
        // Actualizar UI
        updateKPIs();
        updateCharts();
        updateGrids();
        updateLastUpdate();

    } catch (error) {
        console.error('❌ Error cargando dashboard:', error);
    }
}

/**
 * PROCESAR TRADES Y CALCULAR MÉTRICAS
 */
function processTradeData() {
    const trades = dashboardData.trades || [];
    
    dashboardData.processed = {
        totalTrades: trades.length,
        buys: 0,
        sells: 0,
        totalVolume: 0,
        totalFees: 0,
        tradesBySymbol: {},
        tradesByDate: {},
        tradesByHour: {},
        brokerSplit: { schwab: 0, coinbase: 0 },
        brokerVolume: { schwab: 0, coinbase: 0 }
    };

    trades.forEach(trade => {
        // Contadores básicos
        if (trade.side === 'BUY') dashboardData.processed.buys++;
        else dashboardData.processed.sells++;
        
        dashboardData.processed.totalVolume += (trade.amount || 0);
        dashboardData.processed.totalFees += (trade.fee || 0);

        // Por símbolo
        if (!dashboardData.processed.tradesBySymbol[trade.symbol]) {
            dashboardData.processed.tradesBySymbol[trade.symbol] = {
                count: 0,
                volume: 0,
                buys: 0,
                sells: 0,
                trades: [],
                totalQty: 0,
                avgPrice: 0
            };
        }
        
        const symData = dashboardData.processed.tradesBySymbol[trade.symbol];
        symData.count++;
        symData.volume += (trade.amount || 0);
        if (trade.side === 'BUY') symData.buys++;
        else symData.sells++;
        symData.trades.push(trade);
        symData.totalQty += (trade.quantity || 0);

        // Por fecha
        const date = new Date(trade.datetime).toLocaleDateString('es-ES');
        if (!dashboardData.processed.tradesByDate[date]) {
            dashboardData.processed.tradesByDate[date] = {
                count: 0,
                volume: 0,
                trades: []
            };
        }
        dashboardData.processed.tradesByDate[date].count++;
        dashboardData.processed.tradesByDate[date].volume += (trade.amount || 0);
        dashboardData.processed.tradesByDate[date].trades.push(trade);

        // Por hora
        const hour = new Date(trade.datetime).getHours();
        if (!dashboardData.processed.tradesByHour[hour]) {
            dashboardData.processed.tradesByHour[hour] = {
                count: 0,
                volume: 0
            };
        }
        dashboardData.processed.tradesByHour[hour].count++;
        dashboardData.processed.tradesByHour[hour].volume += (trade.amount || 0);

        // Broker
        if (trade.broker === 'schwab') {
            dashboardData.processed.brokerSplit.schwab++;
            dashboardData.processed.brokerVolume.schwab += (trade.amount || 0);
        } else {
            dashboardData.processed.brokerSplit.coinbase++;
            dashboardData.processed.brokerVolume.coinbase += (trade.amount || 0);
        }
    });

    // Calcular promedios por símbolo
    Object.values(dashboardData.processed.tradesBySymbol).forEach(symData => {
        symData.avgPrice = symData.totalQty > 0 ? symData.volume / symData.totalQty : 0;
    });

    // Promedio por trade
    dashboardData.processed.avgPerTrade = dashboardData.processed.totalTrades > 0 
        ? dashboardData.processed.totalVolume / dashboardData.processed.totalTrades 
        : 0;
}

/**
 * ACTUALIZAR KPIs PRINCIPALES
 */
function updateKPIs() {
    const proc = dashboardData.processed;
    
    document.getElementById('total-ops').textContent = proc.totalTrades;
    document.getElementById('pl-usd').textContent = `$${proc.totalVolume.toFixed(2)}`;
    
    const buyRatio = proc.totalTrades > 0 ? ((proc.buys / proc.totalTrades) * 100).toFixed(1) : 0;
    document.getElementById('win-rate').textContent = `${buyRatio}%`;
    
    document.getElementById('profit-factor').textContent = `$${proc.totalFees.toFixed(2)}`;
}

/**
 * ACTUALIZAR GRÁFICOS
 */
function updateCharts() {
    const proc = dashboardData.processed;

    // Chart: Buy vs Sell
    updateChart('chart-buysell', {
        type: 'doughnut',
        data: {
            labels: ['Compras', 'Ventas'],
            datasets: [{
                data: [proc.buys, proc.sells],
                backgroundColor: ['rgba(16, 185, 129, 0.7)', 'rgba(239, 68, 68, 0.7)'],
                borderColor: ['#10b981', '#ef4444'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e2e8f0' }
                }
            }
        }
    });

    // Chart: Brokers
    updateChart('chart-brokers', {
        type: 'pie',
        data: {
            labels: ['Schwab', 'Coinbase'],
            datasets: [{
                data: [proc.brokerSplit.schwab, proc.brokerSplit.coinbase],
                backgroundColor: ['rgba(59, 130, 246, 0.7)', 'rgba(251, 146, 60, 0.7)'],
                borderColor: ['#3b82f6', '#fb923c'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#e2e8f0' } }
            }
        }
    });

    // Chart: Actividad Diaria
    const dates = Object.keys(proc.tradesByDate).sort();
    const dailyData = dates.map(d => proc.tradesByDate[d]);
    
    updateChart('chart-daily', {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Operaciones',
                    data: dailyData.map(d => d.count),
                    backgroundColor: 'rgba(16, 185, 129, 0.5)',
                    borderColor: '#10b981',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Volumen ($)',
                    data: dailyData.map(d => d.volume),
                    backgroundColor: 'rgba(59, 130, 246, 0.5)',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { labels: { color: '#e2e8f0' } }
            },
            scales: {
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: { color: '#e2e8f0' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });

    // Chart: Horas Activas
    const hours = Array.from({length: 24}, (_, i) => i);
    const hourData = hours.map(h => proc.tradesByHour[h]?.count || 0);
    
    updateChart('chart-hours', {
        type: 'line',
        data: {
            labels: hours.map(h => `${h}:00`),
            datasets: [{
                label: 'Operaciones por Hora',
                data: hourData,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#10b981',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#e2e8f0' } }
            },
            scales: {
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });

    // Chart: Volumen por Hora
    const hourVolumeData = hours.map(h => proc.tradesByHour[h]?.volume || 0);
    
    updateChart('chart-volume-hours', {
        type: 'bar',
        data: {
            labels: hours.map(h => `${h}:00`),
            datasets: [{
                label: 'Volumen por Hora',
                data: hourVolumeData,
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: '#3b82f6',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#e2e8f0' } }
            },
            scales: {
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });

    // Chart: Distribución por Símbolo (Tab Symbols)
    const topSymbols = Object.entries(proc.tradesBySymbol)
        .sort((a, b) => b[1].volume - a[1].volume)
        .slice(0, 10);
    
    updateChart('chart-symbols-dist', {
        type: 'bar',
        data: {
            labels: topSymbols.map(s => s[0]),
            datasets: [{
                label: 'Volumen',
                data: topSymbols.map(s => s[1].volume),
                backgroundColor: 'rgba(16, 185, 129, 0.7)',
                borderColor: '#10b981',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { labels: { color: '#e2e8f0' } }
            },
            scales: {
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                },
                y: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: '#334155' }
                }
            }
        }
    });

    // Top 5 Símbolos (lista en Overview)
    updateTopSymbolsList();

    // Top Símbolos en Tab Symbols
    updateTopSymbolsSection();

    // Actualizar estadísticas en Analytics
    updateAnalyticsStats();
}

/**
 * HELPER: Actualizar o crear Chart.js
 */
function updateChart(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    // Destruir chart anterior si existe
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    // Crear nuevo chart
    chartInstances[canvasId] = new Chart(ctx, config);
}

/**
 * TOP 5 SÍMBOLOS (OVERVIEW TAB)
 */
function updateTopSymbolsList() {
    const topSymbols = Object.entries(dashboardData.processed.tradesBySymbol)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 5);
    
    const html = topSymbols.map((s, i) => `
        <div class="flex justify-between items-center p-3 bg-dark-card rounded-lg hover:bg-dark-border transition cursor-pointer"
             onclick="showSymbolModal('${s[0]}')">
            <div class="flex items-center gap-3">
                <span class="text-2xl">${['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i]}</span>
                <div>
                    <p class="font-bold text-lg">${s[0]}</p>
                    <p class="text-xs text-gray-500">${s[1].count} operaciones</p>
                </div>
            </div>
            <div class="text-right">
                <p class="font-bold profit-text">$${s[1].volume.toFixed(2)}</p>
                <p class="text-xs text-gray-500">${s[1].buys}B / ${s[1].sells}S</p>
            </div>
        </div>
    `).join('');
    
    document.getElementById('top-symbols-list').innerHTML = html;
}

/**
 * TOP SÍMBOLOS SECTION (SYMBOLS TAB)
 */
function updateTopSymbolsSection() {
    const topByVolume = Object.entries(dashboardData.processed.tradesBySymbol)
        .sort((a, b) => b[1].volume - a[1].volume)
        .slice(0, 5);
    
    const html = topByVolume.map((s, i) => `
        <div class="p-3 bg-dark-card rounded-lg mb-2 cursor-pointer hover:bg-dark-border transition"
             onclick="showSymbolModal('${s[0]}')">
            <div class="flex justify-between items-center">
                <div>
                    <span class="font-bold text-lg">${s[0]}</span>
                    <span class="text-xs text-gray-500 ml-2">${s[1].count} ops</span>
                </div>
                <span class="font-bold profit-text">$${s[1].volume.toFixed(2)}</span>
            </div>
        </div>
    `).join('');
    
    document.getElementById('top-symbols-gain').innerHTML = html;
}

/**
 * ANALYTICS STATS
 */
function updateAnalyticsStats() {
    const proc = dashboardData.processed;
    
    document.getElementById('stats-buys').textContent = proc.buys;
    document.getElementById('stats-buys-avg').textContent = `Volumen: $${proc.buys > 0 ? (dashboardData.trades.filter(t => t.side === 'BUY').reduce((sum, t) => sum + (t.amount || 0), 0)).toFixed(2) : '0.00'}`;
    
    document.getElementById('stats-sells').textContent = proc.sells;
    document.getElementById('stats-sells-avg').textContent = `Volumen: $${proc.sells > 0 ? (dashboardData.trades.filter(t => t.side === 'SELL').reduce((sum, t) => sum + (t.amount || 0), 0)).toFixed(2) : '0.00'}`;
    
    document.getElementById('stats-avg-trade').textContent = `$${proc.avgPerTrade.toFixed(2)}`;
}

/**
 * ACTUALIZAR AG GRIDS
 */
function updateGrids() {
    updateTradesGrid();
    updateSymbolsGrid();
}

function updateTradesGrid() {
    const trades = dashboardData.trades.map(t => ({
        ...t,
        datetime_formatted: new Date(t.datetime).toLocaleString('es-ES')
    }));

    const gridDiv = document.getElementById('grid-trades');
    
    const gridOptions = {
        columnDefs: [
            {
                headerName: 'Fecha',
                field: 'datetime_formatted',
                width: 180,
                filter: true
            },
            {
                headerName: 'Broker',
                field: 'broker',
                width: 100,
                cellRenderer: (params) => {
                    const colors = {
                        schwab: 'bg-blue-900/30 text-blue-400',
                        coinbase: 'bg-yellow-900/30 text-yellow-400'
                    };
                    return `<span class="px-2 py-1 rounded text-xs font-semibold ${colors[params.value] || ''}">
                        ${params.value.toUpperCase()}
                    </span>`;
                }
            },
            {
                headerName: 'Símbolo',
                field: 'symbol',
                width: 100,
                filter: true,
                cellRenderer: (params) => {
                    return `<span class="font-bold cursor-pointer hover:text-profit" 
                        onclick="showSymbolModal('${params.value}')">
                        ${params.value}
                    </span>`;
                }
            },
            {
                headerName: 'Lado',
                field: 'side',
                width: 80,
                cellRenderer: (params) => {
                    const isBuy = params.value === 'BUY';
                    return `<span class="font-bold ${isBuy ? 'profit-text' : 'loss-text'}">
                        ${params.value}
                    </span>`;
                }
            },
            {
                headerName: 'Cantidad',
                field: 'quantity',
                width: 100,
                valueFormatter: (params) => (params.value || 0).toFixed(4)
            },
            {
                headerName: 'Precio',
                field: 'price',
                width: 100,
                valueFormatter: (params) => `$${(params.value || 0).toFixed(2)}`
            },
            {
                headerName: 'Total',
                field: 'amount',
                width: 120,
                valueFormatter: (params) => `$${(params.value || 0).toFixed(2)}`
            },
            {
                headerName: 'Comisión',
                field: 'fee',
                width: 100,
                valueFormatter: (params) => `$${(params.value || 0).toFixed(2)}`
            }
        ],
        rowData: trades,
        defaultColDef: {
            resizable: true,
            sortable: true,
            filter: true
        },
        pagination: true,
        paginationPageSize: 20
    };

    if (gridInstances['trades']) {
        gridInstances['trades'].destroy();
    }

    gridInstances['trades'] = agGrid.createGrid(gridDiv, gridOptions);
}

function updateSymbolsGrid() {
    const symbolsData = Object.entries(dashboardData.processed.tradesBySymbol)
        .map(([symbol, data]) => ({
            symbol,
            count: data.count,
            buys: data.buys,
            sells: data.sells,
            volume: data.volume,
            avgPrice: data.avgPrice,
            totalQty: data.totalQty
        }))
        .sort((a, b) => b.volume - a.volume);

    const gridDiv = document.getElementById('grid-symbols');
    
    const gridOptions = {
        columnDefs: [
            {
                headerName: 'Símbolo',
                field: 'symbol',
                width: 120,
                cellRenderer: (params) => {
                    return `<span class="font-bold cursor-pointer hover:text-profit" 
                        onclick="showSymbolModal('${params.value}')">
                        ${params.value}
                    </span>`;
                }
            },
            {
                headerName: 'Ops',
                field: 'count',
                width: 80
            },
            {
                headerName: 'Compras',
                field: 'buys',
                width: 100,
                cellRenderer: (params) => `<span class="profit-text font-bold">${params.value}</span>`
            },
            {
                headerName: 'Ventas',
                field: 'sells',
                width: 100,
                cellRenderer: (params) => `<span class="loss-text font-bold">${params.value}</span>`
            },
            {
                headerName: 'Cantidad Total',
                field: 'totalQty',
                width: 120,
                valueFormatter: (params) => (params.value || 0).toFixed(4)
            },
            {
                headerName: 'Volumen',
                field: 'volume',
                width: 140,
                cellRenderer: (params) => {
                    return `<span class="font-bold profit-text">$${params.value.toFixed(2)}</span>`;
                }
            },
            {
                headerName: 'Precio Prom.',
                field: 'avgPrice',
                width: 120,
                valueFormatter: (params) => `$${(params.value || 0).toFixed(2)}`
            }
        ],
        rowData: symbolsData,
        defaultColDef: {
            resizable: true,
            sortable: true,
            filter: true
        }
    };

    if (gridInstances['symbols']) {
        gridInstances['symbols'].destroy();
    }

    gridInstances['symbols'] = agGrid.createGrid(gridDiv, gridOptions);
}

/**
 * TABS NAVIGATION
 */
function switchTab(tabName) {
    // Ocultar todos
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('[onclick*="switchTab"]').forEach(btn => {
        btn.classList.remove('tab-active');
        btn.classList.add('tab-inactive');
    });

    // Mostrar seleccionado
    const tabEl = document.getElementById(`tab-${tabName}`);
    if (tabEl) tabEl.classList.remove('hidden');

    // Marcar botón activo
    event.target.classList.remove('tab-inactive');
    event.target.classList.add('tab-active');

    // Re-renderizar grids para que se vea bien
    if (tabName === 'trades' && gridInstances['trades']) {
        setTimeout(() => {
            if (gridInstances['trades'].api) {
                gridInstances['trades'].api.sizeColumnsToFit();
            }
        }, 100);
    } else if (tabName === 'symbols' && gridInstances['symbols']) {
        setTimeout(() => {
            if (gridInstances['symbols'].api) {
                gridInstances['symbols'].api.sizeColumnsToFit();
            }
        }, 100);
    }
}

/**
 * MODAL DETALLE DE SÍMBOLO
 */
function showSymbolModal(symbol) {
    const symbolData = dashboardData.processed.tradesBySymbol[symbol];
    if (!symbolData) return;

    document.getElementById('modal-symbol').textContent = symbol;
    document.getElementById('modal-ops').textContent = symbolData.count;
    document.getElementById('modal-volume').textContent = `$${symbolData.volume.toFixed(2)}`;
    document.getElementById('modal-buys').textContent = symbolData.buys;
    document.getElementById('modal-sells').textContent = symbolData.sells;

    // Grid de detalle
    const trades = symbolData.trades.map(t => ({
        ...t,
        datetime_formatted: new Date(t.datetime).toLocaleString('es-ES')
    }));

    const gridDiv = document.getElementById('grid-symbol-detail');
    
    const gridOptions = {
        columnDefs: [
            { headerName: 'Fecha', field: 'datetime_formatted', width: 150 },
            { headerName: 'Broker', field: 'broker', width: 80 },
            { 
                headerName: 'Lado', 
                field: 'side', 
                width: 70,
                cellRenderer: (p) => {
                    const cls = p.value === 'BUY' ? 'profit-text' : 'loss-text';
                    return `<span class="${cls} font-bold">${p.value}</span>`;
                }
            },
            { headerName: 'Qty', field: 'quantity', width: 80, valueFormatter: (p) => (p.value || 0).toFixed(4) },
            { headerName: 'Precio', field: 'price', width: 100, valueFormatter: (p) => `$${(p.value || 0).toFixed(2)}` },
            { headerName: 'Total', field: 'amount', width: 100, valueFormatter: (p) => `$${(p.value || 0).toFixed(2)}` },
            { headerName: 'Fee', field: 'fee', width: 80, valueFormatter: (p) => `$${(p.value || 0).toFixed(2)}` }
        ],
        rowData: trades,
        defaultColDef: { resizable: true, sortable: true }
    };

    if (gridInstances['symbol-detail']) {
        gridInstances['symbol-detail'].destroy();
    }

    gridInstances['symbol-detail'] = agGrid.createGrid(gridDiv, gridOptions);

    // Mostrar modal
    document.getElementById('symbol-modal').classList.remove('hidden');
}

function closeSymbolModal() {
    document.getElementById('symbol-modal').classList.add('hidden');
}

/**
 * ACTUALIZAR TIMESTAMP
 */
function updateLastUpdate() {
    const time = new Date().toLocaleTimeString('es-ES', { 
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    document.getElementById('last-update').textContent = `Última actualización: ${time}`;
}

/**
 * REFRESH DASHBOARD
 */
async function refreshDashboard() {
    await loadDashboardData();
}

/**
 * INICIALIZAR
 */
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Actualizar cada 30 segundos
    setInterval(loadDashboardData, 30000);
});
