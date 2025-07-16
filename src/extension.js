const vscode = require('vscode');
const path = require('path');
const fs = require('fs');
const os = require('os');

async function copyRecursive(src, dest) {
  await fs.promises.mkdir(dest, { recursive: true });
  const entries = await fs.promises.readdir(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      await copyRecursive(srcPath, destPath);
    } else {
      await fs.promises.copyFile(srcPath, destPath);
    }
  }
}

async function createTemplate() {
  const docs = path.join(os.homedir(), 'Documents');
  const target = path.join(docs, 'dtk-template');
  const template = path.join(__dirname, '..', 'tools', 'dtk-template');

  try {
    await fs.promises.access(target);
    vscode.window.showInformationMessage('dtk-template already exists in Documents.');
  } catch {
    await copyRecursive(template, target);
  }

  await vscode.commands.executeCommand('vscode.openFolder', vscode.Uri.file(target), false);
  vscode.window.showInformationMessage(`Created dtk-template at ${target}`);
  vscode.commands.executeCommand('workbench.action.openWalkthrough', 'daitk.welcome');
}

function showGettingStarted() {
  const docPath = path.join(__dirname, '..', 'dtk-docs', 'getting_started.md');
  vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(docPath));
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand('daitk.createTemplate', createTemplate),
    vscode.commands.registerCommand('daitk.showGettingStarted', showGettingStarted)
  );
}

function deactivate() {}

module.exports = {
  activate,
  deactivate
};
