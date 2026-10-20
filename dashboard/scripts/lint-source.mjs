import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const roots = ["app", "components", "lib", "scripts"];
const sourceExtensions = new Set([".ts", ".tsx", ".js", ".jsx", ".mjs"]);
const failures = [];
let checked = 0;

async function visit(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name);
    if (entry.isDirectory()) await visit(file);
    else if (sourceExtensions.has(path.extname(entry.name))) await inspect(file);
  }
}

async function inspect(file) {
  const source = await readFile(file, "utf8");
  checked += 1;
  const relative = path.relative(root, file).replaceAll(path.sep, "/");
  const lines = source.split(/\r?\n/);
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    if (/[\t ]+$/.test(line)) failures.push(`${relative}:${lineNumber}: trailing whitespace`);
    if (/\bdebugger\s*;/.test(line)) failures.push(`${relative}:${lineNumber}: remove debugger statement`);
    if (/\bconsole\.log\s*\(/.test(line)) failures.push(`${relative}:${lineNumber}: remove console.log`);
    if (/\b[A-Z]:\\/.test(line)) failures.push(`${relative}:${lineNumber}: do not hardcode an absolute Windows path`);
  });
}

for (const directory of roots) await visit(path.join(root, directory));
if (failures.length) {
  console.error(failures.join("\n"));
  process.exitCode = 1;
} else {
  process.stdout.write(`Source hygiene passed for ${checked} TypeScript/JavaScript files.\n`);
}
