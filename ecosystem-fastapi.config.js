module.exports = {
  apps: [{
    name: 'tradeplus-fastapi',
    script: 'uvicorn',
    args: 'server_fastapi:app --host 0.0.0.0 --port 8080 --log-level info',
    cwd: 'C:\\Users\\joser\\TradePlus\\tradeplus-python',
    interpreter: 'python',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    error_file: './logs/fastapi-error.log',
    out_file: './logs/fastapi-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss'
  }]
};
