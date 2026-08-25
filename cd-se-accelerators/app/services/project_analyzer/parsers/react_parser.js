/**
 * React Parser – Node.js script invoked via subprocess from Python.
 *
 * Uses @babel/parser to generate ASTs and @babel/traverse to walk them.
 * Extracts (v2 enriched): components, props, state (+ state_type/used_in/updated_by),
 *   hooks (+ is_custom/params/return_values), JSX elements (+ id/class_name/role/aria-*
 *   placeholder/alt/disabled/required/value_binding/event_bindings),
 *   event_handlers (+ element/updates_state/service_calls/navigation/prevent_default/stop_propagation),
 *   API calls (+ endpoint/http_method/is_async/has_error_handling/in_use_effect),
 *   forms, routing_info, context_usage, accessibility, testing_metadata, dependency_graph,
 *   component_relationships, test_mapping.
 *
 * Usage:  node react_parser.js <absolute_project_path>
 * Output: JSON on stdout matching the ReactAnalysisResult Pydantic schema.
 * Errors: Written to stderr with non-zero exit code.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const babelParser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

// -------------------------------------------------------------------------
// Configuration
// -------------------------------------------------------------------------

const SOURCE_EXTENSIONS = new Set([".js", ".jsx", ".ts", ".tsx"]);
const TEST_PATTERNS = [/\.test\.[jt]sx?$/, /\.spec\.[jt]sx?$/, /__tests__/];
const EXCLUDED_DIRS = new Set(["node_modules", "dist", "build", ".git", "coverage", ".next"]);

const BABEL_PLUGINS = [
  "jsx",
  "typescript",
  "classProperties",
  "classPrivateProperties",
  "classPrivateMethods",
  "decorators-legacy",
  "dynamicImport",
  "optionalChaining",
  "nullishCoalescingOperator",
  "exportDefaultFrom",
  "exportNamespaceFrom",
  "optionalCatchBinding",
];

// -------------------------------------------------------------------------
// File discovery
// -------------------------------------------------------------------------

function walkDir(dir, fileList = []) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return fileList;
  }
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!EXCLUDED_DIRS.has(entry.name)) {
        walkDir(fullPath, fileList);
      }
    } else if (entry.isFile() && SOURCE_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

function isTestFile(filePath) {
  return TEST_PATTERNS.some((p) => p.test(filePath));
}

// -------------------------------------------------------------------------
// AST helpers
// -------------------------------------------------------------------------

function parseFile(filePath) {
  const code = fs.readFileSync(filePath, "utf-8");
  return babelParser.parse(code, {
    sourceType: "module",
    plugins: BABEL_PLUGINS,
    errorRecovery: true,
  });
}

function getNodeName(node) {
  if (!node) return null;
  if (node.type === "Identifier") return node.name;
  if (node.type === "MemberExpression") {
    const obj = getNodeName(node.object);
    const prop = getNodeName(node.property);
    return obj && prop ? `${obj}.${prop}` : prop || obj;
  }
  return null;
}

// -------------------------------------------------------------------------
// New semantic enrichment helpers (v2)
// -------------------------------------------------------------------------

/**
 * Extract a printable string value from a JSX attribute value node.
 * Returns the raw string for StringLiteral, a source-text approximation
 * for JSXExpressionContainer, or 'true' for a boolean (absent value) attr.
 */
function extractJsxAttrValue(jsxAttr) {
  if (!jsxAttr) return null;
  const val = jsxAttr.value;
  if (!val) return "true"; // boolean attribute, e.g. <input disabled />
  if (val.type === "StringLiteral") return val.value;
  if (val.type === "JSXExpressionContainer") {
    const expr = val.expression;
    if (!expr || expr.type === "JSXEmptyExpression") return null;
    return sourceOf(expr) || "{expr}";
  }
  return null;
}

/**
 * Recursively walk an AST node and collect all CallExpression nodes.
 * Avoids traversing into comment / location data.
 */
function findCallsInNode(node, results) {
  if (!results) results = [];
  if (!node || typeof node !== "object") return results;
  if (node.type === "CallExpression") results.push(node);
  const SKIP = new Set(["type", "start", "end", "loc", "extra",
    "leadingComments", "trailingComments", "innerComments"]);
  for (const key of Object.keys(node)) {
    if (SKIP.has(key)) continue;
    const child = node[key];
    if (Array.isArray(child)) {
      for (const c of child) { if (c && c.type) findCallsInNode(c, results); }
    } else if (child && typeof child === "object" && child.type) {
      findCallsInNode(child, results);
    }
  }
  return results;
}

/**
 * Recursively collect all Identifier names within an AST subtree.
 * Used to check whether a JSX attribute expression references a state variable.
 */
function findIdentifiersInNode(node, results) {
  if (!results) results = [];
  if (!node || typeof node !== "object") return results;
  if (node.type === "Identifier") { results.push(node.name); return results; }
  const SKIP = new Set(["type", "start", "end", "loc", "extra",
    "leadingComments", "trailingComments", "innerComments"]);
  for (const key of Object.keys(node)) {
    if (SKIP.has(key)) continue;
    const child = node[key];
    if (Array.isArray(child)) {
      for (const c of child) { if (c && c.type) findIdentifiersInNode(c, results); }
    } else if (child && typeof child === "object" && child.type) {
      findIdentifiersInNode(child, results);
    }
  }
  return results;
}

/**
 * Infer a semantic type name from the initial_value source text.
 */
function inferStateType(initialValue) {
  if (!initialValue) return "unknown";
  if (initialValue === "true" || initialValue === "false") return "boolean";
  if (initialValue === "null") return "null";
  if (initialValue === "[]") return "array";
  if (initialValue === "{}") return "object";
  if (initialValue.startsWith("'") || initialValue.startsWith('"') || initialValue.startsWith("`")) return "string";
  if (!Number.isNaN(Number(initialValue))) return "number";
  return "unknown";
}

/** Native HTTP method patterns for axios / fetch call detection. */
const AXIOS_METHODS = new Set(["get", "post", "put", "delete", "patch", "head", "options"]);
const BUILTIN_HOOKS = new Set([
  "useState", "useEffect", "useMemo", "useCallback", "useRef",
  "useReducer", "useContext", "useLayoutEffect", "useDebugValue",
  "useImperativeHandle", "useId", "useDeferredValue", "useTransition",
  "useSyncExternalStore", "useInsertionEffect",
  // Redux / React-Query built-ins treated as built-in for hook classification
  "useSelector", "useDispatch", "useStore",
  "useQuery", "useMutation", "useLazyQuery", "useSubscription",
]);

/** Wrappers that contain a functional component as their first argument. */
const COMPONENT_WRAPPERS = new Set(["memo", "forwardRef"]);
const REACT_COMPONENT_WRAPPERS = new Set(["React.memo", "React.forwardRef"]);

/**
 * Analyse a handler expression node (arrow function body or call expression)
 * to determine which state setters it calls, which services, and DOM effects.
 *
 * @param {object} handlerNode  - AST node of the handler expression
 * @param {object} stateSetterMap - { setterName -> stateName }
 * @returns {{ updates_state, service_calls, navigation, prevent_default, stop_propagation }}
 */
function analyzeHandlerNode(handlerNode, stateSetterMap) {
  const result = {
    updates_state: [],
    service_calls: [],
    navigation: false,
    prevent_default: false,
    stop_propagation: false,
  };
  if (!handlerNode) return result;

  const calls = findCallsInNode(handlerNode);
  for (const call of calls) {
    const name = getNodeName(call.callee);
    if (!name) continue;

    // State setter
    if (stateSetterMap[name]) {
      const stateName = stateSetterMap[name];
      if (!result.updates_state.includes(stateName)) result.updates_state.push(stateName);
    }
    // Service / API call
    if (
      name === "fetch" || name.startsWith("axios") ||
      name.includes("Service") || name.includes("service") ||
      name.includes("api") || name.includes("Api")
    ) {
      if (!result.service_calls.includes(name)) result.service_calls.push(name);
    }
    // Navigation
    if (name === "navigate" || name.includes("push") || name.includes("replace") ||
        name.includes("history") || name.includes("router")) {
      result.navigation = true;
    }
    // DOM effects
    if (name.includes("preventDefault")) result.prevent_default = true;
    if (name.includes("stopPropagation")) result.stop_propagation = true;
  }
  return result;
}

/**
 * Check whether path p is inside a useEffect callback by walking ancestors.
 */
function isInsideUseEffect(p) {
  let cur = p.parentPath;
  while (cur) {
    if (
      cur.node.type === "CallExpression" &&
      getNodeName(cur.node.callee) === "useEffect"
    ) return true;
    cur = cur.parentPath;
  }
  return false;
}

/**
 * Check whether path p is inside a try/catch block by walking ancestors.
 */
function isInsideTryCatch(p) {
  let cur = p.parentPath;
  while (cur) {
    if (cur.node.type === "TryStatement") return true;
    cur = cur.parentPath;
  }
  return false;
}

/**
 * Walk UP from a CallExpression path through chained .then()/.catch()/.finally()
 * member calls to detect whether a .catch() exists anywhere in the chain.
 * Covers patterns like: fetch(url).then(fn).catch(fn)
 */
function hasCatchInChain(p) {
  // Walk upward through MemberExpression → CallExpression pairs
  let cur = p.parentPath;
  let depth = 0;
  while (cur && depth < 10) {
    const n = cur.node;
    // We are inside a .something() call — check if .catch or .finally
    if (n.type === "MemberExpression" && n.property) {
      const propName = n.property.name || n.property.value;
      if (propName === "catch" || propName === "finally") return true;
    }
    // Only continue upward through MemberExpression → CallExpression chains
    if (n.type !== "MemberExpression" && n.type !== "CallExpression") break;
    cur = cur.parentPath;
    depth++;
  }
  return false;
}

/**
 * Check whether path p is inside an async function by walking ancestors.
 */
function isInsideAsyncFn(p) {
  let cur = p.parentPath;
  while (cur) {
    const n = cur.node;
    if (
      (n.type === "FunctionDeclaration" || n.type === "ArrowFunctionExpression" ||
       n.type === "FunctionExpression") && n.async
    ) return true;
    cur = cur.parentPath;
  }
  return false;
}

/**
 * Extract the first string-literal argument (endpoint URL) from a call node.
 */
function extractEndpoint(callNode) {
  if (!callNode.arguments || callNode.arguments.length === 0) return null;
  const first = callNode.arguments[0];
  if (first.type === "StringLiteral") return first.value;
  if (first.type === "TemplateLiteral" && first.quasis.length > 0) {
    return first.quasis[0].value.cooked || null; // first segment of template
  }
  return null;
}

/**
 * Infer HTTP method from an axios.METHOD call or fetch options object.
 */
function inferHttpMethod(calleeName, callNode) {
  // axios.get / axios.post / etc.
  if (calleeName && calleeName.includes(".")) {
    const parts = calleeName.split(".");
    const last = parts[parts.length - 1].toLowerCase();
    if (AXIOS_METHODS.has(last)) return last.toUpperCase();
  }
  // fetch(url, { method: 'POST' })
  if (callNode.arguments && callNode.arguments.length >= 2) {
    const opts = callNode.arguments[1];
    if (opts && opts.type === "ObjectExpression") {
      for (const prop of opts.properties) {
        if (
          prop.type === "ObjectProperty" &&
          prop.key && (prop.key.name || prop.key.value) === "method" &&
          prop.value && prop.value.type === "StringLiteral"
        ) {
          return prop.value.value.toUpperCase();
        }
      }
    }
  }
  // Default for bare fetch / axios calls
  if (calleeName === "fetch" || calleeName === "axios") return "GET";
  return null;
}

/**
 * Build a DependencyNode from a component's import list.
 * Heuristics:
 *  - imports from '.' or relative paths with capital start → component
 *  - imports containing 'Service', 'service', 'api', 'Api', 'client' → service
 *  - imports containing 'Context', 'context' → context
 *  - everything else → utility
 */
function buildDependencyNode(componentName, imports) {
  const node = {
    component: componentName,
    imports_components: [],
    imports_services: [],
    imports_utilities: [],
    imports_contexts: [],
    imports_hooks: [],
    imports_stores: [],
    imports_external_libraries: [],
  };
  for (const imp of imports) {
    const src = imp.source || "";
    const isExternal = !src.startsWith(".") && !src.startsWith("/");
    if (isExternal && !node.imports_external_libraries.includes(src)) {
      node.imports_external_libraries.push(src);
    }
    for (const spec of imp.specifiers || []) {
      const name = spec.replace(/^\* as /, "");
      if (!name) continue;
      if (/Service|service|Api|api|client|Client/.test(src) || /Service|service|Api|api/.test(name)) {
        if (!node.imports_services.includes(name)) node.imports_services.push(name);
      } else if (/[Cc]ontext/.test(src) || /[Cc]ontext/.test(name)) {
        if (!node.imports_contexts.includes(name)) node.imports_contexts.push(name);
      } else if (/^use[A-Z]/.test(name)) {
        if (!node.imports_hooks.includes(name)) node.imports_hooks.push(name);
      } else if (/[Ss]tore|[Rr]edux|[Zz]ustand|[Ss]lice/.test(src) || /[Ss]tore|[Rr]edux|[Zz]ustand/.test(name)) {
        if (!node.imports_stores.includes(name)) node.imports_stores.push(name);
      } else if (/^[A-Z]/.test(name) && (src.startsWith(".") || src.startsWith("/"))) {
        if (!node.imports_components.includes(name)) node.imports_components.push(name);
      } else {
        if (!node.imports_utilities.includes(name)) node.imports_utilities.push(name);
      }
    }
  }
  return node;
}

/**
 * Generate framework-agnostic testing metadata for one component.
 */
function buildTestingMetadata(comp) {
  const categories = ["Rendering"]; // always at minimum
  const testableElements = [];
  const interactiveElements = [];
  const mockDependencies = [];
  const recommendedQueries = [];
  const edgeCases = [];
  const negativeScenarios = [];
  const suggestedMocks = [];

  // Elements & Queries
  for (const el of comp.jsx_elements || []) {
    if (!testableElements.includes(el.tag)) testableElements.push(el.tag);
    if ((el.event_bindings && el.event_bindings.length > 0) ||
        (el.attributes && el.attributes.some((a) => /^on[A-Z]/.test(a)))) {
      if (!interactiveElements.includes(el.tag)) interactiveElements.push(el.tag);
    }

    if (el.role) {
      recommendedQueries.push({ query: "getByRole", target: el.tag, name: el.role });
    } else if (el.aria_label) {
      recommendedQueries.push({ query: "getByLabelText", target: el.tag, name: el.aria_label });
    } else if (el.placeholder) {
      recommendedQueries.push({ query: "getByPlaceholderText", target: el.tag, name: el.placeholder });
    } else if (el.alt) {
      recommendedQueries.push({ query: "getByAltText", target: el.tag, name: el.alt });
    } else if (el.id) {
      recommendedQueries.push({ query: "getByTestId", target: el.tag, name: el.id });
    }
  }

  // State
  if ((comp.state || []).length > 0) {
    categories.push("State");
    edgeCases.push("Initial state rendering with default values");
  }

  // Events
  if ((comp.event_handlers || []).length > 0) {
    categories.push("Events");
  }

  // Forms
  if ((comp.forms || []).length > 0) {
    categories.push("Forms");
    edgeCases.push("Form submission with empty or default input values");
    negativeScenarios.push("Submitting form with invalid fields triggers validation error message");
  }

  // API
  if ((comp.api_calls || []).length > 0) {
    categories.push("API");
    edgeCases.push("API network error handling (500/404 server response)");
    edgeCases.push("Loading state indicator rendering while API call is pending");
    negativeScenarios.push("Failed API call handles exception cleanly without crashing UI");
    for (const call of comp.api_calls) {
      if (!mockDependencies.includes(call.function_name)) {
        mockDependencies.push(call.function_name);
      }
      suggestedMocks.push({ name: call.function_name, type: call.type });
    }
  }

  // Accessibility
  if (comp.accessibility && (
    Object.keys(comp.accessibility.aria_attributes || {}).length > 0 ||
    (comp.accessibility.roles || []).length > 0 ||
    (comp.accessibility.keyboard_events || []).length > 0
  )) {
    categories.push("Accessibility");
    edgeCases.push("Keyboard navigation and focus management assertions");
  }

  // Routing
  if (comp.routing_info && (
    comp.routing_info.uses_navigate ||
    (comp.routing_info.links || []).length > 0 ||
    (comp.routing_info.routes || []).length > 0
  )) {
    categories.push("Routing");
    negativeScenarios.push("Unauthorized or missing route parameter navigation fallback");
  }

  // Context
  if ((comp.context_usage || []).length > 0) {
    categories.push("Context");
    for (const ctx of comp.context_usage) {
      suggestedMocks.push({ name: ctx.context_name, type: "context" });
    }
  }

  // Add custom hook mocks
  for (const hk of comp.hooks || []) {
    if (hk.is_custom && !mockDependencies.includes(hk.name)) {
      mockDependencies.push(hk.name);
      suggestedMocks.push({ name: hk.name, type: "hook" });
    }
  }

  return {
    testable_elements: testableElements,
    interactive_elements: interactiveElements,
    mock_dependencies: mockDependencies,
    recommended_test_categories: categories,
    recommended_queries: recommendedQueries,
    edge_cases: edgeCases,
    negative_scenarios: negativeScenarios,
    suggested_mocks: suggestedMocks,
  };
}

// -------------------------------------------------------------------------
// Component-level extraction
// -------------------------------------------------------------------------

function extractFromFile(filePath, projectRoot) {
  let ast;
  try {
    ast = parseFile(filePath);
  } catch (err) {
    process.stderr.write(`Warning: failed to parse ${filePath}: ${err.message}\n`);
    return null;
  }

  const relativePath = path.relative(projectRoot, filePath).replace(/\\/g, "/");
  const components = [];
  const imports = [];
  const exports = [];
  const topLevelFunctions = [];

  // Track seen data per component scope
  let currentComponent = null;

  // ---- Imports & Exports (file-level) ----
  traverse(ast, {
    ImportDeclaration(p) {
      const specifiers = p.node.specifiers.map((s) => {
        if (s.type === "ImportDefaultSpecifier") return s.local.name;
        if (s.type === "ImportNamespaceSpecifier") return `* as ${s.local.name}`;
        return s.imported ? s.imported.name : s.local.name;
      });
      const isDefault = p.node.specifiers.some((s) => s.type === "ImportDefaultSpecifier");
      imports.push({ source: p.node.source.value, specifiers, is_default: isDefault });
    },

    ExportDefaultDeclaration(p) {
      const decl = p.node.declaration;
      // Named function/class export: export default function Foo() { ... }
      if (decl.id) {
        exports.push({ name: decl.id.name, is_default: true });
      } else if (decl.name) {
        // export default Identifier
        exports.push({ name: decl.name, is_default: true });
      } else if (
        decl.type === "ArrowFunctionExpression" ||
        decl.type === "FunctionExpression"
      ) {
        // Anonymous export default () => <JSX />
        // Derive name from file path (PascalCase of filename)
        const fileName = path.basename(
          p.node.loc ? (p.hub && p.hub.file && p.hub.file.opts.filename) || "" : "",
          path.extname(""),
        );
        exports.push({ name: "default", is_default: true, anonymous_fn: decl });
      } else {
        exports.push({ name: "default", is_default: true });
      }
    },

    ExportNamedDeclaration(p) {
      if (p.node.declaration) {
        const decl = p.node.declaration;
        if (decl.id) {
          exports.push({ name: decl.id.name, is_default: false });
        } else if (decl.declarations) {
          for (const d of decl.declarations) {
            if (d.id && d.id.name) exports.push({ name: d.id.name, is_default: false });
          }
        }
      }
      if (p.node.specifiers) {
        for (const spec of p.node.specifiers) {
          const exportedName = spec.exported && (spec.exported.name || spec.exported.value);
          if (exportedName) exports.push({ name: exportedName, is_default: false });
        }
      }
    },
  });

  // ---- Component detection & deep extraction ----
  // Keep track of which declaration names have already been processed
  // so that ExportDefaultDeclaration doesn't double-count.
  const processedNames = new Set();

  traverse(ast, {
    // Functional component: function Foo() { return <JSX /> }
    FunctionDeclaration(p) {
      if (p.node.id && /^[A-Z]/.test(p.node.id.name) && !processedNames.has(p.node.id.name)) {
        processedNames.add(p.node.id.name);
        const comp = createComponent(p.node.id.name, "functional", relativePath, p, imports, exports);
        if (comp) components.push(comp);
      }
    },

    // Arrow/function expression component, plus memo() / forwardRef() wrappers
    VariableDeclarator(p) {
      if (!p.node.id || p.node.id.type !== "Identifier" || !p.node.init) return;
      const varName = p.node.id.name;
      if (!/^[A-Z]/.test(varName) || processedNames.has(varName)) return;

      const init = p.node.init;

      // Plain arrow / function expression: const Foo = () => { ... }
      if (init.type === "ArrowFunctionExpression" || init.type === "FunctionExpression") {
        processedNames.add(varName);
        const comp = createComponent(varName, "functional", relativePath, p, imports, exports);
        if (comp) components.push(comp);
        return;
      }

      // memo(Fn) / forwardRef(Fn) / React.memo(Fn) / React.forwardRef(Fn)
      if (init.type === "CallExpression" && init.arguments && init.arguments.length > 0) {
        const calleeName = getNodeName(init.callee);
        if (
          COMPONENT_WRAPPERS.has(calleeName) ||
          REACT_COMPONENT_WRAPPERS.has(calleeName)
        ) {
          processedNames.add(varName);
          const innerArg = init.arguments[0];

          // memo(function NamedFn() { ... }) — prefer the inner name if it's PascalCase
          let innerName = varName;
          if (
            (innerArg.type === "FunctionDeclaration" || innerArg.type === "FunctionExpression") &&
            innerArg.id && /^[A-Z]/.test(innerArg.id.name)
          ) {
            innerName = innerArg.id.name;
            if (!processedNames.has(innerName)) processedNames.add(innerName);
          }

          // Build a synthetic AST node so createAnonymousComponent can traverse
          const comp = createAnonymousComponent(innerName || varName, relativePath, innerArg, imports, exports);
          if (comp) {
            // Store under the variable name so parent-child linkage uses the right name
            comp.name = varName;
            components.push(comp);
          }
        }
      }
    },

    // Class component: class Foo extends React.Component
    ClassDeclaration(p) {
      if (p.node.id && isReactClassComponent(p.node) && !processedNames.has(p.node.id.name)) {
        processedNames.add(p.node.id.name);
        const comp = createClassComponent(p.node.id.name, relativePath, p, imports, exports);
        components.push(comp);
      }
    },

    // export default function() { return <JSX /> } — anonymous functional component
    ExportDefaultDeclaration(p) {
      const decl = p.node.declaration;
      if (
        (decl.type === "ArrowFunctionExpression" || decl.type === "FunctionExpression" ||
         decl.type === "FunctionDeclaration") &&
        !processedNames.has("default")
      ) {
        processedNames.add("default");
        // Derive a sensible component name from the file path
        const baseName = path.basename(relativePath).replace(/\.[jt]sx?$/, "");
        const compName = baseName.charAt(0).toUpperCase() + baseName.slice(1) || "Default";
        // Wrap the decl node in a fake path so createComponent can traverse it
        const comp = createAnonymousComponent(compName, relativePath, decl, imports, exports);
        if (comp) { processedNames.add(compName); components.push(comp); }
      }
    },
  });

  return { components, relativePath };
}

function isReactClassComponent(classNode) {
  if (!classNode.superClass) return false;
  const sc = classNode.superClass;
  if (sc.type === "Identifier" && (sc.name === "Component" || sc.name === "PureComponent")) return true;
  if (sc.type === "MemberExpression") {
    const objName = getNodeName(sc.object);
    const propName = getNodeName(sc.property);
    return objName === "React" && (propName === "Component" || propName === "PureComponent");
  }
  return false;
}

/**
 * Wrap an anonymous function node as a synthetic component path-like object
 * so we can reuse createComponent's traversal machinery.
 */
function createAnonymousComponent(name, filePath, fnNode, fileImports, fileExports) {
  // Build a synthetic AST + traverse for the function body
  const syntheticAst = babelParser.parse("", { sourceType: "module", plugins: BABEL_PLUGINS, errorRecovery: true });
  // Inject the function node as a top-level statement
  syntheticAst.program.body = [{ type: "ExpressionStatement", expression: fnNode }];
  // Create a fake path-like object with a traverse method
  let result = null;
  traverse(syntheticAst, {
    ExpressionStatement(p) {
      result = createComponentFromFnNode(name, filePath, p.get("expression"), fileImports, fileExports);
      p.stop();
    },
  });
  return result;
}

/**
 * Create a component from a raw function/arrow-function path.
 * Delegates to the same internal logic as createComponent.
 */
function createComponentFromFnNode(name, filePath, fnPath, fileImports, fileExports) {
  // Temporarily wrap in a VariableDeclarator-style path object
  return createComponentCore(name, "functional", filePath, fnPath, fileImports, fileExports);
}

function createComponent(name, type, filePath, componentPath, fileImports, fileExports) {
  // Compute the correct fnNode for prop extraction, then delegate to the core.
  const fnNode = componentPath.node.init || componentPath.node;
  return createComponentCore(name, type, filePath, componentPath, fileImports, fileExports, fnNode);
}

/**
 * Core implementation of component extraction — shared by createComponent
 * and createAnonymousComponent.
 */
function createComponentCore(name, type, filePath, componentPath, fileImports, fileExports, fnNodeOverride) {
  const props = [];
  const state = [];
  const hooks = [];
  const jsxElements = [];
  const eventHandlers = [];
  const functions = [];
  const apiCalls = [];
  const hookMap = {};
  const forms = [];
  const contextUsages = [];
  const conditionalRendering = [];

  // Enrichment tracking
  const stateSetterMap = {};   // setterName -> stateName
  const functionBodyNodes = {}; // funcName -> AST node (for handler cross-ref)
  const rawInputElements = []; // all input/select/textarea nodes before tag deduplication
  const routingInfo = {
    links: [], routes: [], uses_navigate: false, uses_router_push: false,
    route_params: [], redirects: [],
  };
  const ariaAttrs = {};        // aria-attrName -> value
  const accessRoles = [];      // role values
  const altTexts = [];         // alt values
  const keyboardEvents = [];   // keyboard event types
  let hasFocusMgmt = false;
  const labelAssociations = []; // htmlFor values
  const tagOccurrenceCounts = {}; // tagName -> running count for inline handler naming

  // Get the function body scope
  const fnNode = fnNodeOverride || componentPath.node.init || componentPath.node;

  // Walk the subtree
  componentPath.traverse({
    // ---- State, Hooks, API calls (CallExpression) ----
    CallExpression(p) {
      const callee = p.node.callee;
      const calleeName = getNodeName(callee);

      // --- useState detection (enriched) ---
      if (callee.type === "Identifier" && callee.name === "useState") {
        const parent = p.parentPath;
        if (parent.node.type === "VariableDeclarator" && parent.node.id.type === "ArrayPattern") {
          const elements = parent.node.id.elements;
          const stateName = elements[0] ? elements[0].name : "unknown";
          const setterName = elements[1] ? elements[1].name : "unknown";
          const initVal = p.node.arguments.length > 0 ? sourceOf(p.node.arguments[0]) : null;
          const stateEntry = {
            name: stateName,
            setter: setterName,
            initial_value: initVal,
            state_type: inferStateType(initVal),
            management_type: "useState",
            used_in: [],
            updated_by: [],
          };
          state.push(stateEntry);
          stateSetterMap[setterName] = stateName;
        }
      }

      // --- useReducer detection ---
      if (callee.type === "Identifier" && callee.name === "useReducer") {
        const par = p.parentPath;
        if (par && par.node.type === "VariableDeclarator" && par.node.id.type === "ArrayPattern") {
          const elements = par.node.id.elements;
          const stateName = elements[0] ? (getNodeName(elements[0]) || "state") : "state";
          const dispatchName = elements[1] ? (getNodeName(elements[1]) || "dispatch") : "dispatch";
          const initVal = p.node.arguments.length > 1 ? sourceOf(p.node.arguments[1]) : null;
          state.push({
            name: stateName,
            setter: dispatchName,
            initial_value: initVal,
            state_type: inferStateType(initVal),
            management_type: "useReducer",
            used_in: [],
            updated_by: [],
          });
          stateSetterMap[dispatchName] = stateName;
        }
      }

      // --- Hook detection (all use* calls, enriched) ---
      if (callee.type === "Identifier" && /^use[A-Z]/.test(callee.name)) {
        const hookName = callee.name;
        if (!hookMap[hookName]) {
          hookMap[hookName] = {
            name: hookName,
            count: 0,
            dependencies: [],
            is_custom: !BUILTIN_HOOKS.has(hookName),
            params: [],
            return_values: [],
          };
        }
        hookMap[hookName].count++;

        // Dependency array
        if (["useEffect", "useMemo", "useCallback"].includes(hookName)) {
          const lastArg = p.node.arguments[p.node.arguments.length - 1];
          if (lastArg && lastArg.type === "ArrayExpression") {
            for (const el of lastArg.elements) {
              if (el) {
                const depName = getNodeName(el);
                if (depName && !hookMap[hookName].dependencies.includes(depName)) {
                  hookMap[hookName].dependencies.push(depName);
                }
              }
            }
          }
        }

        // Custom hook: capture params (as source text)
        if (hookMap[hookName].is_custom) {
          hookMap[hookName].params = p.node.arguments.map((a) => sourceOf(a) || "?");
          // Capture return value destructuring from parent
          const par = p.parentPath;
          if (par && par.node.type === "VariableDeclarator") {
            const id = par.node.id;
            if (id.type === "ArrayPattern") {
              hookMap[hookName].return_values = id.elements
                .filter(Boolean)
                .map((e) => e.name || "?");
            } else if (id.type === "ObjectPattern") {
              hookMap[hookName].return_values = id.properties
                .filter((prop) => prop.key)
                .map((prop) => prop.key.name || "?");
            } else if (id.type === "Identifier") {
              hookMap[hookName].return_values = [id.name];
            }
          }
        }

        // Routing hooks
        if (hookName === "useNavigate" || hookName === "useHistory") {
          routingInfo.uses_navigate = true;
        }
        if (hookName === "useParams") {
          // Capture destructured param names
          const par = p.parentPath;
          if (par && par.node.type === "VariableDeclarator" && par.node.id.type === "ObjectPattern") {
            for (const prop of par.node.id.properties) {
              if (prop.key && !routingInfo.route_params.includes(prop.key.name)) {
                routingInfo.route_params.push(prop.key.name);
              }
            }
          }
        }

        // useContext detection
        if (hookName === "useContext" && p.node.arguments.length > 0) {
          const ctxName = getNodeName(p.node.arguments[0]) || "UnknownContext";
          const existing = contextUsages.find((c) => c.context_name === ctxName);
          if (!existing) {
            contextUsages.push({
              context_name: ctxName,
              is_provider: false,
              is_consumer: true,
              values_provided: [],
            });
          } else {
            existing.is_consumer = true;
          }
        }

        // Redux tracking: useSelector / useDispatch
        if (hookName === "useSelector") {
          const existing = contextUsages.find((c) => c.context_name === "ReduxStore");
          if (!existing) {
            contextUsages.push({
              context_name: "ReduxStore",
              is_provider: false,
              is_consumer: true,
              values_provided: [],
            });
          }
        }
        if (hookName === "useDispatch") {
          // Capture dispatch variable name and add it to stateSetterMap so
          // analyzeHandlerNode can resolve dispatch({type:...}) as a state update
          const par = p.parentPath;
          if (par && par.node.type === "VariableDeclarator" && par.node.id.type === "Identifier") {
            const dispatchVar = par.node.id.name;
            // Map dispatch -> any useReducer-derived state, or a sentinel
            if (!stateSetterMap[dispatchVar]) {
              stateSetterMap[dispatchVar] = "__redux_state";
            }
          }
          const existing = contextUsages.find((c) => c.context_name === "ReduxStore");
          if (!existing) {
            contextUsages.push({
              context_name: "ReduxStore",
              is_provider: false,
              is_consumer: true,
              values_provided: [],
            });
          }
        }

        // GraphQL hooks (Apollo, urql): useQuery / useMutation
        if (hookName === "useQuery" || hookName === "useMutation" ||
            hookName === "useLazyQuery" || hookName === "useSubscription") {
          const inUseEffect = isInsideUseEffect(p);
          const par = p.parentPath;
          // Capture destructured { data, loading, error } from return value
          let loadingVar = null;
          if (par && par.node.type === "VariableDeclarator" && par.node.id.type === "ObjectPattern") {
            for (const prop of par.node.id.properties) {
              if (prop.key && /loading|isLoading/i.test(prop.key.name || "")) {
                loadingVar = prop.key.name;
              }
            }
          }
          apiCalls.push({
            function_name: hookName,
            type: "graphql",
            endpoint: null,
            http_method: hookName === "useQuery" || hookName === "useLazyQuery" ? "GET" : "POST",
            is_async: true,
            has_error_handling: false,
            in_use_effect: inUseEffect,
            loading_state_var: loadingVar,
          });
        }
      }

      // --- API call detection (enriched) ---
      if (calleeName) {
        const isApi =
          calleeName === "fetch" ||
          calleeName.startsWith("axios") ||
          calleeName.includes("Service") ||
          calleeName.includes("service") ||
          calleeName.includes(".get") ||
          calleeName.includes(".post") ||
          calleeName.includes(".put") ||
          calleeName.includes(".delete") ||
          calleeName.includes(".patch") ||
          calleeName.includes("api") ||
          calleeName.includes("Api");

        if (isApi) {
          const callType =
            calleeName === "fetch" ? "fetch" :
            calleeName.startsWith("axios") ? "axios" : "service_call";

          // Enrichment
          const inUseEffect = isInsideUseEffect(p);
          const hasTryCatch = isInsideTryCatch(p);
          // Detect .catch() or .finally() anywhere in a promise chain
          const hasCatch = hasTryCatch || hasCatchInChain(p);

          // Find loading state heuristically
          let loadingVar = null;
          for (const s of state) {
            if (/loading|isLoading|fetching/i.test(s.name)) {
              loadingVar = s.name;
              break;
            }
          }

          apiCalls.push({
            function_name: calleeName,
            type: callType,
            endpoint: extractEndpoint(p.node),
            http_method: inferHttpMethod(calleeName, p.node),
            is_async: isInsideAsyncFn(p),
            has_error_handling: hasCatch,
            in_use_effect: inUseEffect,
            loading_state_var: loadingVar,
          });
        }

        // Track navigate() calls for routing
        if (calleeName === "navigate" || calleeName === "push" || calleeName === "replace") {
          routingInfo.uses_router_push = true;
          const firstArg = p.node.arguments[0];
          if (firstArg && firstArg.type === "StringLiteral") {
            if (!routingInfo.redirects.includes(firstArg.value)) {
              routingInfo.redirects.push(firstArg.value);
            }
          }
        }

        // Focus management
        if (calleeName.includes(".focus") || calleeName === "focus") {
          hasFocusMgmt = true;
        }
      }
    },

    // ---- JSX elements (enriched) ----
    JSXOpeningElement(p) {
      const tagName = getJsxTagName(p.node.name);
      const attrNames = [];
      const jsxEntry = {
        tag: tagName,
        attributes: attrNames,
        children_count: 0,
        // Enriched fields
        id: null,
        class_name: null,
        role: null,
        aria_label: null,
        aria_expanded: null,
        placeholder: null,
        alt: null,
        disabled: null,
        required: null,
        value_binding: null,
        event_bindings: [],
      };

      // Process every attribute
      for (const attr of p.node.attributes) {
        if (attr.type !== "JSXAttribute" || !attr.name) continue;

        // Get attribute name (handle JSXNamespacedName like aria-label)
        const attrName =
          attr.name.type === "JSXNamespacedName"
            ? `${attr.name.namespace.name}-${attr.name.name.name}`
            : attr.name.name;

        if (!attrName) continue;
        attrNames.push(attrName);

        const attrVal = extractJsxAttrValue(attr);

        // Standard attribute enrichment
        switch (attrName) {
          case "id":          jsxEntry.id = attrVal; break;
          case "className":   jsxEntry.class_name = attrVal; break;
          case "role":        jsxEntry.role = attrVal;
                              if (attrVal && !accessRoles.includes(attrVal)) accessRoles.push(attrVal);
                              break;
          case "aria-label":  jsxEntry.aria_label = attrVal;
                              ariaAttrs["aria-label"] = attrVal;
                              break;
          case "aria-expanded": jsxEntry.aria_expanded = attrVal;
                              ariaAttrs["aria-expanded"] = attrVal;
                              break;
          case "placeholder": jsxEntry.placeholder = attrVal; break;
          case "alt":         jsxEntry.alt = attrVal;
                              if (attrVal) altTexts.push(attrVal);
                              break;
          case "disabled":    jsxEntry.disabled = attrVal || "true"; break;
          case "required":    jsxEntry.required = attrVal || "true"; break;
          case "value":       jsxEntry.value_binding = attrVal; break;
          case "htmlFor":     if (attrVal) labelAssociations.push(attrVal); break;
          case "autoFocus":   hasFocusMgmt = true; break;
          // Store the raw type= value so field_type can use it later
          case "type":        jsxEntry._inputType = attrVal; break;
        }

        // Collect remaining aria-* attributes
        if (attrName.startsWith("aria-") && attrName !== "aria-label" && attrName !== "aria-expanded") {
          ariaAttrs[attrName] = attrVal;
        }

        // Event binding detection
        if (/^on[A-Z]/.test(attrName)) {
          // Keyboard events → accessibility
          if (/^onKey/.test(attrName) && !keyboardEvents.includes(attrName)) {
            keyboardEvents.push(attrName);
          }

          // Resolve handler name
          let handlerName = attrName;
          let handlerNode = null;

          if (attr.value && attr.value.type === "JSXExpressionContainer" && attr.value.expression) {
            const expr = attr.value.expression;
            const exprName = getNodeName(expr);
            if (exprName) {
              handlerName = exprName;
              // Inline arrow / call — keep the node for analysis
              handlerNode = expr;
            } else if (
              expr.type === "ArrowFunctionExpression" ||
              expr.type === "FunctionExpression"
            ) {
              // Disambiguate inline handlers per element type + occurrence index
              // e.g. onChange_input_0, onChange_input_1 for two separate inputs
              const occurrence = tagOccurrenceCounts[tagName] || 0;
              handlerName = `${attrName}_${tagName}_${occurrence}`;
              handlerNode = expr;
            } else {
              handlerNode = expr;
            }
          }

          // Record event binding on this JSX element
          jsxEntry.event_bindings.push({ event: attrName, handler: handlerName });

          // Enrich / create EventHandler entry
          const existingEH = eventHandlers.find(
            (eh) => eh.name === handlerName && eh.event_type === attrName
          );
          if (!existingEH) {
            const handlerAnalysis = analyzeHandlerNode(
              handlerNode || functionBodyNodes[handlerName],
              stateSetterMap
            );
            eventHandlers.push({
              name: handlerName,
              event_type: attrName,
              element: tagName,
              updates_state: handlerAnalysis.updates_state,
              service_calls: handlerAnalysis.service_calls,
              navigation: handlerAnalysis.navigation,
              prevent_default: handlerAnalysis.prevent_default,
              stop_propagation: handlerAnalysis.stop_propagation,
            });
          } else if (!existingEH.element) {
            existingEH.element = tagName;
          }
        }
      }

      // Children count
      const parentEl = p.parentPath.node;
      jsxEntry.children_count = parentEl && parentEl.children
        ? parentEl.children.filter((c) => c.type !== "JSXText" || c.value.trim()).length
        : 0;

      // Collect all form input entries prior to tag deduplication
      if (["input", "select", "textarea"].includes(tagName)) {
        rawInputElements.push(jsxEntry);
      }

      // Track per-tag occurrence count (for disambiguating inline handler names)
      tagOccurrenceCounts[tagName] = (tagOccurrenceCounts[tagName] || 0) + 1;

      // Deduplication by tag (backward compat) — keep first, merge event_bindings
      const existing = jsxElements.find((el) => el.tag === tagName);
      if (!existing) {
        jsxElements.push(jsxEntry);
      } else {
        // Merge event bindings from additional occurrences
        for (const eb of jsxEntry.event_bindings) {
          if (!existing.event_bindings.some((x) => x.event === eb.event && x.handler === eb.handler)) {
            existing.event_bindings.push(eb);
          }
        }
        // Merge attribute names
        for (const a of attrNames) {
          if (!existing.attributes.includes(a)) existing.attributes.push(a);
        }
      }

      // ---- Form detection ----
      if (tagName === "form") {
        const submitAttr = p.node.attributes.find((a) => a.name && a.name.name === "onSubmit");
        const resetAttr  = p.node.attributes.find((a) => a.name && a.name.name === "onReset");
        forms.push({
          element: "form",
          is_controlled: false, // refined in post-processing
          submit_handler: submitAttr ? (extractJsxAttrValue(submitAttr) || "onSubmit") : null,
          reset_handler:  resetAttr  ? (extractJsxAttrValue(resetAttr)  || "onReset")  : null,
          library: null,
          fields: [],
        });
      }

      // ---- Routing element detection (Link, NavLink, Route, Redirect) ----
      if (tagName === "Link" || tagName === "NavLink") {
        const toAttr = p.node.attributes.find((a) => a.name && a.name.name === "to");
        if (toAttr) {
          const toVal = extractJsxAttrValue(toAttr);
          if (toVal && !routingInfo.links.includes(toVal)) routingInfo.links.push(toVal);
        }
      }
      if (tagName === "Route") {
        const pathAttr = p.node.attributes.find((a) => a.name && a.name.name === "path");
        if (pathAttr) {
          const pathVal = extractJsxAttrValue(pathAttr);
          if (pathVal && !routingInfo.routes.includes(pathVal)) routingInfo.routes.push(pathVal);
        }
      }
      if (tagName === "Redirect") {
        const toAttr = p.node.attributes.find((a) => a.name && a.name.name === "to");
        if (toAttr) {
          const toVal = extractJsxAttrValue(toAttr);
          if (toVal && !routingInfo.redirects.includes(toVal)) routingInfo.redirects.push(toVal);
        }
      }

      // ---- Context Provider / Consumer detection ----
      if (tagName.endsWith(".Provider")) {
        const ctxName = tagName.replace(".Provider", "");
        const valueAttr = p.node.attributes.find((a) => a.name && a.name.name === "value");
        const valuesProvided = [];
        if (valueAttr && valueAttr.value && valueAttr.value.type === "JSXExpressionContainer") {
          const expr = valueAttr.value.expression;
          if (expr && expr.type === "ObjectExpression") {
            for (const prop of expr.properties) {
              if (prop.key) valuesProvided.push(prop.key.name || prop.key.value);
            }
          }
        }
        const existing = contextUsages.find((c) => c.context_name === ctxName);
        if (!existing) {
          contextUsages.push({ context_name: ctxName, is_provider: true, is_consumer: false, values_provided: valuesProvided });
        } else {
          existing.is_provider = true;
          existing.values_provided = valuesProvided;
        }
      }
      if (tagName.endsWith(".Consumer")) {
        const ctxName = tagName.replace(".Consumer", "");
        const existing = contextUsages.find((c) => c.context_name === ctxName);
        if (!existing) {
          contextUsages.push({ context_name: ctxName, is_provider: false, is_consumer: true, values_provided: [] });
        } else {
          existing.is_consumer = true;
        }
      }
    },

    // ---- Internal functions (enriched with body tracking) ----
    FunctionDeclaration(p) {
      if (p.node.id && p.node.id.name !== name) {
        const fnName = p.node.id.name;
        functionBodyNodes[fnName] = p.node.body;
        functions.push({
          name: fnName,
          params: p.node.params.map((param) => paramName(param)),
          is_async: p.node.async || false,
        });
      }
    },

    VariableDeclarator(p) {
      // Non-component arrow functions inside the component body
      if (
        p.node.id && p.node.id.type === "Identifier" &&
        p.node.init &&
        (p.node.init.type === "ArrowFunctionExpression" || p.node.init.type === "FunctionExpression") &&
        p.node.id.name !== name
      ) {
        const fnName = p.node.id.name;
        if (!/^[A-Z]/.test(fnName)) { // exclude sub-components
          functionBodyNodes[fnName] = p.node.init.body || p.node.init;
          // Also record as a named function entry
          const alreadyRecorded = functions.some((f) => f.name === fnName);
          if (!alreadyRecorded) {
            functions.push({
              name: fnName,
              params: p.node.init.params.map((param) => paramName(param)),
              is_async: p.node.init.async || false,
            });
          }
        }
      }
    },

    // ---- Conditional rendering (ternary / logical expressions in JSX) ----
    ConditionalExpression(p) {
      // Only capture if the ancestor is JSX
      let cur = p.parentPath;
      let insideJsx = false;
      while (cur) {
        if (
          cur.node.type === "JSXExpressionContainer" ||
          cur.node.type === "JSXElement" ||
          cur.node.type === "JSXFragment"
        ) { insideJsx = true; break; }
        if (
          cur.node.type === "ReturnStatement" ||
          cur.node.type === "ArrowFunctionExpression" ||
          cur.node.type === "FunctionDeclaration"
        ) break;
        cur = cur.parentPath;
      }
      if (!insideJsx) return;

      const condition = sourceOf(p.node.test) || "condition";
      const consequent = p.node.consequent &&
        (p.node.consequent.type === "JSXElement" || p.node.consequent.type === "JSXFragment")
        ? getJsxTagName(p.node.consequent.openingElement && p.node.consequent.openingElement.name)
        : null;
      const alternate = p.node.alternate &&
        (p.node.alternate.type === "JSXElement" || p.node.alternate.type === "JSXFragment")
        ? getJsxTagName(p.node.alternate.openingElement && p.node.alternate.openingElement.name)
        : null;

      conditionalRendering.push({
        type: "ternary",
        condition,
        consequent: consequent || "JSX",
        alternate: alternate || "null",
      });
    },

    LogicalExpression(p) {
      // Only capture && / || patterns inside JSX context
      if (p.node.operator !== "&&" && p.node.operator !== "||") return;
      let cur = p.parentPath;
      let insideJsx = false;
      while (cur) {
        if (
          cur.node.type === "JSXExpressionContainer" ||
          cur.node.type === "JSXElement" ||
          cur.node.type === "JSXFragment"
        ) { insideJsx = true; break; }
        if (
          cur.node.type === "ReturnStatement" ||
          cur.node.type === "ArrowFunctionExpression" ||
          cur.node.type === "FunctionDeclaration"
        ) break;
        cur = cur.parentPath;
      }
      if (!insideJsx) return;

      const condition = sourceOf(p.node.left) || "condition";
      const right = p.node.right;
      const rendered = right &&
        (right.type === "JSXElement" || right.type === "JSXFragment")
        ? getJsxTagName(right.openingElement && right.openingElement.name)
        : null;

      conditionalRendering.push({
        type: p.node.operator === "&&" ? "logical_and" : "logical_or",
        condition,
        consequent: rendered || "JSX",
        alternate: p.node.operator === "&&" ? "null" : "JSX",
      });
    },
  });

  // If no JSX found, this might not be a component
  if (jsxElements.length === 0) return null;

  // Convert hook map to array
  for (const h of Object.values(hookMap)) {
    hooks.push(h);
  }

  // Extract props from function params (with TS type info)
  extractPropsFromParams(fnNode, props);

  // Deduplicate conditional_rendering entries by condition+type
  const seenCR = new Set();
  const dedupedCR = conditionalRendering.filter((cr) => {
    const key = `${cr.type}|${cr.condition}`;
    if (seenCR.has(key)) return false;
    seenCR.add(key);
    return true;
  });

  // -------------------------------------------------------------------
  // Post-traverse enrichment: cross-reference state ↔ JSX ↔ handlers
  // -------------------------------------------------------------------

  // 1. state.used_in — scan ALL input occurrences (rawInputElements) plus
  //    deduplicated jsxElements to find references to each state variable.
  //    Using rawInputElements avoids missing the second <input> etc.
  const allJsxForStateRef = [
    ...rawInputElements,
    ...jsxElements.filter((el) => !(["input", "select", "textarea"].includes(el.tag))),
  ];
  for (const stateEntry of state) {
    for (const jsxEl of allJsxForStateRef) {
      // Check attribute name list (e.g. disabled={loading} would put 'loading' in event attr)
      if (jsxEl.attributes.some((a) => a === stateEntry.name)) {
        if (!stateEntry.used_in.includes(jsxEl.tag)) stateEntry.used_in.push(jsxEl.tag);
      }
      // Check value binding
      if (jsxEl.value_binding && jsxEl.value_binding.includes(stateEntry.name)) {
        if (!stateEntry.used_in.includes(jsxEl.tag)) stateEntry.used_in.push(jsxEl.tag);
      }
      // Check aria-label, disabled, placeholder for state variable references
      for (const attrVal of [jsxEl.aria_label, jsxEl.disabled, jsxEl.placeholder, jsxEl.class_name]) {
        if (attrVal && attrVal.includes(stateEntry.name)) {
          if (!stateEntry.used_in.includes(jsxEl.tag)) stateEntry.used_in.push(jsxEl.tag);
        }
      }
    }
  }

  // 2. state.updated_by — find handlers that call the setter
  for (const stateEntry of state) {
    for (const eh of eventHandlers) {
      if (eh.updates_state && eh.updates_state.includes(stateEntry.name)) {
        if (!stateEntry.updated_by.includes(eh.name)) stateEntry.updated_by.push(eh.name);
      }
    }
    // Also scan function bodies
    for (const [fnName, bodyNode] of Object.entries(functionBodyNodes)) {
      const calls = findCallsInNode(bodyNode);
      const callsThisSetter = calls.some((c) => getNodeName(c.callee) === stateEntry.setter);
      if (callsThisSetter && !stateEntry.updated_by.includes(fnName)) {
        stateEntry.updated_by.push(fnName);
      }
    }
  }

  // 3. Enrich existing event handlers whose body wasn't analyzed inline
  for (const eh of eventHandlers) {
    if (eh.updates_state.length === 0 && functionBodyNodes[eh.name]) {
      const analysis = analyzeHandlerNode(functionBodyNodes[eh.name], stateSetterMap);
      eh.updates_state = analysis.updates_state;
      if (!eh.service_calls.length) eh.service_calls = analysis.service_calls;
      if (!eh.navigation) eh.navigation = analysis.navigation;
      if (!eh.prevent_default) eh.prevent_default = analysis.prevent_default;
      if (!eh.stop_propagation) eh.stop_propagation = analysis.stop_propagation;
    }
  }

  // 4. Form library detection (from imports)
  let formLibrary = null;
  for (const imp of fileImports) {
    if (imp.source.includes("formik")) { formLibrary = "formik"; break; }
    if (imp.source.includes("react-hook-form")) { formLibrary = "react-hook-form"; break; }
    if (imp.source.includes("react-final-form")) { formLibrary = "react-final-form"; break; }
  }
  for (const f of forms) { f.library = formLibrary || "native"; }

  // 5. Detect controlled inputs and build form fields
  const targetInputs = rawInputElements.length > 0 ? rawInputElements : jsxElements.filter((el) => ["input", "select", "textarea"].includes(el.tag));
  const formControlled = targetInputs.every((el) =>
    el.value_binding !== null && el.event_bindings.some((eb) => eb.event === "onChange")
  ) && targetInputs.length > 0;

  const formFields = targetInputs.map((el) => {
    // field_type: read the actual value of the type= attribute (stored in _inputType),
    // not just whether the attribute name appears in the list.
    const fieldType = el._inputType || "text";
    return {
      name: el.id || el.attributes.find((a) => ![
        "type", "placeholder", "value", "onChange", "required", "aria-label",
        "className", "id", "disabled"
      ].includes(a)) || "field",
      field_type: fieldType,
      is_controlled: el.value_binding !== null && el.event_bindings.some((eb) => eb.event === "onChange"),
      is_required: el.required === "true" || el.required === true || el.attributes.includes("required"),
      validation_rules: (el.required ? ["required"] : []).concat(
        fieldType === "email" ? ["email"] : []
      ),
      error_message: null,
      label: el.aria_label || null,
      placeholder: el.placeholder || null,
    };
  });

  for (const f of forms) {
    f.is_controlled = formControlled;
    f.fields = formFields;
  }

  // 5b. Prop usage tracking — check all JSX elements (including rawInputElements)
  //     for references to each prop's name in any attribute value.
  const allJsxForPropRef = [
    ...rawInputElements,
    ...jsxElements.filter((el) => !(["input", "select", "textarea"].includes(el.tag))),
  ];
  for (const propEntry of props) {
    for (const jsxEl of allJsxForPropRef) {
      const searchIn = [
        jsxEl.value_binding, jsxEl.aria_label, jsxEl.placeholder,
        jsxEl.disabled, jsxEl.class_name, jsxEl.id,
        ...(jsxEl.event_bindings || []).map((eb) => eb.handler),
      ];
      const nameMatched = searchIn.some((v) => v && v.includes(propEntry.name));
      const attrMatched = jsxEl.attributes.includes(propEntry.name);
      if (nameMatched || attrMatched) {
        if (!propEntry.usage.includes(jsxEl.tag)) propEntry.usage.push(jsxEl.tag);
      }
    }
  }

  // 5c. Hook side effects — include API calls inside useEffect regardless of
  //     whether they are async-await style or .then()-chained style.
  for (const hk of hooks) {
    hk.side_effects = [];
    if (hk.name === "useEffect" || hk.name === "useCallback" || hk.name === "useMemo") {
      for (const call of apiCalls) {
        if (call.in_use_effect && !hk.side_effects.includes(call.function_name)) {
          hk.side_effects.push(call.function_name);
        }
      }
    }
    // For useCallback/useMemo: also add any API calls whose function_name appears in
    // the hook's dependency array (covers indirect side effects).
  }

  // 6. Build child_components (capital-letter JSX tags that aren't HTML elements)
  const HTML_TAGS = new Set([
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "a", "img", "button", "input", "form",
    "select", "textarea", "label", "table", "thead", "tbody",
    "tr", "th", "td", "nav", "header", "footer", "main",
    "section", "article", "aside", "figure", "figcaption",
    "strong", "em", "small", "br", "hr", "pre", "code",
    "svg", "path", "circle", "rect", "g", "text",
    "Fragment", "React.Fragment",
  ]);
  const childComponents = jsxElements
    .map((el) => el.tag)
    .filter((tag) => /^[A-Z]/.test(tag) && !HTML_TAGS.has(tag));

  // 7. Build accessibility summary
  const accessibilityInfo = {
    aria_attributes: ariaAttrs,
    roles: accessRoles,
    keyboard_events: keyboardEvents,
    has_focus_management: hasFocusMgmt,
    alt_texts: altTexts,
    label_associations: labelAssociations,
    accessible_elements: jsxElements
      .filter((el) => el.role || el.aria_label || el.alt)
      .map((el) => el.tag),
  };

  // 8. Build routing_info (only set if something was found)
  const hasRouting =
    routingInfo.links.length > 0 ||
    routingInfo.routes.length > 0 ||
    routingInfo.uses_navigate ||
    routingInfo.uses_router_push ||
    routingInfo.route_params.length > 0 ||
    routingInfo.redirects.length > 0;

  // 9. Build per-component dependency graph node
  const depNode = buildDependencyNode(name, fileImports);

  const eventFlows = eventHandlers.map((eh) => ({
    event: eh.event_type,
    handler: eh.name,
    element: eh.element || "element",
    updates_state: eh.updates_state || [],
    service_calls: eh.service_calls || [],
    navigation: eh.navigation || false,
    prevent_default: eh.prevent_default || false,
    stop_propagation: eh.stop_propagation || false,
  }));

  let businessPurpose = "Interactive Frontend Component";
  const nameLower = name.toLowerCase();
  if (/login|auth|signin|register|signup/.test(nameLower)) {
    businessPurpose = "User Authentication & Access Management";
  } else if (/card|stat|badge|item|tile|counter/.test(nameLower)) {
    businessPurpose = "UI Data Card & Metric Presentation";
  } else if (/form|input|editor/.test(nameLower)) {
    businessPurpose = "Interactive Form & Data Entry Management";
  } else if (/nav|header|footer|sidebar|menu/.test(nameLower)) {
    businessPurpose = "Navigation & Page Workspace Layout";
  } else if (/table|list|grid/.test(nameLower)) {
    businessPurpose = "Tabular Data & List Collection Presentation";
  }

  let complexity = 1 + props.length + (state.length * 2) + hooks.length + eventHandlers.length + (apiCalls.length * 2) + (forms.length * 2);
  if (complexity > 10) complexity = 10;

  let risk = 1 + (forms.length * 2) + (apiCalls.length * 2) + state.length + hooks.length;
  if (risk > 10) risk = 10;

  let testPriority = "medium";
  if (complexity >= 5 || forms.length > 0 || apiCalls.length > 0) {
    testPriority = "high";
  } else if (eventHandlers.length === 0 && state.length === 0 && props.length <= 1) {
    testPriority = "low";
  }

  const compResult = {
    file_path: filePath,
    name,
    type,
    props,
    state,
    hooks,
    jsx_elements: jsxElements,
    event_handlers: eventHandlers,
    functions,
    imports: fileImports,
    exports: fileExports,
    api_calls: apiCalls,
    // New enriched fields
    parent_component: null, // filled in main()
    child_components: childComponents,
    forms,
    routing_info: hasRouting ? routingInfo : null,
    context_usage: contextUsages,
    accessibility: accessibilityInfo,
    testing_metadata: null, // filled after full component is built
    dependency_graph: depNode,
    conditional_rendering: dedupedCR,
    event_flows: eventFlows,
    business_purpose: businessPurpose,
    complexity_score: complexity,
    risk_score: risk,
    test_priority: testPriority,
    confidence_score: 1.0,
  };

  // 10. Build testing_metadata (requires the complete component object)
  compResult.testing_metadata = buildTestingMetadata(compResult);

  return compResult;
} // end createComponentCore

// Keep the old createComponent signature so all call-sites still work —
// it now delegates to createComponentCore.
function _createComponent_UNUSED() {}

function createClassComponent(name, filePath, componentPath, fileImports, fileExports) {
  const props = [];
  const state = [];
  const hooks = [];
  const jsxElements = [];
  const eventHandlers = [];
  const functions = [];
  const apiCalls = [];
  const ariaAttrs = {};
  const accessRoles = [];
  const altTexts = [];
  const keyboardEvents = [];
  let hasFocusMgmt = false;
  const labelAssociations = [];
  const conditionalRendering = [];
  const seenThisProps = new Set(); // track this.props.x references

  componentPath.traverse({
    // Class methods
    ClassMethod(p) {
      const methodName = p.node.key.name || p.node.key.value;
      if (methodName && methodName !== "constructor" && methodName !== "render") {
        functions.push({
          name: methodName,
          params: p.node.params.map((param) => paramName(param)),
          is_async: p.node.async || false,
        });
      }
    },

    // this.state in constructor
    AssignmentExpression(p) {
      if (
        p.node.left.type === "MemberExpression" &&
        p.node.left.object.type === "ThisExpression" &&
        getNodeName(p.node.left.property) === "state" &&
        p.node.right.type === "ObjectExpression"
      ) {
        for (const prop of p.node.right.properties) {
          if (prop.key) {
            state.push({
              name: prop.key.name || prop.key.value,
              setter: "setState",
              initial_value: sourceOf(prop.value),
              state_type: inferStateType(sourceOf(prop.value)),
              used_in: [],
              updated_by: [],
            });
          }
        }
      }
    },

    // JSX elements in render() (enriched)
    JSXOpeningElement(p) {
      const tagName = getJsxTagName(p.node.name);
      const attrNames = [];
      const jsxEntry = {
        tag: tagName,
        attributes: attrNames,
        children_count: 0,
        id: null, class_name: null, role: null, aria_label: null, aria_expanded: null,
        placeholder: null, alt: null, disabled: null, required: null,
        value_binding: null, event_bindings: [],
      };

      for (const attr of p.node.attributes) {
        if (attr.type !== "JSXAttribute" || !attr.name) continue;
        const attrName = attr.name.type === "JSXNamespacedName"
          ? `${attr.name.namespace.name}-${attr.name.name.name}`
          : attr.name.name;
        if (!attrName) continue;
        attrNames.push(attrName);
        const attrVal = extractJsxAttrValue(attr);

        switch (attrName) {
          case "id": jsxEntry.id = attrVal; break;
          case "className": jsxEntry.class_name = attrVal; break;
          case "role": jsxEntry.role = attrVal; if (attrVal && !accessRoles.includes(attrVal)) accessRoles.push(attrVal); break;
          case "aria-label": jsxEntry.aria_label = attrVal; ariaAttrs["aria-label"] = attrVal; break;
          case "aria-expanded": jsxEntry.aria_expanded = attrVal; ariaAttrs["aria-expanded"] = attrVal; break;
          case "placeholder": jsxEntry.placeholder = attrVal; break;
          case "alt": jsxEntry.alt = attrVal; if (attrVal) altTexts.push(attrVal); break;
          case "disabled": jsxEntry.disabled = attrVal || "true"; break;
          case "required": jsxEntry.required = attrVal || "true"; break;
          case "value": jsxEntry.value_binding = attrVal; break;
          case "htmlFor": if (attrVal) labelAssociations.push(attrVal); break;
          case "autoFocus": hasFocusMgmt = true; break;
        }
        if (attrName.startsWith("aria-") && attrName !== "aria-label" && attrName !== "aria-expanded") {
          ariaAttrs[attrName] = attrVal;
        }

        if (/^on[A-Z]/.test(attrName)) {
          if (/^onKey/.test(attrName) && !keyboardEvents.includes(attrName)) keyboardEvents.push(attrName);
          let handlerName = attrName;
          let handlerNode = null;
          if (attr.value && attr.value.type === "JSXExpressionContainer" && attr.value.expression) {
            const expr = attr.value.expression;
            const exprName = getNodeName(expr);
            if (exprName) {
              handlerName = exprName.replace("this.", "");
              handlerNode = expr;
            } else if (expr.type === "ArrowFunctionExpression" || expr.type === "FunctionExpression") {
              handlerName = `${attrName}Handler`;
              handlerNode = expr;
            } else {
              handlerNode = expr;
            }
          }
          jsxEntry.event_bindings.push({ event: attrName, handler: handlerName });
          if (!eventHandlers.some((eh) => eh.name === handlerName && eh.event_type === attrName)) {
            const analysis = analyzeHandlerNode(handlerNode, {});
            eventHandlers.push({
              name: handlerName, event_type: attrName, element: tagName,
              updates_state: analysis.updates_state, service_calls: analysis.service_calls,
              navigation: analysis.navigation, prevent_default: analysis.prevent_default,
              stop_propagation: analysis.stop_propagation,
            });
          }
        }
      }

      const parentEl = p.parentPath.node;
      jsxEntry.children_count = parentEl && parentEl.children
        ? parentEl.children.filter((c) => c.type !== "JSXText" || c.value.trim()).length : 0;

      const existing = jsxElements.find((el) => el.tag === tagName);
      if (!existing) {
        jsxElements.push(jsxEntry);
      } else {
        for (const eb of jsxEntry.event_bindings) {
          if (!existing.event_bindings.some((x) => x.event === eb.event && x.handler === eb.handler)) {
            existing.event_bindings.push(eb);
          }
        }
        for (const a of attrNames) { if (!existing.attributes.includes(a)) existing.attributes.push(a); }
      }
    },

    // API calls
    CallExpression(p) {
      const calleeName = getNodeName(p.node.callee);
      if (calleeName) {
        const cleaned = calleeName.replace("this.", "");
        if (
          cleaned === "fetch" || cleaned.startsWith("axios") ||
          cleaned.includes("Service") || cleaned.includes("service") ||
          cleaned.includes("api") || cleaned.includes("Api")
        ) {
          const callType = cleaned === "fetch" ? "fetch" : cleaned.startsWith("axios") ? "axios" : "service_call";
          apiCalls.push({
            function_name: cleaned,
            type: callType,
            endpoint: extractEndpoint(p.node),
            http_method: inferHttpMethod(cleaned, p.node),
            is_async: isInsideAsyncFn(p),
            has_error_handling: isInsideTryCatch(p),
            in_use_effect: false, // class components don't use useEffect
            loading_state_var: null,
          });
        }
        if (cleaned.includes(".focus") || cleaned === "focus") hasFocusMgmt = true;
      }
    },

    // Capture this.props.x references in class components
    MemberExpression(p) {
      const node = p.node;
      if (
        node.object &&
        node.object.type === "MemberExpression" &&
        node.object.object.type === "ThisExpression" &&
        getNodeName(node.object.property) === "props" &&
        node.property
      ) {
        const propName = node.property.name || node.property.value;
        if (propName && !seenThisProps.has(propName)) {
          seenThisProps.add(propName);
          props.push({ name: propName, type: "any", required: true, default_value: null, usage: [] });
        }
      }
    },

    // Conditional rendering
    ConditionalExpression(p) {
      let cur = p.parentPath;
      let insideJsx = false;
      while (cur) {
        if (
          cur.node.type === "JSXExpressionContainer" ||
          cur.node.type === "JSXElement" ||
          cur.node.type === "JSXFragment"
        ) { insideJsx = true; break; }
        if (cur.node.type === "ReturnStatement") break;
        cur = cur.parentPath;
      }
      if (!insideJsx) return;
      const condition = sourceOf(p.node.test) || "condition";
      const consequent = p.node.consequent &&
        (p.node.consequent.type === "JSXElement" || p.node.consequent.type === "JSXFragment")
        ? getJsxTagName(p.node.consequent.openingElement && p.node.consequent.openingElement.name)
        : null;
      const alternate = p.node.alternate &&
        (p.node.alternate.type === "JSXElement" || p.node.alternate.type === "JSXFragment")
        ? getJsxTagName(p.node.alternate.openingElement && p.node.alternate.openingElement.name)
        : null;
      conditionalRendering.push({
        type: "ternary",
        condition,
        consequent: consequent || "JSX",
        alternate: alternate || "null",
      });
    },

    LogicalExpression(p) {
      if (p.node.operator !== "&&" && p.node.operator !== "||") return;
      let cur = p.parentPath;
      let insideJsx = false;
      while (cur) {
        if (
          cur.node.type === "JSXExpressionContainer" ||
          cur.node.type === "JSXElement" ||
          cur.node.type === "JSXFragment"
        ) { insideJsx = true; break; }
        if (cur.node.type === "ReturnStatement") break;
        cur = cur.parentPath;
      }
      if (!insideJsx) return;
      const condition = sourceOf(p.node.left) || "condition";
      const right = p.node.right;
      const rendered = right &&
        (right.type === "JSXElement" || right.type === "JSXFragment")
        ? getJsxTagName(right.openingElement && right.openingElement.name)
        : null;
      conditionalRendering.push({
        type: p.node.operator === "&&" ? "logical_and" : "logical_or",
        condition,
        consequent: rendered || "JSX",
        alternate: p.node.operator === "&&" ? "null" : "JSX",
      });
    },
  });

  const HTML_TAGS = new Set([
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "a", "img", "button", "input", "form",
    "select", "textarea", "label", "table", "thead", "tbody",
    "tr", "th", "td", "nav", "header", "footer", "main",
    "section", "article", "aside", "svg", "path", "g",
    "Fragment", "React.Fragment",
  ]);
  const childComponents = jsxElements
    .map((el) => el.tag)
    .filter((tag) => /^[A-Z]/.test(tag) && !HTML_TAGS.has(tag));

  const accessibilityInfo = {
    aria_attributes: ariaAttrs, roles: accessRoles, keyboard_events: keyboardEvents,
    has_focus_management: hasFocusMgmt, alt_texts: altTexts,
    label_associations: labelAssociations,
    accessible_elements: jsxElements.filter((el) => el.role || el.aria_label || el.alt).map((el) => el.tag),
  };

  const depNode = buildDependencyNode(name, fileImports);

  const eventFlows = eventHandlers.map((eh) => ({
    event: eh.event_type,
    handler: eh.name,
    element: eh.element || "element",
    updates_state: eh.updates_state || [],
    service_calls: eh.service_calls || [],
    navigation: eh.navigation || false,
    prevent_default: eh.prevent_default || false,
    stop_propagation: eh.stop_propagation || false,
  }));

  let businessPurpose = "Interactive Frontend Component";
  const nameLower = name.toLowerCase();
  if (/login|auth|signin|register|signup/.test(nameLower)) {
    businessPurpose = "User Authentication & Access Management";
  } else if (/card|stat|badge|item|tile|counter/.test(nameLower)) {
    businessPurpose = "UI Data Card & Metric Presentation";
  } else if (/form|input|editor/.test(nameLower)) {
    businessPurpose = "Interactive Form & Data Entry Management";
  } else if (/nav|header|footer|sidebar|menu/.test(nameLower)) {
    businessPurpose = "Navigation & Page Workspace Layout";
  } else if (/table|list|grid/.test(nameLower)) {
    businessPurpose = "Tabular Data & List Collection Presentation";
  }

  let complexity = 1 + props.length + (state.length * 2) + hooks.length + eventHandlers.length + (apiCalls.length * 2);
  if (complexity > 10) complexity = 10;

  let risk = 1 + (apiCalls.length * 2) + state.length;
  if (risk > 10) risk = 10;

  let testPriority = "medium";
  if (complexity >= 5 || apiCalls.length > 0) {
    testPriority = "high";
  } else if (eventHandlers.length === 0 && state.length === 0 && props.length <= 1) {
    testPriority = "low";
  }

  // Deduplicate conditional_rendering
  const seenCRClass = new Set();
  const dedupedCRClass = conditionalRendering.filter((cr) => {
    const key = `${cr.type}|${cr.condition}`;
    if (seenCRClass.has(key)) return false;
    seenCRClass.add(key);
    return true;
  });

  const compResult = {
    file_path: filePath,
    name,
    type: "class",
    props,
    state,
    hooks,
    jsx_elements: jsxElements,
    event_handlers: eventHandlers,
    functions,
    imports: fileImports,
    exports: fileExports,
    api_calls: apiCalls,
    parent_component: null,
    child_components: childComponents,
    forms: [],
    routing_info: null,
    context_usage: [],
    accessibility: accessibilityInfo,
    testing_metadata: null,
    dependency_graph: depNode,
    conditional_rendering: dedupedCRClass,
    event_flows: eventFlows,
    business_purpose: businessPurpose,
    complexity_score: complexity,
    risk_score: risk,
    test_priority: testPriority,
    confidence_score: 1.0,
  };
  compResult.testing_metadata = buildTestingMetadata(compResult);
  return compResult;
}

// -------------------------------------------------------------------------
// Utility helpers
// -------------------------------------------------------------------------

/**
 * Infer a human-readable type string from a TypeScript type annotation node.
 */
function inferTsType(tsTypeNode) {
  if (!tsTypeNode) return "any";
  switch (tsTypeNode.type) {
    case "TSStringKeyword":  return "string";
    case "TSNumberKeyword":  return "number";
    case "TSBooleanKeyword": return "boolean";
    case "TSAnyKeyword":     return "any";
    case "TSUnknownKeyword": return "unknown";
    case "TSVoidKeyword":    return "void";
    case "TSNullKeyword":    return "null";
    case "TSUndefinedKeyword": return "undefined";
    case "TSArrayType":      return `${inferTsType(tsTypeNode.elementType)}[]`;
    case "TSTypeReference":  return getNodeName(tsTypeNode.typeName) || "object";
    case "TSUnionType":      return (tsTypeNode.types || []).map(inferTsType).join(" | ");
    case "TSIntersectionType": return (tsTypeNode.types || []).map(inferTsType).join(" & ");
    case "TSLiteralType":    return sourceOf(tsTypeNode.literal) || "literal";
    case "TSFunctionType":   return "() => void";
    case "TSObjectKeyword":  return "object";
    case "TSTypeLiteral":    return "object";
    default: return "any";
  }
}

function extractPropsFromParams(fnNode, propsArray) {
  const params = fnNode.params || [];
  if (params.length === 0) return;
  const firstParam = params[0];

  if (firstParam.type === "ObjectPattern") {
    for (const prop of firstParam.properties) {
      // RestElement: function Foo({ a, ...rest }) — capture rest as a prop
      if (prop.type === "RestElement" && prop.argument) {
        const restName = prop.argument.name || "rest";
        propsArray.push({ name: restName, type: "object", required: false, default_value: null, usage: [] });
        continue;
      }
      if (prop.type === "ObjectProperty" && prop.key) {
        const propName = prop.key.name || prop.key.value;
        if (!propName) continue;

        // Infer TS type from the value's type annotation (e.g., { onClick: handler }: Props)
        let propType = "any";
        if (prop.value && prop.value.typeAnnotation) {
          propType = inferTsType(prop.value.typeAnnotation.typeAnnotation);
        }

        const propEntry = {
          name: propName,
          type: propType,
          required: true,
          default_value: null,
          usage: [],
        };
        // AssignmentPattern: { foo = 'bar' }
        if (prop.value && prop.value.type === "AssignmentPattern") {
          propEntry.required = false;
          propEntry.default_value = sourceOf(prop.value.right);
          // Type from the left side's annotation
          if (prop.value.left && prop.value.left.typeAnnotation) {
            propEntry.type = inferTsType(prop.value.left.typeAnnotation.typeAnnotation);
          }
        }
        propsArray.push(propEntry);
      }
    }
  } else if (firstParam.type === "Identifier") {
    // function Foo(props) — whole props object
    propsArray.push({ name: firstParam.name, type: "object", required: true, default_value: null, usage: [] });
  } else if (firstParam.type === "AssignmentPattern" && firstParam.left) {
    // function Foo({ a } = {}) — destructured with default
    const inner = firstParam.left;
    if (inner.type === "ObjectPattern") {
      // Recurse with a fake node so we reuse the ObjectPattern branch
      extractPropsFromParams({ params: [inner] }, propsArray);
    }
  }

  // TypeScript typed props via parameter annotations
  // e.g., function Foo({ a, b }: { a: string; b: number }) { ... }
  const annotation = firstParam.typeAnnotation && firstParam.typeAnnotation.typeAnnotation;
  if (annotation && annotation.type === "TSTypeLiteral" && annotation.members) {
    for (const member of annotation.members) {
      if (member.type === "TSPropertySignature" && member.key) {
        const memberName = member.key.name || member.key.value;
        if (!memberName) continue;
        // Upsert: if already in propsArray, update type; otherwise add
        const existing = propsArray.find((p) => p.name === memberName);
        const inferredType = member.typeAnnotation
          ? inferTsType(member.typeAnnotation.typeAnnotation)
          : "any";
        const isRequired = !member.optional;
        if (existing) {
          if (existing.type === "any") existing.type = inferredType;
          if (isRequired) existing.required = true;
        } else {
          propsArray.push({
            name: memberName,
            type: inferredType,
            required: isRequired,
            default_value: null,
            usage: [],
          });
        }
      }
    }
  } else if (annotation && annotation.type === "TSTypeReference" && annotation.typeName) {
    // Props typed by a named interface — we note the interface name but
    // cannot resolve its members without a type-checker.
    // Tag all existing props with the interface name as context.
    const ifaceName = getNodeName(annotation.typeName);
    if (ifaceName && propsArray.length === 0) {
      // No props destructured — add a placeholder so callers know it's typed
      propsArray.push({ name: "props", type: ifaceName, required: true, default_value: null, usage: [] });
    }
  }
}

function getJsxTagName(nameNode) {
  if (!nameNode) return "unknown";
  if (nameNode.type === "JSXIdentifier") return nameNode.name;
  if (nameNode.type === "JSXMemberExpression") {
    return `${getJsxTagName(nameNode.object)}.${getJsxTagName(nameNode.property)}`;
  }
  if (nameNode.type === "JSXNamespacedName") {
    return `${nameNode.namespace.name}:${nameNode.name.name}`;
  }
  return "unknown";
}

function paramName(param) {
  if (param.type === "Identifier") return param.name;
  if (param.type === "AssignmentPattern" && param.left) return paramName(param.left);
  if (param.type === "ObjectPattern") return "props";
  if (param.type === "RestElement" && param.argument) return `...${paramName(param.argument)}`;
  return "unknown";
}

function sourceOf(node) {
  if (!node) return null;
  if (node.type === "StringLiteral") return `'${node.value}'`;
  if (node.type === "NumericLiteral") return String(node.value);
  if (node.type === "BooleanLiteral") return String(node.value);
  if (node.type === "NullLiteral") return "null";
  if (node.type === "Identifier") return node.name;
  if (node.type === "ArrayExpression") return "[]";
  if (node.type === "ObjectExpression") return "{}";
  if (node.type === "TemplateLiteral") return "`...`";
  if (node.type === "ArrowFunctionExpression" || node.type === "FunctionExpression") return "() => {}";
  return null;
}

// -------------------------------------------------------------------------
// Main entry point
// -------------------------------------------------------------------------

function main() {
  const projectPath = process.argv[2];
  if (!projectPath) {
    process.stderr.write("Usage: node react_parser.js <project_path>\n");
    process.exit(1);
  }

  if (!fs.existsSync(projectPath) || !fs.statSync(projectPath).isDirectory()) {
    process.stderr.write(`Error: project path does not exist or is not a directory: ${projectPath}\n`);
    process.exit(1);
  }

  const allFiles = walkDir(projectPath);
  const sourceFiles = allFiles.filter((f) => !isTestFile(f));
  const testFiles = allFiles.filter((f) => isTestFile(f));

  const allComponents = [];

  for (const filePath of sourceFiles) {
    try {
      const result = extractFromFile(filePath, projectPath);
      if (result && result.components.length > 0) {
        allComponents.push(...result.components);
      }
    } catch (err) {
      process.stderr.write(`Warning: error processing ${filePath}: ${err.message}\n`);
    }
  }

  const existingTests = testFiles.map((f) => {
    const rel = path.relative(projectPath, f).replace(/\\/g, "/");
    const type = /\.spec\./.test(f) ? "spec" : "test";
    return { file_path: rel, type };
  });

  // -----------------------------------------------------------------
  // Post-parse enrichment: component hierarchy, test mapping, dep graph
  // -----------------------------------------------------------------

  // Build index of all known component names
  const componentNameSet = new Set(allComponents.map((c) => c.name));

  // 1. Component relationships + parent_component assignment
  const componentRelationships = [];
  for (const comp of allComponents) {
    // Filter child_components to known project components
    const validChildren = (comp.child_components || []).filter((ch) => componentNameSet.has(ch));
    comp.child_components = validChildren;

    const rel = {
      component: comp.name,
      parent: null, // filled below
      children: validChildren,
      depth: 0,   // filled below
    };
    componentRelationships.push(rel);
  }

  // Assign parents (a component is a parent if another component appears in its child_components)
  for (const parentComp of allComponents) {
    for (const childName of parentComp.child_components) {
      // Set parent on the child component object
      const childComp = allComponents.find((c) => c.name === childName);
      if (childComp && !childComp.parent_component) {
        childComp.parent_component = parentComp.name;
      }
      // Set parent on the relationship entry
      const childRel = componentRelationships.find((r) => r.component === childName);
      if (childRel && !childRel.parent) childRel.parent = parentComp.name;
    }
  }

  // Compute depth using BFS from roots (components with no parent)
  const roots = componentRelationships.filter((r) => !r.parent);
  function assignDepth(rel, depth) {
    rel.depth = depth;
    for (const childName of rel.children) {
      const childRel = componentRelationships.find((r) => r.component === childName);
      if (childRel) assignDepth(childRel, depth + 1);
    }
  }
  for (const root of roots) assignDepth(root, 0);

  // 2. Test mapping — match test files to components by name proximity
  const testMapping = [];
  for (const comp of allComponents) {
    const compName = comp.name;
    // Look for test file whose basename contains the component name
    const matched = existingTests.find((t) => {
      const base = path.basename(t.file_path, path.extname(t.file_path))
        .replace(/\.test$/, "").replace(/\.spec$/, "");
      return base.toLowerCase() === compName.toLowerCase();
    });

    let coveredFeatures = [];
    let testingFramework = null;

    if (matched) {
      // Scan test file for describe/it/test labels
      const testFileFull = path.join(projectPath, matched.file_path);
      if (fs.existsSync(testFileFull)) {
        try {
          const testCode = fs.readFileSync(testFileFull, "utf-8");
          // Extract labels from describe('...') / it('...') / test('...')
          const labelRe = /(?:describe|it|test)\s*\(\s*['"`]([^'"`]+)['"`]/g;
          let m;
          while ((m = labelRe.exec(testCode)) !== null) {
            if (!coveredFeatures.includes(m[1])) coveredFeatures.push(m[1]);
          }
          // Detect framework
          if (testCode.includes("@testing-library/react")) testingFramework = "jest+rtl";
          else if (testCode.includes("enzyme")) testingFramework = "jest+enzyme";
          else if (testCode.includes("vitest")) testingFramework = "vitest";
          else testingFramework = "jest";
        } catch { /* ignore read errors */ }
      }
    }

    testMapping.push({
      component: compName,
      test_file: matched ? matched.file_path : null,
      testing_framework: testingFramework,
      covered_features: coveredFeatures,
    });
  }

  // 3. Top-level dependency graph (one node per component)
  const dependencyGraph = allComponents.map((c) => c.dependency_graph).filter(Boolean);

  const output = {
    components: allComponents,
    existing_tests: existingTests,
    files_analyzed: sourceFiles.length,
    component_relationships: componentRelationships,
    dependency_graph: dependencyGraph,
    test_mapping: testMapping,
  };

  process.stdout.write(JSON.stringify(output, null, 0));
}

main();
