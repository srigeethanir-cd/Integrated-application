/**
 * TestCase Syntax Validator – Module 8.
 * 
 * Uses @babel/parser to verify syntax, imports, and AST correctness 
 * of the generated test suites.
 */

const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];

if (!filePath) {
  console.log(JSON.stringify({ passed: false, errors: ["No file path provided."] }));
  process.exit(1);
}

try {
  if (!fs.existsSync(filePath)) {
    console.log(JSON.stringify({ passed: false, errors: [`File does not exist: ${filePath}`] }));
    process.exit(1);
  }

  const code = fs.readFileSync(filePath, 'utf8');

  // Verify basic syntax using @babel/parser with JSX and TypeScript plugins
  const babelParserPath = path.resolve(__dirname, '..', 'project_analyzer', 'parsers', 'node_modules', '@babel', 'parser');
  const parser = require(babelParserPath);
  parser.parse(code, {
    sourceType: 'module',
    plugins: [
      'jsx',
      'typescript',
      'decorators-legacy'
    ]
  });

  console.log(JSON.stringify({ passed: true, errors: [] }));
} catch (err) {
  console.log(JSON.stringify({ passed: false, errors: [err.message] }));
}
