import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.FRONTEND_PORT || 8080;

// Servir archivos estáticos (HTML, CSS, JS)
app.use(express.static(__dirname));

// Ruta raíz - sirve index.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Ruta para cualquier otro archivo
app.get('/*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Escuchar en puerto
app.listen(PORT, () => {
  console.log(`✅ Frontend servidor corriendo en http://localhost:${PORT}`);
  console.log(`   Abre el navegador y ve a http://localhost:${PORT}`);
});
