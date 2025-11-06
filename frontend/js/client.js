const WS_URL = `ws://${window.location.hostname}:5001/ws`;
let ws = null;
let candles = [];
let chart = null;
let gridApi = null;

// Configurar AG Grid
const gridOptions = {
    columnDefs: [
        { field: 'broker', width: 100 },
        { field: 'symbol', width: 100 },
        { field: 'timeframe', width: 100 },
        { field: 'open', width: 80, valueFormatter: (p) => p.value.toFixed(2) },
        { field: 'high', width: 80, valueFormatter: (p) => p.value.toFixed(2) },
        { field: 'low', width: 80, valueFormatter: (p) => p.value.toFixed(2) },
        { field: 'close', width: 80, valueFormatter: (p) => p.value.toFixed(2) },
        { field: 'volume', width: 100, valueFormatter: (p) => p.value.toFixed(0) }
    ],
    rowData: [],
    defaultColDef: {
        sortable: true,
        filter: true,
        resizable: true
    },
    theme: 'ag-theme-quartz-dark'
};

// Conectar WebSocket
function connectWebSocket() {
    ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
        console.log('✅ WebSocket conectado');
        document.getElementById('status').innerHTML = '🟢 Conectado';
        document.getElementById('status').className = 'mt-4 p-3 bg-green-900/30 border border-green-600 rounded text-green-200';
    };
    
    ws.onmessage = (event) => {
        const candle = JSON.parse(event.data);
        console.log('📊 Candle recibido:', candle);
        
        candles.push(candle);
        
        // Mantener solo últimas 100
        if (candles.length > 100) candles.shift();
        
        // Actualizar grid
        updateGrid(candle);
        
        // Actualizar chart
        updateChart();
        
        // Actualizar stats
        updateStats(candle);
    };
    
    ws.onerror = (error) => {
        console.error('❌ Error WebSocket:', error);
        document.getElementById('status').innerHTML = '🔴 Error de conexión';
        document.getElementById('status').className = 'mt-4 p-3 bg-red-900/30 border border-red-600 rounded text-red-200';
    };
    
    ws.onclose = () => {
        console.log('❌ WebSocket desconectado');
        document.getElementById('status').innerHTML = '🔴 Desconectado';
        document.getElementById('status').className = 'mt-4 p-3 bg-red-900/30 border border-red-600 rounded text-red-200';
        setTimeout(connectWebSocket, 3000);
    };
}

function updateGrid(candle) {
    if (!gridApi) return;
    gridApi.applyTransaction({ add: [candle], addIndex: 0 });
    
    // Mantener solo últimas 50 filas
    const displayedRows = gridApi.getDisplayedRowCount();
    if (displayedRows > 50) {
        gridApi.applyTransaction({ remove: [gridApi.getDisplayedRowAtIndex(49).data] });
    }
}

function updateChart() {
    if (candles.length === 0) return;
    
    // Últimas 20 velas de BTC-USD (ejemplo)
    const btcCandles = candles.filter(c => c.symbol === 'BTC-USD').slice(-20);
    
    if (!chart) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: btcCandles.map((c, i) => i),
                datasets: [
                    {
                        label: 'Close',
                        data: btcCandles.map(c => c.close),
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1
                    },
                    {
                        label: 'High',
                        data: btcCandles.map(c => c.high),
                        borderColor: 'rgba(75, 192, 75, 0.5)',
                        borderDash:[2]
                    },
                    {
                        label: 'Low',
                        data: btcCandles.map(c => c.low),
                        borderColor: 'rgba(192, 75, 75, 0.5)',
                        borderDash:[2]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { labels: { color: '#fff' } }
                },
                scales: {
                    y: { ticks: { color: '#fff' }, grid: { color: '#333' } },
                    x: { ticks: { color: '#fff' }, grid: { color: '#333' } }
                }
            }
        });
    } else {
        chart.data.labels = btcCandles.map((c, i) => i);
        chart.data.datasets[0].data = btcCandles.map(c => c.close);
        chart.data.datasets[1].data = btcCandles.map(c => c.high);
        chart.data.datasets[2].data = btcCandles.map(c => c.low);
        chart.update();
    }
}

function updateStats(candle) {
    document.getElementById('candle-count').textContent = candles.length;
    
    const symbols = [...new Set(candles.map(c => c.symbol))];
    const latest = symbols.map(s => {
        const c = candles.slice().reverse().find(x => x.symbol === s);
        return c ? `${s}: $${c.close.toFixed(2)}` : '';
    }).filter(x => x);
    
    document.getElementById('latest-symbols').innerHTML = latest
        .map(s => `<p class="text-green-400">-  ${s}</p>`)
        .join('');
}

// Inicializar Grid
document.addEventListener('DOMContentLoaded', () => {
    const gridDiv = document.querySelector('#grid');
    gridApi = agGrid.createGrid(gridDiv, gridOptions);
    connectWebSocket();
});
