import * as vscode from 'vscode';
import { execFile } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {
  let disposable = vscode.commands.registerCommand('extension.runComplexityChecker', async () => {
    const folderUri = await vscode.window.showOpenDialog({
      canSelectFolders: true,
      canSelectFiles: false,
      canSelectMany: false,
      openLabel: 'Select Folder to Analyze'
    });

    if (!folderUri || folderUri.length === 0) {
      vscode.window.showWarningMessage('No folder selected.');
      return;
    }

    const folderPath = folderUri[0].fsPath;
    const pythonScript = path.join(context.extensionPath, 'scripts', 'complexity_checker.py');
    const outputJson = path.join(folderPath, 'complexity_report.json');

    vscode.window.withProgress({
      location: vscode.ProgressLocation.Notification,
      title: "Running Complexity Checker...",
      cancellable: false
    }, async () => {
      return new Promise<void>((resolve, reject) => {
        execFile('python', [pythonScript, folderPath], (error, stdout, stderr) => {
          if (error) {
            vscode.window.showErrorMessage(`Error: ${stderr || error.message}`);
            reject();
            return;
          }

          vscode.window.showInformationMessage('Analysis complete!');

          let htmlContent = '';
          let jsonData = '';
          try {
            const htmlPath = path.join(context.extensionPath, 'media', 'webview.html');
            htmlContent = fs.readFileSync(htmlPath, 'utf8');
            jsonData = fs.readFileSync(outputJson, 'utf8');

            // Log the parsed JSON to the developer console
            const parsedData = JSON.parse(jsonData);
            console.log('Complexity Report:', parsedData);
          } catch (readErr) {
            let msg = 'Could not read report files.';
            if (readErr instanceof Error) {
              msg += ' ' + readErr.message;
            }
            vscode.window.showErrorMessage(msg);
            resolve();
            return;
          }

          htmlContent = htmlContent.replace('/*__DATA__*/', `const data = ${jsonData};`);

          setTimeout(() => {
            const panel = vscode.window.createWebviewPanel(
              'complexityView',
              'Python Complexity Report',
              vscode.ViewColumn.One,
              { enableScripts: true }
            );
            panel.webview.html = htmlContent;
          }, 100);

          resolve();
        });
      });
    });
  });

  context.subscriptions.push(disposable);
}
