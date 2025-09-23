#!/bin/bash

VERSION="1.0.0"
PACKAGE_NAME="qyro"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed. Install it with: pip install poetry"
    exit 1
fi

echo "🔄 Updating package data..."
if [ -f "package.json" ]; then
    cp package.json $PACKAGE_NAME/cli_commands/
    echo "✅ package.json copied"
else
    echo "⚠️  package.json not found, continuing..."
fi

echo "🧹 Cleaning previous builds..."
rm -rf build dist *.egg-info

echo "📦 Checking Poetry configuration..."
poetry check

echo "📦 Building wheel for $PACKAGE_NAME v$VERSION with Poetry..."
poetry build

if [ $? -eq 0 ]; then
    echo "✅ Build successful"

    echo "📥 Uninstalling previous version..."
    pip uninstall -y $PACKAGE_NAME

    echo "📥 Installing local wheel..."
    if pip install "dist/${PACKAGE_NAME//-/_}-$VERSION-py3-none-any.whl"; then
        echo "✅ Installation completed for $PACKAGE_NAME v$VERSION"
    else
        echo "❌ Installation failed"
        exit 1
    fi
else
    echo "❌ Build failed"
    exit 1
fi
