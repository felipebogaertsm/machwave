module.exports = {
  reactStrictMode: true,
  serverRuntimeConfig: {
    BACKEND_URL: process.env.SERVER_BACKEND_URL,
  },
  publicRuntimeConfig: {
    BACKEND_URL: process.env.CLIENT_BACKEND_URL,
  },
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
};
