/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Mode standalone pour la production Docker
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  images: {
    domains: [
      'localhost',
      '127.0.0.1',
      // Ajouter vos domaines de production ici
      process.env.NEXT_PUBLIC_API_URL?.replace(/https?:\/\//, '').split(':')[0],
    ].filter(Boolean),
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}

module.exports = nextConfig

