/**
 * 扫描 paoqi 项目根目录的 core/ Python 模块，
 * 生成 TypeScript 文件，将所有 .py 文件内容内联为字符串映射表，
 * 供 Pyodide 浏览器引擎加载使用。
 *
 * 用法：node web/frontend/scripts/bundleCoreModules.js
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");
const CORE_DIR = path.join(PROJECT_ROOT, "core");
const GAME_IMPL_DIR = path.join(CORE_DIR, "game_impl");
const OUTPUT_FILE = path.join(__dirname, "..", "src", "engine", "coreModules.ts");

function collectPythonFiles(dir, baseDir) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      // Include __pycache__ directories? No - skip them
      if (entry.name === "__pycache__") {
        continue;
      }
      results.push(...collectPythonFiles(fullPath, baseDir));
    } else if (entry.name.endsWith(".py")) {
      results.push(fullPath);
    }
  }

  return results;
}

function buildModulesMap() {
  const allFiles = [
    ...collectPythonFiles(CORE_DIR, CORE_DIR),
  ];

  const lines = [];
  lines.push("// 自动生成的文件，请勿手动编辑。");
  lines.push("// 由 scripts/bundleCoreModules.js 生成。");
  lines.push("// 包含 core/ 目录下所有 .py 模块的内容。");
  lines.push("");
  lines.push("const CORE_MODULES: Record<string, string> = {");

  for (const filePath of allFiles.sort()) {
    const relativePath = path.relative(CORE_DIR, filePath).replace(/\\/g, "/");
    const content = fs.readFileSync(filePath, "utf-8");

    // 使用模板字符串转义：反引号、美元符号、反斜杠
    const escaped = content
      .replace(/\\/g, "\\\\")
      .replace(/`/g, "\\`")
      .replace(/\$/g, "\\$");

    lines.push(`  "${relativePath}": \`${escaped}\`,`);
  }

  lines.push("};");
  lines.push("");
  lines.push("export default CORE_MODULES;");
  lines.push("");

  return lines.join("\n");
}

const output = buildModulesMap();
fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
fs.writeFileSync(OUTPUT_FILE, output, "utf-8");

console.log(`✅ 已生成 ${OUTPUT_FILE}`);
console.log(`   包含 ${output.split("\n").filter(l => l.trim().startsWith('"')).length} 个 Python 模块`);
