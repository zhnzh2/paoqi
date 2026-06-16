/**
 * 扫描 paoqi 项目根目录的 core/ Python 模块，
 * 生成 TypeScript 文件，将所有 .py 文件内容内联为字符串映射表，
 * 供 Pyodide 浏览器引擎加载使用。
 *
 * 用法：node web/frontend/scripts/bundleCoreModules.js
 *
 * 路径探测：
 *   本地开发：core/ 在 ../../../core/（相对于 web/frontend/scripts/）
 *   Railway 构建：core/ 不在构建上下文中，使用已提交的 coreModules.ts
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUTPUT_FILE = path.join(__dirname, "..", "src", "engine", "coreModules.ts");

/**
 * 探测 core/ 目录位置。按优先级尝试多个可能路径。
 */
function findCoreDir() {
  const candidates = [
    // 本地开发：从 web/frontend/scripts/ 向上三级到项目根目录
    path.resolve(__dirname, "..", "..", "..", "core"),
    // 如果当前工作目录是项目根目录
    path.resolve(process.cwd(), "core"),
    // 如果当前工作目录是 web/frontend
    path.resolve(process.cwd(), "..", "..", "..", "core"),
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      return candidate;
    }
  }

  return null;
}

function collectPythonFiles(dir) {
  const results = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "__pycache__") {
        continue;
      }
      results.push(...collectPythonFiles(fullPath));
    } else if (entry.name.endsWith(".py")) {
      results.push(fullPath);
    }
  }

  return results;
}

function buildModulesMap(coreDir) {
  const allFiles = collectPythonFiles(coreDir);

  const lines = [];
  lines.push("// 自动生成的文件，请勿手动编辑。");
  lines.push("// 由 scripts/bundleCoreModules.js 生成。");
  lines.push("// 包含 core/ 目录下所有 .py 模块的内容。");
  lines.push("");
  lines.push("const CORE_MODULES: Record<string, string> = {");

  for (const filePath of allFiles.sort()) {
    const relativePath = path.relative(coreDir, filePath).replace(/\\/g, "/");
    const content = fs.readFileSync(filePath, "utf-8");

    // 模板字符串转义：反斜杠、反引号、美元符号
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

// ===================== 主流程 =====================

const coreDir = findCoreDir();

if (coreDir) {
  // 找到了 core/ —— 重新生成
  const output = buildModulesMap(coreDir);
  fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
  fs.writeFileSync(OUTPUT_FILE, output, "utf-8");

  const moduleCount = Object.keys(
    Object.fromEntries(
      output
        .split("\n")
        .filter((l) => l.trim().startsWith('"'))
        .map((l) => [l, true])
    )
  ).length;

  console.log(`✅ 已生成 ${OUTPUT_FILE}`);
  console.log(`   包含 ${moduleCount} 个 Python 模块`);
} else if (fs.existsSync(OUTPUT_FILE)) {
  // 找不到 core/ 但输出文件已存在（如 Railway 构建环境）—— 保留已有文件
  console.log(`⚠️  未找到 core/ 目录，使用已有的 coreModules.ts`);
  console.log(`   （如需更新，请在本地运行 npm run bundle-core）`);
} else {
  // 既找不到 core/ 也没有已有文件 —— 致命错误
  console.error(`❌ 未找到 core/ 目录，且 ${OUTPUT_FILE} 不存在。`);
  console.error(`   请确保 core/ 目录存在，或在本地先运行 npm run bundle-core 生成该文件。`);
  process.exit(1);
}
