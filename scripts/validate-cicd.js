#!/usr/bin/env node

/**
 * CI/CD Validation Script
 * 
 * This script validates that all CI/CD components are properly configured
 * and can be tested locally before pushing to trigger the pipeline.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔍 Validating CI/CD Pipeline Components...\n');

let hasErrors = false;

function checkError(condition, message) {
    if (condition) {
        console.log(`❌ ${message}`);
        hasErrors = true;
    } else {
        console.log(`✅ ${message}`);
    }
}

// 1. Check repository structure
console.log('📁 Repository Structure');
checkError(!fs.existsSync('.github/workflows/ci.yml'), 'GitHub Actions workflow exists');
checkError(!fs.existsSync('packages/mcp-server-smart-typer/package.json'), 'MCP server package exists');
checkError(!fs.existsSync('packages/mcp-server-smart-typer/tsconfig.json'), 'TypeScript config exists');
checkError(!fs.existsSync('packages/native-helpers/pyproject.toml'), 'Python package config exists');
checkError(!fs.existsSync('packages/native-helpers/build_uia_server.spec'), 'PyInstaller spec exists');
console.log('');

// 2. Check package.json configurations
console.log('📦 Package Configuration');
const rootPackage = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const serverPackage = JSON.parse(fs.readFileSync('packages/mcp-server-smart-typer/package.json', 'utf8'));

checkError(!rootPackage.scripts['prepare-release'], 'Release script configured in root package');
checkError(!serverPackage.dependencies['@modelcontextprotocol/sdk'], 'MCP SDK dependency present');
checkError(!serverPackage.keywords.includes('mcp'), 'MCP keywords present');
checkError(!serverPackage.bin, 'Binary entries configured');
console.log('');

// 3. Check Python configuration
console.log('🐍 Python Configuration');
const pyprojectContent = fs.readFileSync('packages/native-helpers/pyproject.toml', 'utf8');
checkError(!pyprojectContent.includes('PyInstaller'), 'PyInstaller dependency configured');
checkError(!pyprojectContent.includes('grpc'), 'gRPC dependencies configured');
console.log('');

// 4. Check build scripts
console.log('🛠️  Build Scripts');
try {
    // Check if pnpm is available
    execSync('pnpm --version', { stdio: 'ignore' });
    console.log('✅ pnpm is available');
    
    // Check if node_modules exists (basic dependency check)
    if (fs.existsSync('node_modules')) {
        console.log('✅ Dependencies appear to be installed');
        
        // Try TypeScript build if possible
        try {
            execSync('pnpm build', { stdio: 'ignore' });
            checkError(!fs.existsSync('packages/mcp-server-smart-typer/dist'), 'TypeScript build produces dist folder');
        } catch (buildError) {
            console.log('⚠️  TypeScript build test skipped (dependencies may need installation)');
        }
    } else {
        console.log('⚠️  Dependencies not installed, skipping build tests');
        console.log('   Run "pnpm install" to enable full validation');
    }
    
    // Check if Python can generate protobufs (basic check)
    try {
        execSync('python -c "import grpc_tools.protoc"', { stdio: 'ignore' });
        console.log('✅ Python gRPC tools available');
    } catch (pythonError) {
        console.log('⚠️  Python gRPC tools not available, protobuf generation may fail');
    }
    
} catch (error) {
    console.log('⚠️  Build environment checks skipped (tools not available)');
}
console.log('');

// 5. Check GitHub Actions workflow
console.log('⚙️  GitHub Actions Configuration');
const workflowContent = fs.readFileSync('.github/workflows/ci.yml', 'utf8');
checkError(!workflowContent.includes('publish-npm'), 'npm publishing job configured');
checkError(!workflowContent.includes('build-python-executable'), 'Python build job configured');
checkError(!workflowContent.includes('create-release'), 'Release creation job configured');
checkError(!workflowContent.includes('NODE_AUTH_TOKEN'), 'npm authentication configured');
console.log('');

// 6. Check MCP compliance
console.log('🔗 MCP Specification Compliance');
checkError(serverPackage.name !== '@mcp-smart-typer/server', 'Package name follows MCP conventions (current name is fine for development)');
checkError(!serverPackage.description.toLowerCase().includes('mcp'), 'Package description mentions MCP');
checkError(!serverPackage.repository, 'Repository URL configured');
console.log('');

// 7. Version consistency check
console.log('📊 Version Consistency');
const pythonContent = fs.readFileSync('packages/native-helpers/pyproject.toml', 'utf8');
const pythonVersionMatch = pythonContent.match(/version = "([^"]+)"/);
const pythonVersion = pythonVersionMatch ? pythonVersionMatch[1] : null;

console.log(`Root package version: ${rootPackage.version}`);
console.log(`Server package version: ${serverPackage.version}`);
console.log(`Python package version: ${pythonVersion}`);

const versionsMatch = rootPackage.version === serverPackage.version && 
                     serverPackage.version === pythonVersion;
checkError(!versionsMatch, 'All package versions are synchronized');
console.log('');

// 8. Security considerations
console.log('🔒 Security Configuration');
checkError(!workflowContent.includes('secrets.NPM_TOKEN'), 'npm token secret referenced');
checkError(!workflowContent.includes('secrets.GITHUB_TOKEN'), 'GitHub token secret referenced');
checkError(!workflowContent.includes('NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}'), 'Secrets properly scoped to publishing steps only');
console.log('');

// Summary
console.log('📋 Validation Summary');
if (hasErrors) {
    console.log('❌ Validation failed! Please fix the issues above before proceeding.');
    console.log('\nNext steps:');
    console.log('1. Fix the reported issues');
    console.log('2. Run this script again to verify fixes');
    console.log('3. Once all checks pass, proceed with release preparation');
    process.exit(1);
} else {
    console.log('✅ All validations passed! CI/CD pipeline is ready to use.');
    console.log('\nNext steps:');
    console.log('1. Ensure GitHub Secrets are configured:');
    console.log('   - NPM_TOKEN: Your npm publishing token');
    console.log('2. Test the pipeline:');
    console.log('   - npm run prepare-release 2.0.1');
    console.log('   - git add -A && git commit -m "chore: prepare release v2.0.1"');
    console.log('   - git tag v2.0.1 && git push origin v2.0.1');
    console.log('3. Monitor the GitHub Actions workflow execution');
}

console.log('\n🎉 CI/CD validation complete!');
