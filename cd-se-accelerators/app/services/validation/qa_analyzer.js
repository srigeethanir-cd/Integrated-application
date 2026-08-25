/**
 * Static QA Analyzer – Module 9.
 * 
 * Performs AST static analysis on test files to check for syntax correctness,
 * verify imports, count test cases, check assertions, detect unused imports,
 * and ensure cleanup hooks (afterEach/cleanup) are present.
 */

const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];

if (!filePath) {
  console.log(JSON.stringify({ compiled: false, errors: ["No file path provided."] }));
  process.exit(1);
}

try {
  if (!fs.existsSync(filePath)) {
    console.log(JSON.stringify({ compiled: false, errors: [`File does not exist: ${filePath}`] }));
    process.exit(1);
  }

  const code = fs.readFileSync(filePath, 'utf8');

  // Load @babel/parser dynamically
  const babelParserPath = path.resolve(__dirname, '..', 'project_analyzer', 'parsers', 'node_modules', '@babel', 'parser');
  const babelParser = require(babelParserPath);

  const ast = babelParser.parse(code, {
    sourceType: 'module',
    plugins: [
      'jsx',
      'typescript',
      'decorators-legacy'
    ]
  });

  const report = {
    compiled: true,
    test_cases: [],
    errors: [],
    warnings: [],
    has_cleanup: false,
    has_assertions: true,
    unused_imports: [],
    invalid_assertions_count: 0
  };

  const imports = [];
  let expectCallsCount = 0;
  let itCallsCount = 0;

  function traverse(node) {
    if (!node) return;

    // Check ImportDeclaration
    if (node.type === 'ImportDeclaration') {
      node.specifiers.forEach(spec => {
        imports.push({
          name: spec.local.name
        });
      });
    }

    // Check CallExpressions
    if (node.type === 'CallExpression') {
      if (node.callee.type === 'Identifier') {
        const name = node.callee.name;
        if (name === 'it' || name === 'test') {
          itCallsCount++;
          if (node.arguments.length > 0 && node.arguments[0].type === 'StringLiteral') {
            report.test_cases.push(node.arguments[0].value);
          }
        }
        if (name === 'afterEach' || name === 'cleanup' || name === 'fixture.destroy') {
          report.has_cleanup = true;
        }
        if (name === 'expect') {
          expectCallsCount++;
        }
      }
    }

    // Traverse children
    for (const key in node) {
      if (node[key] && typeof node[key] === 'object') {
        if (Array.isArray(node[key])) {
          node[key].forEach(child => {
            if (child && child.type) {
              traverse(child);
            }
          });
        } else if (node[key].type) {
          traverse(node[key]);
        }
      }
    }
  }

  traverse(ast.program);

  // Check unused imports
  imports.forEach(imp => {
    // If the count of occurrences in the code of the import name is <= 1 (only the import itself), it's unused.
    const regex = new RegExp(`\\b${imp.name}\\b`, 'g');
    const matches = code.match(regex);
    if (matches && matches.length <= 1) {
      report.unused_imports.push(imp.name);
    }
  });

  if (itCallsCount > 0 && expectCallsCount === 0) {
    report.has_assertions = false;
    report.invalid_assertions_count = itCallsCount;
  } else {
    report.has_assertions = true;
  }

  console.log(JSON.stringify(report));
} catch (err) {
  console.log(JSON.stringify({ compiled: false, errors: [err.message] }));
}
