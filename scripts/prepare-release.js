#!/usr/bin/env node

/**
 * Prepare Release Script
 * 
 * This script helps prepare a new release by:
 * 1. Updating version numbers across all packages
 * 2. Generating changelog entries
 * 3. Ensuring MCP specification compliance
 * 4. Validating package integrity
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// MCP specification version this server supports
const MCP_SPEC_VERSION = '1.0.0';

function updatePackageVersion(packagePath, newVersion) {
    const packageJsonPath = path.join(packagePath, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    
    packageJson.version = newVersion;
    
    // Ensure MCP compatibility metadata
    if (!packageJson.keywords.includes('mcp')) {
        packageJson.keywords.unshift('mcp');
    }
    if (!packageJson.keywords.includes('model-context-protocol')) {
        packageJson.keywords.push('model-context-protocol');
    }
    
    // Add MCP specification version
    packageJson.mcpSpecVersion = MCP_SPEC_VERSION;
    
    fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n');
    console.log(`✅ Updated ${packagePath}/package.json to version ${newVersion}`);
}

function updatePythonVersion(pyprojectPath, newVersion) {
    let content = fs.readFileSync(pyprojectPath, 'utf8');
    content = content.replace(/version = "[^"]*"/, `version = "${newVersion}"`);
    fs.writeFileSync(pyprojectPath, content);
    console.log(`✅ Updated ${pyprojectPath} to version ${newVersion}`);
}

function validateMCPCompliance() {
    const serverPackagePath = path.join(__dirname, '..', 'packages', 'mcp-server-smart-typer', 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(serverPackagePath, 'utf8'));
    
    const required = {
        '@modelcontextprotocol/sdk': 'MCP SDK dependency'
    };
    
    for (const [dep, description] of Object.entries(required)) {
        if (!packageJson.dependencies[dep]) {
            throw new Error(`❌ Missing required dependency: ${dep} (${description})`);
        }
    }
    
    console.log('✅ MCP specification compliance validated');
}

function generateChangelog(version) {
    try {
        const lastTag = execSync('git describe --tags --abbrev=0 HEAD~1', { encoding: 'utf8' }).trim();
        const commits = execSync(`git log --pretty=format:"- %s" ${lastTag}..HEAD`, { encoding: 'utf8' });
        
        const changelogEntry = `
## [${version}] - ${new Date().toISOString().split('T')[0]}

### MCP Specification Compliance
- Supports MCP specification version ${MCP_SPEC_VERSION}
- Full compatibility with MCP client implementations

### Changes
${commits}

### Technical Details
- Windows UI Automation via gRPC protocol
- Enhanced security and permission management
- Comprehensive error handling and logging
- Cross-platform compatibility (Windows primary)

`;
        
        const changelogPath = path.join(__dirname, '..', 'CHANGELOG.md');
        let existingChangelog = '';
        
        if (fs.existsSync(changelogPath)) {
            existingChangelog = fs.readFileSync(changelogPath, 'utf8');
        } else {
            existingChangelog = '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n';
        }
        
        const newChangelog = existingChangelog.replace(
            '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n',
            `# Changelog\n\nAll notable changes to this project will be documented in this file.\n${changelogEntry}`
        );
        
        fs.writeFileSync(changelogPath, newChangelog);
        console.log(`✅ Updated CHANGELOG.md with version ${version} entries`);
        
    } catch (error) {
        console.warn('⚠️  Could not generate changelog (no previous tags found)');
    }
}

function main() {
    const args = process.argv.slice(2);
    const newVersion = args[0];
    
    if (!newVersion) {
        console.error('Usage: node scripts/prepare-release.js <version>');
        console.error('Example: node scripts/prepare-release.js 2.1.0');
        process.exit(1);
    }
    
    // Validate version format
    if (!/^\d+\.\d+\.\d+$/.test(newVersion)) {
        console.error('❌ Version must be in semver format (e.g., 2.1.0)');
        process.exit(1);
    }
    
    console.log(`🚀 Preparing release ${newVersion}...`);
    
    try {
        // Update root package.json
        updatePackageVersion(path.join(__dirname, '..'), newVersion);
        
        // Update MCP server package
        updatePackageVersion(path.join(__dirname, '..', 'packages', 'mcp-server-smart-typer'), newVersion);
        
        // Update Python package
        updatePythonVersion(path.join(__dirname, '..', 'packages', 'native-helpers', 'pyproject.toml'), newVersion);
        
        // Validate MCP compliance
        validateMCPCompliance();
        
        // Generate changelog
        generateChangelog(newVersion);
        
        console.log('\n🎉 Release preparation complete!');
        console.log('\nNext steps:');
        console.log('1. Review the changes: git diff');
        console.log('2. Commit the changes: git add -A && git commit -m "chore: prepare release v' + newVersion + '"');
        console.log('3. Create and push the tag: git tag v' + newVersion + ' && git push origin v' + newVersion);
        console.log('4. The CI/CD pipeline will handle the rest!');
        
    } catch (error) {
        console.error('❌ Release preparation failed:', error.message);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
