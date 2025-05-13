"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
function activate(context) {
    console.log('Python Profiler extension is now active!');
    let disposable = vscode.commands.registerCommand('python-profiler-viewer.showProfilerData', async () => {
        let selectedFilePath;
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            selectedFilePath = editor.document.uri.fsPath;
        }
        else {
            const pickedFile = await vscode.window.showOpenDialog({
                canSelectMany: false,
                filters: {
                    'Supported Files': ['py', 'class'],
                    'All Files': ['*']
                }
            });
            if (!pickedFile || pickedFile.length === 0) {
                vscode.window.showErrorMessage('No file selected.');
                return;
            }
            selectedFilePath = pickedFile[0].fsPath;
        }
        const fileExtension = path.extname(selectedFilePath);
        const fileNameOnly = path.basename(selectedFilePath, fileExtension);
        const directory = path.dirname(selectedFilePath);
        let profilerScript;
        let profilerArgs;
        if (fileExtension === '.py') {
            profilerScript = path.join(context.extensionPath, 'universal_profiler.py');
            profilerArgs = [profilerScript, selectedFilePath];
        }
        else if (fileExtension === '.class') {
            profilerScript = path.join(context.extensionPath, 'java_files', 'python_java.py');
            profilerArgs = [profilerScript, '--class', fileNameOnly];
        }
        else {
            vscode.window.showErrorMessage('Unsupported file type. Only .py and .class are supported.');
            return;
        }
        const realtimeJsonPath = path.join(directory, 'realtime_monitor.json');
        const statsJsonPath = path.join(directory, 'function_statistics.json');
        const realtimePanel = vscode.window.createWebviewPanel('profilerRealtimeView', 'Profiler - Realtime Monitor', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        const realtimeHtmlPath = vscode.Uri.file(path.join(context.extensionPath, 'src', 'realtimeView.html'));
        const realtimeHtmlContent = fs.readFileSync(realtimeHtmlPath.fsPath, 'utf8');
        realtimePanel.webview.html = realtimeHtmlContent;
        if (!fs.existsSync(realtimeJsonPath)) {
            fs.writeFileSync(realtimeJsonPath, '{}', 'utf8');
        }
        let realtimeWatcher;
        try {
            realtimeWatcher = fs.watch(realtimeJsonPath, async (eventType) => {
                if (eventType === 'change') {
                    try {
                        const data = fs.readFileSync(realtimeJsonPath, 'utf8');
                        if (data.trim() === '')
                            return;
                        try {
                            const jsonData = JSON.parse(data);
                            realtimePanel.webview.postMessage({
                                command: 'updateData',
                                data: jsonData
                            });
                        }
                        catch (parseError) {
                            console.error('Error parsing JSON:', parseError);
                        }
                    }
                    catch (err) {
                        console.error('Error reading realtime JSON:', err);
                    }
                }
            });
        }
        catch (err) {
            console.error('Error setting up file watcher:', err);
            vscode.window.showErrorMessage('Failed to set up real-time monitoring');
        }
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: "Running profiler...",
            cancellable: false
        }, async () => {
            return new Promise((resolve, reject) => {
                const process = (0, child_process_1.spawn)('python', profilerArgs, {
                    cwd: directory
                });
                process.on('close', async (code) => {
                    realtimeWatcher.close();
                    if (code !== 0) {
                        vscode.window.showErrorMessage('Profiler script failed.');
                        reject();
                        return;
                    }
                    let retries = 0;
                    const maxRetries = 10;
                    const checkFile = () => {
                        if (fs.existsSync(statsJsonPath)) {
                            const data = JSON.parse(fs.readFileSync(statsJsonPath, 'utf8'));
                            showFinalStatsView(data);
                            resolve();
                        }
                        else {
                            retries++;
                            if (retries > maxRetries) {
                                vscode.window.showErrorMessage('Profiler output JSON not found after waiting.');
                                reject();
                                return;
                            }
                            setTimeout(checkFile, 500);
                        }
                    };
                    checkFile();
                });
            });
        });
        realtimePanel.onDidDispose(() => {
            if (realtimeWatcher)
                realtimeWatcher.close();
        });
    });
    context.subscriptions.push(disposable);
}
function showFinalStatsView(data) {
    const panel = vscode.window.createWebviewPanel('profilerStatsView', 'Python Profiler - Final Statistics', vscode.ViewColumn.One, { enableScripts: true });
    panel.webview.html = getWebviewContent(data);
}
// ... keep the existing getWebviewContent function ...
function getWebviewContent(data) {
    let rows = '';
    let functionNames = [];
    let avgCpuUsages = [];
    let avgMemUsages = [];
    let totalTimes = [];
    for (const [funcName, stats] of Object.entries(data)) {
        const s = stats;
        const [programName, functionName, lineNumber] = funcName.split(":");
        rows += `
            <tr>
               <td>${programName}</td>
               <td>${functionName}</td>
                <td>${lineNumber}</td>
                <td>${s.calls}</td>
                <td>${s.total_time.toFixed(3)} sec</td>
                <td>${s.avg_cpu.toFixed(2)} %</td>
                <td>${s.avg_mem.toFixed(2)} MB</td>
            </tr>
        `;
        functionNames.push(functionName);
        avgCpuUsages.push(s.avg_cpu);
        avgMemUsages.push(s.avg_mem);
        totalTimes.push(s.total_time);
    }
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Profiler Data</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

            // <style>
            //     body { font-family: sans-serif; padding: 20px; }
            //     table { width: 100%; border-collapse: collapse; }
            //     th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
            //     th { background-color: #f4f4f4; }
            //     tr:nth-child(even) { background-color: #f9f9f9; }
            //     tr:hover { background-color: #f1f1f1; }
            // </style>
            <style>
    body { 
        font-family: 'Arial', sans-serif; 
        padding: 20px; 
        background-color: #f0f0f0; 
        margin: 0;
    }

    h1 {
        font-size: 24px;
        color: #333;
        margin-bottom: 20px;
    }
    h2 {
        font-size: 20px;
        color: #D84040;
        margin-bottom: 10px;
    }
    h3 {
        font-size: 20px;
        color: #4F1C51;
        margin-bottom: 10px;
    }

    table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 20px;
        background-color: #fff;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }

    th, td { 
        border: 1px solid #ddd; 
        padding: 12px 16px; 
        text-align: center; 
        font-size: 14px;
    }

    th { 
        background-color: #4CAF50; 
        color: white; 
        font-weight: bold; 
    }

    tr:nth-child(even) { 
        background-color: #f9f9f9; 
    }

    tr:hover { 
        background-color: #f1f1f1; 
        cursor: pointer;
    }

    td {
        color: #555;
    }

    .highlight {
        background-color: #ffecb3 !important;
        font-weight: bold;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        th, td { 
            font-size: 12px;
            padding: 10px;
        }

        body {
            padding: 10px;
        }

        table {
            font-size: 12px;
        }
    }
</style>

        </head>
        <body>
            <h2 >Python Profiler Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>File Name</th>
                        <th>Function Name</th>
                        <th>Line Number</th>
                        <th>Calls Made</th>
                        <th>Cummulative Execution Time</th>
                        <th>Avg CPU Usage</th>
                        <th>Avg Memory Usage</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
            
 <h2 style="text-align: center; margin-bottom: 30px;">Graphs</h2>

<div style="display: flex; flex-direction: column; align-items: center; gap: 40px; padding: 20px;">

    <div style="background: #fff; padding: 20px; box-shadow: 0px 0px 10px #ccc; border-radius: 10px; width: 80%; max-width: 800px;">
        <h3 style="text-align: center; margin-bottom: 20px;">Avg CPU Usage by Function</h3>
        <center><div style="height: 250px; width: 100%;">
            <canvas id="cpuChart"></canvas>
        </div></center>
    </div>

    <div style="background: #fff; padding: 20px; box-shadow: 0px 0px 10px #ccc; border-radius: 10px; width: 80%; max-width: 800px;">
        <h3 style="text-align: center; margin-bottom: 20px;">Avg Memory Usage by Function</h3>
        <center><div style="height: 250px; width: 100%;">
            <canvas id="memChart"></canvas>
        </div></center>
    </div>

    <div style="background: #fff; padding: 20px; box-shadow: 0px 0px 10px #ccc; border-radius: 10px; width: 80%; max-width: 800px;">
        <h3 style="text-align: center; margin-bottom: 20px;">Total Time by Function</h3>
       <center> <div style="height: 250px; width: 100%;">
            <canvas id="timeChart"></canvas>
        </div></center>
    </div>

</div>



    </div>
    </div>

         <script>
                const functionNames = ${JSON.stringify(functionNames)};
                const avgCpuUsages = ${JSON.stringify(avgCpuUsages)};
                const avgMemUsages = ${JSON.stringify(avgMemUsages)};
                const totalTimes = ${JSON.stringify(totalTimes)};

                const cpuCtx = document.getElementById('cpuChart').getContext('2d');
                new Chart(cpuCtx, {
                    type: 'bar',
                    data: {
                        labels: functionNames,
                        datasets: [{
                            label: 'Avg CPU Usage (%)',
                            data: avgCpuUsages,
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'CPU Usage (%)' }
                            },
                            x: {
                                title: { display: true, text: 'Function Name' }
                            }
                        }
                    }
                });

                const memCtx = document.getElementById('memChart').getContext('2d');
                new Chart(memCtx, {
                    type: 'bar',
                    data: {
                        labels: functionNames,
                        datasets: [{
                            label: 'Avg Memory Usage (MB)',
                            data: avgMemUsages,
                            backgroundColor: 'rgba(255, 159, 64, 0.6)',
                            borderColor: 'rgba(255, 159, 64, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'Memory (MB)' }
                            },
                            x: {
                                title: { display: true, text: 'Function Name' }
                            }
                        }
                    }
                });

                const timeCtx = document.getElementById('timeChart').getContext('2d');
                new Chart(timeCtx, {
                    type: 'bar',
                    data: {
                        labels: functionNames,
                        datasets: [{
                            label: 'Total Time (sec)',
                            data: totalTimes,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: { display: true, text: 'Time (sec)' }
                            },
                            x: {
                                title: { display: true, text: 'Function Name' }
                            }
                        }
                    }
                });
            </script>
        </body>
        </html>
    `;
}
function deactivate() { }
//# sourceMappingURL=extension.js.map