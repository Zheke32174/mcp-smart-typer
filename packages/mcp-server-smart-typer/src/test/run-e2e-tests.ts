/**
 * End-to-End Test Runner
 * Executes comprehensive test suite and generates detailed reports
 */

import { spawn } from 'child_process';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';

interface TestResult {
  name: string;
  duration: number;
  passed: number;
  failed: number;
  skipped: number;
  coverage?: {
    lines: number;
    functions: number;
    branches: number;
    statements: number;
  };
}

interface TestSuite {
  name: string;
  description: string;
  testFile: string;
  category: 'detection' | 'typing' | 'integration';
}

class E2ETestRunner {
  private testSuites: TestSuite[] = [
    {
      name: 'Field Detection',
      description: 'Tests field detection precision and accuracy with Playwright sample pages',
      testFile: 'src/test/e2e/field-detection.test.ts',
      category: 'detection'
    },
    {
      name: 'Typing Accuracy',
      description: 'Tests typing accuracy and performance across different scenarios',
      testFile: 'src/test/e2e/typing-accuracy.test.ts',
      category: 'typing'
    },
    {
      name: 'Notepad Integration',
      description: 'Tests integration with Windows Notepad application',
      testFile: 'src/test/e2e/notepad-integration.test.ts',
      category: 'integration'
    }
  ];

  private results: TestResult[] = [];
  private startTime: number = 0;
  private endTime: number = 0;

  async runAllTests(): Promise<void> {
    console.log('🚀 Starting comprehensive E2E test suite...');
    console.log('================================================');
    
    this.startTime = Date.now();

    // Ensure test directories exist
    this.setupTestEnvironment();

    // Run each test suite
    for (const suite of this.testSuites) {
      console.log(`\n📋 Running ${suite.name} tests...`);
      console.log(`   ${suite.description}`);
      
      try {
        const result = await this.runTestSuite(suite);
        this.results.push(result);
        this.logTestResult(result);
      } catch (error) {
        console.error(`❌ Failed to run ${suite.name}:`, error);
        this.results.push({
          name: suite.name,
          duration: 0,
          passed: 0,
          failed: 1,
          skipped: 0
        });
      }
    }

    this.endTime = Date.now();

    // Generate reports
    await this.generateReports();
    
    // Display summary
    this.displaySummary();
  }

  private setupTestEnvironment(): void {
    const directories = [
      './test-screenshots',
      './test-reports',
      './coverage'
    ];

    directories.forEach(dir => {
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
    });
  }

  private async runTestSuite(suite: TestSuite): Promise<TestResult> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const jestProcess = spawn('npx', [
        'jest',
        suite.testFile,
        '--verbose',
        '--coverage',
        '--json',
        '--outputFile',
        `./test-reports/${suite.name.toLowerCase().replace(/\s+/g, '-')}-results.json`
      ], {
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true
      });

      let stdout = '';
      let stderr = '';

      jestProcess.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      jestProcess.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      jestProcess.on('close', (code) => {
        const duration = Date.now() - startTime;
        
        try {
          // Parse Jest output to extract results
          const result = this.parseJestOutput(stdout, stderr, suite.name, duration);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      jestProcess.on('error', (error) => {
        reject(error);
      });
    });
  }

  private parseJestOutput(stdout: string, stderr: string, suiteName: string, duration: number): TestResult {
    // Parse Jest output - this is a simplified parser
    // In real implementation, you'd parse the JSON output more thoroughly
    
    const passedMatch = stdout.match(/(\d+) passing/);
    const failedMatch = stdout.match(/(\d+) failing/);
    const skippedMatch = stdout.match(/(\d+) pending/);

    return {
      name: suiteName,
      duration,
      passed: passedMatch ? parseInt(passedMatch[1]) : 0,
      failed: failedMatch ? parseInt(failedMatch[1]) : 0,
      skipped: skippedMatch ? parseInt(skippedMatch[1]) : 0,
      coverage: this.extractCoverageInfo(stdout)
    };
  }

  private extractCoverageInfo(output: string): TestResult['coverage'] {
    // Extract coverage information from Jest output
    const coverageMatch = output.match(/All files\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)\s+\|\s+([\d.]+)/);
    
    if (coverageMatch) {
      return {
        statements: parseFloat(coverageMatch[1]),
        branches: parseFloat(coverageMatch[2]),
        functions: parseFloat(coverageMatch[3]),
        lines: parseFloat(coverageMatch[4])
      };
    }

    return undefined;
  }

  private logTestResult(result: TestResult): void {
    const status = result.failed === 0 ? '✅' : '❌';
    const duration = (result.duration / 1000).toFixed(1);
    
    console.log(`${status} ${result.name}: ${result.passed} passed, ${result.failed} failed, ${result.skipped} skipped (${duration}s)`);
    
    if (result.coverage) {
      console.log(`   📊 Coverage: ${result.coverage.lines}% lines, ${result.coverage.functions}% functions`);
    }
  }

  private async generateReports(): Promise<void> {
    console.log('\n📄 Generating test reports...');

    // Generate JSON report
    const jsonReport = {
      timestamp: new Date().toISOString(),
      totalDuration: this.endTime - this.startTime,
      summary: {
        totalTests: this.results.reduce((sum, r) => sum + r.passed + r.failed + r.skipped, 0),
        totalPassed: this.results.reduce((sum, r) => sum + r.passed, 0),
        totalFailed: this.results.reduce((sum, r) => sum + r.failed, 0),
        totalSkipped: this.results.reduce((sum, r) => sum + r.skipped, 0),
        overallSuccess: this.results.every(r => r.failed === 0)
      },
      testSuites: this.results,
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch
      }
    };

    writeFileSync('./test-reports/e2e-test-results.json', JSON.stringify(jsonReport, null, 2));

    // Generate HTML report
    await this.generateHtmlReport(jsonReport);

    // Generate markdown report
    await this.generateMarkdownReport(jsonReport);

    console.log('✅ Reports generated in ./test-reports/');
  }

  private async generateHtmlReport(report: any): Promise<void> {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Smart Typer E2E Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
        .metric h3 { margin: 0 0 10px 0; color: #333; }
        .metric .value { font-size: 24px; font-weight: bold; }
        .passed { color: #28a745; }
        .failed { color: #dc3545; }
        .skipped { color: #ffc107; }
        .test-suite { border: 1px solid #dee2e6; border-radius: 6px; margin-bottom: 20px; }
        .suite-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #dee2e6; }
        .suite-content { padding: 15px; }
        .status-badge { padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }
        .status-success { background-color: #28a745; }
        .status-failed { background-color: #dc3545; }
        .coverage-bar { background: #f8f9fa; height: 20px; border-radius: 10px; overflow: hidden; margin-top: 5px; }
        .coverage-fill { height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 MCP Smart Typer E2E Test Results</h1>
            <p>Generated on ${new Date(report.timestamp).toLocaleString()}</p>
            <p>Total Duration: ${(report.totalDuration / 1000 / 60).toFixed(1)} minutes</p>
        </div>

        <div class="summary">
            <div class="metric">
                <h3>Total Tests</h3>
                <div class="value">${report.summary.totalTests}</div>
            </div>
            <div class="metric">
                <h3>Passed</h3>
                <div class="value passed">${report.summary.totalPassed}</div>
            </div>
            <div class="metric">
                <h3>Failed</h3>
                <div class="value failed">${report.summary.totalFailed}</div>
            </div>
            <div class="metric">
                <h3>Skipped</h3>
                <div class="value skipped">${report.summary.totalSkipped}</div>
            </div>
            <div class="metric">
                <h3>Success Rate</h3>
                <div class="value ${report.summary.overallSuccess ? 'passed' : 'failed'}">
                    ${((report.summary.totalPassed / report.summary.totalTests) * 100).toFixed(1)}%
                </div>
            </div>
        </div>

        ${report.testSuites.map((suite: any) => `
            <div class="test-suite">
                <div class="suite-header">
                    <h3>${suite.name} 
                        <span class="status-badge ${suite.failed === 0 ? 'status-success' : 'status-failed'}">
                            ${suite.failed === 0 ? 'PASSED' : 'FAILED'}
                        </span>
                    </h3>
                    <p>Duration: ${(suite.duration / 1000).toFixed(1)}s | 
                       Passed: ${suite.passed} | 
                       Failed: ${suite.failed} | 
                       Skipped: ${suite.skipped}</p>
                </div>
                <div class="suite-content">
                    ${suite.coverage ? `
                        <h4>Code Coverage</h4>
                        <div>
                            Lines: ${suite.coverage.lines}%
                            <div class="coverage-bar">
                                <div class="coverage-fill" style="width: ${suite.coverage.lines}%"></div>
                            </div>
                        </div>
                        <div>
                            Functions: ${suite.coverage.functions}%
                            <div class="coverage-bar">
                                <div class="coverage-fill" style="width: ${suite.coverage.functions}%"></div>
                            </div>
                        </div>
                    ` : '<p>No coverage data available</p>'}
                </div>
            </div>
        `).join('')}

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d;">
            <p>Generated by MCP Smart Typer E2E Test Runner</p>
        </div>
    </div>
</body>
</html>`;

    writeFileSync('./test-reports/e2e-test-results.html', html);
  }

  private async generateMarkdownReport(report: any): Promise<void> {
    const markdown = `# MCP Smart Typer E2E Test Results

**Generated:** ${new Date(report.timestamp).toLocaleString()}  
**Total Duration:** ${(report.totalDuration / 1000 / 60).toFixed(1)} minutes  
**Overall Status:** ${report.summary.overallSuccess ? '✅ PASSED' : '❌ FAILED'}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | ${report.summary.totalTests} |
| Passed | ${report.summary.totalPassed} |
| Failed | ${report.summary.totalFailed} |
| Skipped | ${report.summary.totalSkipped} |
| Success Rate | ${((report.summary.totalPassed / report.summary.totalTests) * 100).toFixed(1)}% |

## Test Suites

${report.testSuites.map((suite: any) => `
### ${suite.name} ${suite.failed === 0 ? '✅' : '❌'}

- **Duration:** ${(suite.duration / 1000).toFixed(1)}s
- **Results:** ${suite.passed} passed, ${suite.failed} failed, ${suite.skipped} skipped
${suite.coverage ? `- **Coverage:** ${suite.coverage.lines}% lines, ${suite.coverage.functions}% functions` : '- **Coverage:** Not available'}

`).join('')}

## Environment

- **Node.js:** ${report.environment.nodeVersion}
- **Platform:** ${report.environment.platform}
- **Architecture:** ${report.environment.arch}

---

*Generated by MCP Smart Typer E2E Test Runner*
`;

    writeFileSync('./test-reports/e2e-test-results.md', markdown);
  }

  private displaySummary(): void {
    console.log('\n🎯 Test Execution Summary');
    console.log('========================');
    
    const totalTests = this.results.reduce((sum, r) => sum + r.passed + r.failed + r.skipped, 0);
    const totalPassed = this.results.reduce((sum, r) => sum + r.passed, 0);
    const totalFailed = this.results.reduce((sum, r) => sum + r.failed, 0);
    const totalSkipped = this.results.reduce((sum, r) => sum + r.skipped, 0);
    const successRate = ((totalPassed / totalTests) * 100).toFixed(1);
    const totalDuration = (this.endTime - this.startTime) / 1000;

    console.log(`📊 Total Tests: ${totalTests}`);
    console.log(`✅ Passed: ${totalPassed}`);
    console.log(`❌ Failed: ${totalFailed}`);
    console.log(`⏭️  Skipped: ${totalSkipped}`);
    console.log(`🎯 Success Rate: ${successRate}%`);
    console.log(`⏱️  Total Duration: ${totalDuration.toFixed(1)}s`);

    if (totalFailed === 0) {
      console.log('\n🎉 All tests passed successfully!');
    } else {
      console.log('\n⚠️  Some tests failed. Check the detailed reports for more information.');
    }

    console.log('\n📁 Reports generated:');
    console.log('   - ./test-reports/e2e-test-results.json');
    console.log('   - ./test-reports/e2e-test-results.html');
    console.log('   - ./test-reports/e2e-test-results.md');
  }
}

// Run the tests if this file is executed directly
if (require.main === module) {
  const runner = new E2ETestRunner();
  runner.runAllTests().catch(console.error);
}

export { E2ETestRunner };
