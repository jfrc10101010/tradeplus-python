/**
 * PM2 Configuration para Journal Test Server
 * Ejecutar: pm2 start ecosystem.config.js
 */

module.exports = {
  apps: [
    {
      name: 'journal-test',
      script: './test/server.js',
      env: {
        NODE_ENV: 'production',
        PORT: 8080
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: './logs/journal-test-error.log',
      out_file: './logs/journal-test-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    }
  ]
};
