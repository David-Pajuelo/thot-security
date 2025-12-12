/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Optimización para producción con archivos estáticos
  ...(process.env.NODE_ENV === 'production' ? { output: 'standalone' } : {}),
  trailingSlash: true,
  // Base path para servir desde /cryptotrace
  basePath: process.env.NODE_ENV === 'production' ? '/cryptotrace' : '',
  // Configuración para archivos estáticos
  assetPrefix: process.env.NODE_ENV === 'production' ? '/cryptotrace' : '',
  // Optimizaciones de build
  compress: true,
  poweredByHeader: false,
  swcMinify: true, // Usar SWC para minificación más rápida
  // Configuración para evitar errores en build de producción
  serverExternalPackages: ['canvas', 'pdfjs-dist'],
  // Configuración para páginas que requieren client-side rendering
  async rewrites() {
    return [];
  },
}

export default nextConfig
