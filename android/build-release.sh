#!/bin/bash
# APKビルドスクリプト

set -e

echo "=========================================="
echo "ChArUco Tracking - APK Build Script"
echo "=========================================="
echo ""

# Check if we're in the android directory
if [ ! -f "build.gradle.kts" ]; then
    echo "Error: Please run this script from the android/ directory"
    exit 1
fi

# Check if keystore.properties exists
if [ ! -f "keystore.properties" ]; then
    echo "Warning: keystore.properties not found"
    echo "Building unsigned debug APK..."
    echo ""

    # Build debug APK
    ./gradlew assembleDebug

    echo ""
    echo "=========================================="
    echo "Build completed!"
    echo "Debug APK location:"
    echo "  app/build/outputs/apk/debug/app-debug.apk"
    echo ""
    echo "To create a signed release APK:"
    echo "  1. Create keystore: see BUILD_RELEASE.md"
    echo "  2. Create keystore.properties"
    echo "  3. Run this script again"
    echo "=========================================="
else
    echo "Building signed release APK..."
    echo ""

    # Build release APK
    ./gradlew assembleRelease

    echo ""
    echo "=========================================="
    echo "Build completed!"
    echo "Release APK location:"
    echo "  app/build/outputs/apk/release/app-release.apk"
    echo ""
    echo "Install with:"
    echo "  adb install app/build/outputs/apk/release/app-release.apk"
    echo "=========================================="
fi
