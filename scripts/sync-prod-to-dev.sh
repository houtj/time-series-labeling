#!/bin/bash
# Sync production data to development environment
# This includes: app_data, MongoDB data, and Redis data
# This allows you to test with real production data in a safe dev environment

set -e  # Exit on error

# Directory paths
PROD_BASE="/home/thou2/projects/hill-app"
DEV_BASE="/home/thou2/projects/hill_dev"

PROD_APP_DATA="$PROD_BASE/app_data"
PROD_MONGODB_DATA="$PROD_BASE/mongodb_data"

DEV_APP_DATA="$DEV_BASE/dev_data"
DEV_MONGODB_DATA="$DEV_BASE/mongodb_data"
DEV_REDIS_DATA="$DEV_BASE/redis_data"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Sync Production Data to Development                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  WARNING: This will OVERWRITE all data in dev environment!"
echo ""
echo "This will sync:"
echo "  1. Application data (uploaded files, parsed JSON)"
echo "  2. MongoDB data (database files)"
echo "  3. Redis data (will be cleared and restarted fresh)"
echo ""

# Check if prod directories exist
if [ ! -d "$PROD_APP_DATA" ]; then
    echo "❌ Error: Production app_data not found: $PROD_APP_DATA"
    exit 1
fi

if [ ! -d "$PROD_MONGODB_DATA" ]; then
    echo "❌ Error: Production mongodb_data not found: $PROD_MONGODB_DATA"
    exit 1
fi

# Show directory sizes
echo "📊 Current sizes:"
echo ""
echo "Production:"
echo "  App data:     $(du -sh "$PROD_APP_DATA" 2>/dev/null | cut -f1)"
echo "  MongoDB data: $(du -sh "$PROD_MONGODB_DATA" 2>/dev/null | cut -f1)"
echo ""
echo "Development (current):"
echo "  App data:     $(du -sh "$DEV_APP_DATA" 2>/dev/null | cut -f1 || echo '(empty)')"
echo "  MongoDB data: $(du -sh "$DEV_MONGODB_DATA" 2>/dev/null | cut -f1 || echo '(empty)')"
echo "  Redis data:   $(du -sh "$DEV_REDIS_DATA" 2>/dev/null | cut -f1 || echo '(empty)')"
echo ""

# Confirm with user
read -p "Continue with sync? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Sync cancelled."
    exit 0
fi

echo ""
echo "🛑 Step 1: Stopping dev databases..."
cd "$DEV_BASE"
if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    docker compose -f docker-compose.dev.yml down
    echo "✅ Dev databases stopped"
else
    echo "ℹ️  Dev databases were not running"
fi

echo ""
echo "📦 Step 2: Syncing application data..."
mkdir -p "$DEV_APP_DATA"

if command -v rsync &> /dev/null; then
    rsync -av --delete \
        --exclude='*.log' \
        --exclude='*.tmp' \
        "$PROD_APP_DATA/" "$DEV_APP_DATA/"
else
    echo "⚠️  rsync not found, using cp instead (slower)"
    rm -rf "$DEV_APP_DATA"
    cp -r "$PROD_APP_DATA" "$DEV_APP_DATA"
fi
echo "✅ Application data synced"

echo ""
echo "📦 Step 3: Syncing MongoDB data..."
mkdir -p "$DEV_MONGODB_DATA"

if command -v rsync &> /dev/null; then
    # Remove existing dev MongoDB data and sync from prod
    rm -rf "$DEV_MONGODB_DATA"/*
    rsync -av "$PROD_MONGODB_DATA/" "$DEV_MONGODB_DATA/"
else
    rm -rf "$DEV_MONGODB_DATA"
    cp -r "$PROD_MONGODB_DATA" "$DEV_MONGODB_DATA"
fi
echo "✅ MongoDB data synced"

echo ""
echo "📦 Step 4: Clearing Redis data..."
# Redis data should start fresh - clear it
rm -rf "$DEV_REDIS_DATA"
mkdir -p "$DEV_REDIS_DATA"
echo "✅ Redis data cleared (will start fresh)"

echo ""
echo "🚀 Step 5: Starting dev databases..."
cd "$DEV_BASE"
docker compose -f docker-compose.dev.yml up -d
echo "✅ Dev databases started"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Sync completed successfully!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📊 New dev data sizes:"
echo "  App data:     $(du -sh "$DEV_APP_DATA" | cut -f1)"
echo "  MongoDB data: $(du -sh "$DEV_MONGODB_DATA" | cut -f1)"
echo "  Redis data:   $(du -sh "$DEV_REDIS_DATA" | cut -f1)"
echo ""
echo "💡 Next steps:"
echo "  - Dev databases are now running with production data"
echo "  - Restart dev backend:  ./scripts/start-dev-backend.sh"
echo "  - Restart dev worker:   ./scripts/start-dev-worker.sh"
echo "  - Restart dev frontend: ./scripts/start-dev-frontend.sh"
echo ""
