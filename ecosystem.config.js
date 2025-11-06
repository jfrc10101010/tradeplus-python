// ecosystem.config.js

module.exports = {
  apps: [
    {
      name: 'tradeplus-api',
      script: 'server.py',
      interpreter: 'python',
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      env: {
        NODE_ENV: 'development'
      },
      error_file: './logs/api-error.log',
      out_file: './logs/api-out.log'
    },
    {
      name: 'tradeplus-dashboard',
      script: 'serve',
      args: '-s . -l 8080',
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'production'
      },
      error_file: './logs/dashboard-error.log',
      out_file: './logs/dashboard-out.log'
    }
  ]
};