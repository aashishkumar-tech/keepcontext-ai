/**
 * Webview panel for displaying rich agent workflow results.
 */

import * as vscode from 'vscode';
import type { AgentResponse } from './types';

export class AgentResultPanel {
    public static readonly viewType = 'keepcontext.agentResult';
    private static currentPanel: AgentResultPanel | undefined;

    private constructor(
        private readonly panel: vscode.WebviewPanel,
        private readonly extensionUri: vscode.Uri,
    ) {
        this.panel.onDidDispose(() => {
            AgentResultPanel.currentPanel = undefined;
        });
    }

    /** Show (or re-use) the agent result panel. */
    static show(
        extensionUri: vscode.Uri,
        result: AgentResponse,
    ): void {
        const column = vscode.window.activeTextEditor
            ? vscode.ViewColumn.Beside
            : vscode.ViewColumn.One;

        if (AgentResultPanel.currentPanel) {
            AgentResultPanel.currentPanel.panel.reveal(column);
            AgentResultPanel.currentPanel.update(result);
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            AgentResultPanel.viewType,
            '🤖 Agent Result',
            column,
            { enableScripts: false },
        );

        AgentResultPanel.currentPanel = new AgentResultPanel(panel, extensionUri);
        AgentResultPanel.currentPanel.update(result);
    }

    private update(result: AgentResponse): void {
        this.panel.title = `Agent: ${result.goal.substring(0, 40)}`;
        this.panel.webview.html = this.buildHtml(result);
    }

    private buildHtml(result: AgentResponse): string {
        const planHtml = result.plan
            ? `<section>
                <h2>📋 Plan</h2>
                <ol>${result.plan.steps
                    .map((s) => `<li><strong>${escapeHtml(s.description)}</strong><br/><small>${escapeHtml(s.details)}</small></li>`)
                    .join('')}</ol>
                ${result.plan.architecture_notes ? `<blockquote>${escapeHtml(result.plan.architecture_notes)}</blockquote>` : ''}
               </section>`
            : '';

        const codeHtml =
            result.code_outputs.length > 0
                ? `<section>
                    <h2>💻 Generated Code</h2>
                    ${result.code_outputs
                        .map(
                            (c) =>
                                `<div class="code-block">
                                    <h3>${escapeHtml(c.filename)}</h3>
                                    <pre><code>${escapeHtml(c.code)}</code></pre>
                                    <p class="explanation">${escapeHtml(c.explanation)}</p>
                                 </div>`,
                        )
                        .join('')}
                   </section>`
                : '';

        const reviewHtml = result.review
            ? `<section>
                <h2>🔍 Review: ${result.review.approved ? '✅ Approved' : '❌ Needs Revision'}</h2>
                <p>${escapeHtml(result.review.summary)}</p>
                ${result.review.issues.length > 0
                    ? `<ul>${result.review.issues
                          .map((i) => `<li><span class="severity-${i.severity}">[${i.severity}]</span> ${escapeHtml(i.description)}</li>`)
                          .join('')}</ul>`
                    : ''}
               </section>`
            : '';

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Agent Result</title>
    <style>
        body {
            font-family: var(--vscode-font-family, system-ui);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            padding: 16px;
            line-height: 1.6;
        }
        h1 { color: var(--vscode-textLink-foreground); }
        h2 { margin-top: 24px; border-bottom: 1px solid var(--vscode-widget-border); padding-bottom: 4px; }
        pre {
            background: var(--vscode-textBlockQuote-background);
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 13px;
        }
        code { font-family: var(--vscode-editor-font-family, monospace); }
        blockquote {
            border-left: 3px solid var(--vscode-textLink-foreground);
            padding-left: 12px;
            margin-left: 0;
            opacity: 0.85;
        }
        .meta { opacity: 0.7; font-size: 0.9em; }
        .code-block { margin-bottom: 20px; }
        .explanation { font-style: italic; opacity: 0.8; }
        .severity-critical { color: var(--vscode-errorForeground); font-weight: bold; }
        .severity-warning { color: var(--vscode-editorWarning-foreground); }
        .severity-suggestion { opacity: 0.8; }
    </style>
</head>
<body>
    <h1>🤖 KeepContext Agent</h1>
    <p><strong>Goal:</strong> ${escapeHtml(result.goal)}</p>
    <p class="meta">Iterations: ${result.iterations_used}</p>
    ${planHtml}
    ${codeHtml}
    ${reviewHtml}
</body>
</html>`;
    }
}

function escapeHtml(text: string): string {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
