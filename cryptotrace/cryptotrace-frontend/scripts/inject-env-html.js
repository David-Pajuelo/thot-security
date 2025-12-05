#!/usr/bin/env node
/**
 * Script para inyectar variables de entorno en archivos HTML estáticos
 * Reemplaza placeholders como __VARIABLE__ con valores de variables de entorno
 */

const fs = require('fs');
const path = require('path');

const PUBLIC_DIR = path.join(__dirname, '..', 'public');
const TOKEN_SYNC_HTML = path.join(PUBLIC_DIR, 'token-sync.html');

// Variables de entorno a inyectar
const ENV_VARS = {
  '__HPS_SYSTEM_URL__': process.env.NEXT_PUBLIC_HPS_SYSTEM_URL || 'http://localhost:3001',
};

function injectEnvVars() {
  console.log('🔧 Inyectando variables de entorno en archivos HTML...');
  
  // Procesar token-sync.html
  if (fs.existsSync(TOKEN_SYNC_HTML)) {
    let content = fs.readFileSync(TOKEN_SYNC_HTML, 'utf8');
    
    // Reemplazar placeholders
    Object.entries(ENV_VARS).forEach(([placeholder, value]) => {
      content = content.replace(new RegExp(placeholder, 'g'), value);
      console.log(`  ✅ Reemplazado ${placeholder} → ${value}`);
    });
    
    fs.writeFileSync(TOKEN_SYNC_HTML, content, 'utf8');
    console.log('  ✅ token-sync.html actualizado');
  } else {
    console.warn('  ⚠️ token-sync.html no encontrado');
  }
  
  console.log('✅ Inyección de variables completada');
}

// Ejecutar solo si se llama directamente
if (require.main === module) {
  injectEnvVars();
}

module.exports = { injectEnvVars };

