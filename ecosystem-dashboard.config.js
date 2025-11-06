module.exports = {
  apps: [{
    name: 'websocket-dashboard',
    script: 'dashboard_realtime_fixed.py',
    interpreter: 'python',
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '500M',
    error_file: './logs/dashboard.error.log',
    out_file: './logs/dashboard.out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    env: {
      NODE_ENV: 'production',
      PORT: 8000
    },
    restart_delay: 4000,
    max_restarts: 10,
    min_uptime: '10s'
  }]
};
