/**
 * Test runner for the VS Code extension.
 */

import * as path from 'path';
import * as os from 'os';
import { execSync } from 'child_process';
import { runTests } from '@vscode/test-electron';

/** Convert a Windows long path to its 8.3 short form to avoid space issues. */
function toShortPath(p: string): string {
    if (process.platform !== 'win32') { return p; }
    try {
        return execSync(`cmd /c for %I in ("${p}") do @echo %~sI`, { encoding: 'utf-8' }).trim();
    } catch {
        return p;
    }
}

async function main(): Promise<void> {
    const extensionDevelopmentPath = toShortPath(path.resolve(__dirname, '../../'));
    const extensionTestsPath = toShortPath(path.resolve(__dirname, './suite/index'));

    const testDir = path.join(os.tmpdir(), 'vscode-ext-test');

    await runTests({
        extensionDevelopmentPath,
        extensionTestsPath,
        launchArgs: [
            '--user-data-dir',
            path.join(testDir, 'user-data'),
            '--extensions-dir',
            path.join(testDir, 'extensions'),
            '--disable-gpu-sandbox',
            '--disable-workspace-trust',
        ],
    });
}

main().catch((err) => {
    console.error('Failed to run tests:', err);
    process.exit(1);
});
