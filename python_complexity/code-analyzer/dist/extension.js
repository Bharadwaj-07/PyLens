/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ([
/* 0 */
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {


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
Object.defineProperty(exports, "__esModule", ({ value: true }));
exports.activate = activate;
const vscode = __importStar(__webpack_require__(1));
const child_process_1 = __webpack_require__(2);
const path = __importStar(__webpack_require__(3));
const fs = __importStar(__webpack_require__(4));
function activate(context) {
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
            return new Promise((resolve, reject) => {
                (0, child_process_1.execFile)('python', [pythonScript, folderPath], (error, stdout, stderr) => {
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
                    }
                    catch (readErr) {
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
                        const panel = vscode.window.createWebviewPanel('complexityView', 'Python Complexity Report', vscode.ViewColumn.One, { enableScripts: true });
                        panel.webview.html = htmlContent;
                    }, 100);
                    resolve();
                });
            });
        });
    });
    context.subscriptions.push(disposable);
}


/***/ }),
/* 1 */
/***/ ((module) => {

module.exports = require("vscode");

/***/ }),
/* 2 */
/***/ ((module) => {

module.exports = require("child_process");

/***/ }),
/* 3 */
/***/ ((module) => {

module.exports = require("path");

/***/ }),
/* 4 */
/***/ ((module) => {

module.exports = require("fs");

/***/ })
/******/ 	]);
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module is referenced by other modules so it can't be inlined
/******/ 	var __webpack_exports__ = __webpack_require__(0);
/******/ 	module.exports = __webpack_exports__;
/******/ 	
/******/ })()
;
//# sourceMappingURL=extension.js.map