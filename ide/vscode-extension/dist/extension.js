"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
function activate(context) {
    const provider = new DaitkSidebarProvider(context);
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('daitkActions', provider));
}
exports.activate = activate;
function deactivate() { }
exports.deactivate = deactivate;
class DaitkSidebarProvider {
    constructor(context) {
        this.context = context;
    }
    resolveWebviewView(webviewView) {
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this.getHtml();
        webviewView.webview.onDidReceiveMessage((message) => {
            switch (message.command) {
                case 'newProject':
                    vscode.window.showInformationMessage('Create new project');
                    break;
                case 'importProject':
                    vscode.window.showInformationMessage('Import project');
                    break;
                case 'openDoc':
                    vscode.window.showInformationMessage(`Open documentation: ${message.doc}`);
                    break;
            }
        });
    }
    getHtml() {
        return `
      <style>
        .section { font-weight: bold; margin-top: 1em; }
        .button {
          display: block; width: 100%; margin: 0.5em 0; padding: 0.7em;
          background: #007acc; color: white; border: none; border-radius: 4px;
          font-size: 1em; cursor: pointer;
        }
        .button:hover { background: #005fa3; }
        .version { margin-top: 2em; color: #888; font-size: 0.9em; }
        .doc-link { display: block; margin: 0.3em 0; color: #007acc; text-decoration: underline; cursor: pointer; }
      </style>
      <div>
        <div class="section">Actions</div>
        <button class="button" onclick="vscode.postMessage({ command: 'newProject' })">New Project</button>
        <button class="button" onclick="vscode.postMessage({ command: 'importProject' })">Import Project</button>
        <div class="section">Documentation</div>
        <a class="doc-link" onclick="vscode.postMessage({ command: 'openDoc', doc: 'getting_started' })">Getting Started</a>
        <a class="doc-link" onclick="vscode.postMessage({ command: 'openDoc', doc: 'api_reference' })">API Reference</a>
        <div class="version">daitk: 1.0.0</div>
      </div>
      <script>
        const vscode = acquireVsCodeApi();
      </script>
    `;
    }
}
//# sourceMappingURL=extension.js.map