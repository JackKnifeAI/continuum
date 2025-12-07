#!/bin/bash
# CONTINUUM Cloudflare Workers - Setup Script

set -e

echo "🚀 CONTINUUM Cloudflare Workers Setup"
echo "======================================"
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Check if logged in
echo "🔐 Checking Cloudflare authentication..."
if ! wrangler whoami &> /dev/null; then
    echo "Please login to Cloudflare:"
    wrangler login
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create KV namespaces
echo "🗄️  Creating KV namespaces..."
echo ""
echo "Creating CACHE namespace..."
wrangler kv:namespace create CACHE
echo ""
echo "Creating CACHE preview namespace..."
wrangler kv:namespace create CACHE --preview
echo ""
echo "Creating SESSIONS namespace..."
wrangler kv:namespace create SESSIONS
echo ""
echo "Creating SESSIONS preview namespace..."
wrangler kv:namespace create SESSIONS --preview
echo ""

echo "⚠️  IMPORTANT: Update wrangler.toml with the namespace IDs shown above"
echo ""

# Generate JWT secret
echo "🔑 Generating JWT secret..."
JWT_SECRET=$(openssl rand -base64 32)
echo "Generated JWT secret: $JWT_SECRET"
echo ""

# Create .dev.vars file
if [ ! -f .dev.vars ]; then
    echo "📝 Creating .dev.vars file..."
    cp .dev.vars.example .dev.vars
    sed -i "s/your-secret-key-here-use-openssl-rand-base64-32/$JWT_SECRET/" .dev.vars
    echo "✅ Created .dev.vars with generated JWT secret"
else
    echo "⚠️  .dev.vars already exists. Skipping..."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update wrangler.toml with the KV namespace IDs"
echo "2. Set production secrets:"
echo "   echo '$JWT_SECRET' | wrangler secret put JWT_SECRET"
echo "3. Run development server:"
echo "   npm run dev"
echo "4. Deploy to production:"
echo "   npm run deploy:prod"
echo ""
