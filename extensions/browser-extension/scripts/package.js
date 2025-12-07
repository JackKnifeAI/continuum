#!/usr/bin/env node

/**
 * Package script for browser extension
 * Creates .zip files for store submission
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const browser = process.argv[2] || 'chrome';
const packageInfo = require('../package.json');
const version = packageInfo.version;

const distDir = path.join(__dirname, '..', 'dist', browser);
const packagesDir = path.join(__dirname, '..', 'packages');
const outputFile = path.join(packagesDir, `continuum-${browser}-v${version}.zip`);

// Ensure packages directory exists
if (!fs.existsSync(packagesDir)) {
  fs.mkdirSync(packagesDir, { recursive: true });
}

// Build first
console.log(`Building ${browser}...`);
execSync(`npm run build:${browser}`, { stdio: 'inherit' });

// Create zip
console.log(`Packaging ${browser}...`);
execSync(`cd ${distDir} && zip -r ${outputFile} .`, { stdio: 'inherit' });

console.log(`✅ Package created: ${outputFile}`);
console.log(`Size: ${(fs.statSync(outputFile).size / 1024).toFixed(2)} KB`);
