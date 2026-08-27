/**
 * Angular Parser – Node.js script invoked via subprocess from Python.
 *
 * Uses the TypeScript Compiler API to parse .ts files and
 * @angular/compiler to parse HTML templates.
 *
 * Extracts (v2 enriched): components, decorators, inputs, outputs, services,
 *   DI, reactive forms, routing, modules, template bindings,
 *   and existing test files. New in v2: API calls in services and components,
 *   accessibility from templates, child component detection, testing metadata,
 *   component_relationships, dependency_graph, test_mapping.
 *
 * Usage:  node angular_parser.js <absolute_project_path>
 * Output: JSON on stdout matching the AngularAnalysisResult Pydantic schema.
 * Errors: Written to stderr with non-zero exit code.
 */

"use strict";

const fs = require("fs");
const path = require("path");
const ts = require("typescript");

let angularCompiler;
try {
  angularCompiler = require("@angular/compiler");
} catch {
  // If @angular/compiler is not installed, template parsing will be skipped.
  angularCompiler = null;
}

// -------------------------------------------------------------------------
// Configuration
// -------------------------------------------------------------------------

const EXCLUDED_DIRS = new Set(["node_modules", "dist", "build", ".git", "coverage", "e2e"]);

/** Angular HTTP client method names that indicate API calls. */
const HTTP_METHODS = new Set(["get", "post", "put", "delete", "patch", "head", "request"]);

/** Angular lifecycle hooks (excluded from methods list). */
const LIFECYCLE_HOOKS = new Set([
  "ngOnInit", "ngOnDestroy", "ngOnChanges", "ngDoCheck",
  "ngAfterContentInit", "ngAfterContentChecked",
  "ngAfterViewInit", "ngAfterViewChecked",
]);

// -------------------------------------------------------------------------
// New Angular enrichment helpers (v2)
// -------------------------------------------------------------------------

/**
 * Walk a TypeScript AST subtree and collect all call expressions.
 * Returns an array of { callee, node } pairs.
 */
function findTsCallsInNode(node, results) {
  if (!results) results = [];
  if (!node) return results;
  if (ts.isCallExpression(node)) results.push(node);
  ts.forEachChild(node, (child) => findTsCallsInNode(child, results));
  return results;
}

/**
 * Extract API calls from a TypeScript method body.
 * Looks for this.http.get/post/put/delete/patch() and bare fetch() calls.
 */
function extractApiCallsFromMethod(methodNode) {
  const calls = findTsCallsInNode(methodNode.body);
  const apiCalls = [];

  for (const callNode of calls) {
    let calleeName = null;
    let httpMethod = null;
    let endpoint = null;

    // this.http.get / this.http.post etc.
    if (ts.isPropertyAccessExpression(callNode.expression)) {
      const methodPart = callNode.expression.name.text;
      if (HTTP_METHODS.has(methodPart.toLowerCase())) {
        httpMethod = methodPart.toUpperCase();
        // Build full callee name
        calleeName = callNode.expression.getText
          ? callNode.expression.getText()
          : `this.http.${methodPart}`;

        // First string argument is the endpoint
        if (callNode.arguments.length > 0 && ts.isStringLiteral(callNode.arguments[0])) {
          endpoint = callNode.arguments[0].text;
        } else if (callNode.arguments.length > 0 && ts.isTemplateExpression(callNode.arguments[0])) {
          endpoint = callNode.arguments[0].head ? callNode.arguments[0].head.text : null;
        }

        // Error handling: inside try block
        let hasTry = false;
        let parent = callNode.parent;
        while (parent) {
          if (ts.isTryStatement(parent)) { hasTry = true; break; }
          parent = parent.parent;
        }

        // is_async: check if enclosing function is async
        let isAsync = false;
        if (methodNode.modifiers) {
          isAsync = methodNode.modifiers.some((m) => m.kind === ts.SyntaxKind.AsyncKeyword);
        }

        apiCalls.push({
          function_name: calleeName,
          type: "service_call",
          endpoint,
          http_method: httpMethod,
          is_async: isAsync,
          has_error_handling: hasTry,
          in_use_effect: false,
          loading_state_var: null,
        });
      }
    }

    // Bare fetch()
    if (
      ts.isIdentifier(callNode.expression) &&
      callNode.expression.text === "fetch"
    ) {
      let httpMethodFetch = "GET";
      let endpointFetch = null;
      if (callNode.arguments.length > 0 && ts.isStringLiteral(callNode.arguments[0])) {
        endpointFetch = callNode.arguments[0].text;
      }
      if (callNode.arguments.length >= 2 && ts.isObjectLiteralExpression(callNode.arguments[1])) {
        const opts = callNode.arguments[1];
        for (const prop of opts.properties) {
          if (ts.isPropertyAssignment(prop) &&
              ts.isIdentifier(prop.name) &&
              prop.name.text === "method" &&
              ts.isStringLiteral(prop.initializer)) {
            httpMethodFetch = prop.initializer.text.toUpperCase();
          }
        }
      }
      apiCalls.push({
        function_name: "fetch",
        type: "fetch",
        endpoint: endpointFetch,
        http_method: httpMethodFetch,
        is_async: false,
        has_error_handling: false,
        in_use_effect: false,
        loading_state_var: null,
      });
    }
  }

  return apiCalls;
}

/**
 * Build a DependencyNode for an Angular component/service from its imports.
 */
function buildAngularDependencyNode(entityName, imports) {
  const node = {
    component: entityName,
    imports_components: [],
    imports_services: [],
    imports_utilities: [],
    imports_contexts: [],
  };
  for (const imp of imports) {
    const src = imp.source || "";
    for (const spec of imp.specifiers || []) {
      const name = spec.replace(/^\* as /, "");
      if (!name) continue;
      if (/Service|service|Http|http/.test(name) || /Service|service|api|Api|http/.test(src)) {
        if (!node.imports_services.includes(name)) node.imports_services.push(name);
      } else if (/Component$/.test(name) || (/^[A-Z]/.test(name) && src.startsWith("."))) {
        if (!node.imports_components.includes(name)) node.imports_components.push(name);
      } else {
        if (!node.imports_utilities.includes(name)) node.imports_utilities.push(name);
      }
    }
  }
  return node;
}

/**
 * Extract accessibility info from raw HTML string (works without @angular/compiler).
 */
function extractAccessibilityFromHtml(html) {
  const ariaAttrs = {};
  const roles = [];
  const keyboardEvents = [];
  const altTexts = [];
  const labelAssociations = [];
  let hasFocus = false;

  // aria-* attributes
  const ariaRe = /aria-([\w-]+)=["']([^"']*)["']/g;
  let m;
  while ((m = ariaRe.exec(html)) !== null) {
    ariaAttrs[`aria-${m[1]}`] = m[2];
  }
  // Also attr binding: [attr.aria-label]="..."
  const ariaBindRe = /\[attr\.(aria-[\w-]+)\]=["']([^"']*)["']/g;
  while ((m = ariaBindRe.exec(html)) !== null) {
    ariaAttrs[m[1]] = m[2];
  }

  // role=
  const roleRe = /role=["']([^"']+)["']/g;
  while ((m = roleRe.exec(html)) !== null) {
    if (!roles.includes(m[1])) roles.push(m[1]);
  }

  // alt=
  const altRe = /alt=["']([^"']+)["']/g;
  while ((m = altRe.exec(html)) !== null) {
    if (!altTexts.includes(m[1])) altTexts.push(m[1]);
  }

  // htmlFor / for=
  const forRe = /(?:htmlFor|for)=["']([^"']+)["']/g;
  while ((m = forRe.exec(html)) !== null) {
    if (!labelAssociations.includes(m[1])) labelAssociations.push(m[1]);
  }

  // keyboard event bindings
  const kbRe = /\((keydown|keyup|keypress)(?:\.[^)]+)?\)/g;
  while ((m = kbRe.exec(html)) !== null) {
    const eventName = `(${m[1]})`;
    if (!keyboardEvents.includes(eventName)) keyboardEvents.push(eventName);
  }

  // autofocus
  if (/autofocus/i.test(html)) hasFocus = true;

  // Detect accessible elements (elements with aria or role attributes)
  const accessibleEls = [];
  const tagWithAriaRe = /<([a-zA-Z][a-zA-Z0-9-]*)\s[^>]*(?:aria-|role=)[^>]*>/g;
  while ((m = tagWithAriaRe.exec(html)) !== null) {
    if (!accessibleEls.includes(m[1])) accessibleEls.push(m[1]);
  }

  return {
    aria_attributes: ariaAttrs,
    roles,
    keyboard_events: keyboardEvents,
    has_focus_management: hasFocus,
    alt_texts: altTexts,
    label_associations: labelAssociations,
    accessible_elements: accessibleEls,
  };
}

/**
 * Detect child Angular component selectors used in an HTML template.
 * Matches camelCase or dash-case custom tags that are not standard HTML.
 */
function extractChildSelectorsFromHtml(html, knownSelectors) {
  const HTML_TAGS = new Set([
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "a", "img", "button", "input", "form",
    "select", "textarea", "label", "table", "thead", "tbody",
    "tr", "th", "td", "nav", "header", "footer", "main",
    "section", "article", "aside", "svg", "path", "g",
    "ng-container", "ng-content", "ng-template", "router-outlet",
    "script", "style", "link", "meta", "title",
  ]);
  const found = [];
  // Match custom element tags (dash-case or PascalCase)
  const tagRe = /<([a-zA-Z][a-zA-Z0-9-]*)/g;
  let m;
  while ((m = tagRe.exec(html)) !== null) {
    const tag = m[1];
    if (HTML_TAGS.has(tag.toLowerCase())) continue;
    if (tag.includes("-") || /^[A-Z]/.test(tag)) {
      if (!found.includes(tag)) found.push(tag);
    }
  }
  // Filter to only known component selectors
  if (knownSelectors && knownSelectors.size > 0) {
    return found.filter((t) => knownSelectors.has(t));
  }
  return found;
}

/**
 * Generate testing metadata for an Angular component.
 */
function buildAngularTestingMetadata(comp) {
  const categories = ["Rendering"];
  const testableElements = [];
  const interactiveElements = [];
  const mockDependencies = [];
  const recommendedQueries = [];
  const edgeCases = [];
  const negativeScenarios = [];
  const suggestedMocks = [];

  // Inputs / Outputs
  if ((comp.inputs || []).length > 0) {
    categories.push("Input Properties");
    edgeCases.push("Component rendering when @Input properties change");
    for (const input of comp.inputs) testableElements.push(`@Input ${input.name}`);
  }
  if ((comp.outputs || []).length > 0) {
    categories.push("Output Events");
    for (const output of comp.outputs) interactiveElements.push(`@Output ${output.name}`);
  }

  // Forms
  if ((comp.reactive_forms || []).length > 0) {
    categories.push("Forms");
    edgeCases.push("Reactive form submission with default control values");
    negativeScenarios.push("Submitting invalid reactive form triggers validation error");
  }

  // API calls
  if ((comp.api_calls || []).length > 0) {
    categories.push("API");
    edgeCases.push("HTTP client request 500 error handling");
    negativeScenarios.push("HTTP error response triggers error state display");
    for (const call of comp.api_calls) {
      if (!mockDependencies.includes(call.function_name)) mockDependencies.push(call.function_name);
      suggestedMocks.push({ name: call.function_name, type: "service_call" });
    }
  }

  // Services from DI
  for (const svc of comp.injected_services || []) {
    if (!mockDependencies.includes(svc.type)) mockDependencies.push(svc.type);
    suggestedMocks.push({ name: svc.type, type: "injected_service" });
  }

  // Accessibility
  if (comp.accessibility && (
    Object.keys(comp.accessibility.aria_attributes || {}).length > 0 ||
    (comp.accessibility.roles || []).length > 0
  )) {
    categories.push("Accessibility");
    edgeCases.push("Aria role and keyboard accessibility assertions");
  }

  // Template event bindings
  if (comp.template_bindings && (comp.template_bindings.event_bindings || []).length > 0) {
    categories.push("Events");
    for (const eb of comp.template_bindings.event_bindings) interactiveElements.push(eb);
  }

  // Recommended queries
  if (comp.selector) {
    recommendedQueries.push({ query: "By.css", target: comp.selector, name: comp.name });
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
    } else if (entry.isFile() && entry.name.endsWith(".ts") && !entry.name.endsWith(".d.ts")) {
      fileList.push(fullPath);
    }
  }
  return fileList;
}

function isTestFile(filePath) {
  return /\.spec\.ts$/.test(filePath);
}

// -------------------------------------------------------------------------
// TypeScript AST helpers
// -------------------------------------------------------------------------

function getDecoratorName(decorator) {
  const expr = ts.isCallExpression(decorator.expression) ? decorator.expression.expression : decorator.expression;
  if (ts.isIdentifier(expr)) return expr.text;
  if (ts.isPropertyAccessExpression(expr)) return expr.name.text;
  return null;
}

function getDecoratorArguments(decorator) {
  if (!ts.isCallExpression(decorator.expression)) return {};
  const args = decorator.expression.arguments;
  if (args.length === 0) return {};
  const firstArg = args[0];
  if (ts.isObjectLiteralExpression(firstArg)) {
    return objectLiteralToDict(firstArg);
  }
  return {};
}

function objectLiteralToDict(node) {
  const result = {};
  for (const prop of node.properties) {
    if (ts.isPropertyAssignment(prop) && ts.isIdentifier(prop.name)) {
      const key = prop.name.text;
      result[key] = nodeToValue(prop.initializer);
    }
  }
  return result;
}

function nodeToValue(node) {
  if (ts.isStringLiteral(node)) return node.text;
  if (ts.isNumericLiteral(node)) return Number(node.text);
  if (node.kind === ts.SyntaxKind.TrueKeyword) return true;
  if (node.kind === ts.SyntaxKind.FalseKeyword) return false;
  if (node.kind === ts.SyntaxKind.NullKeyword) return null;
  if (ts.isArrayLiteralExpression(node)) return node.elements.map(nodeToValue);
  if (ts.isObjectLiteralExpression(node)) return objectLiteralToDict(node);
  if (ts.isIdentifier(node)) return node.text;
  // Fallback: return the source text
  return node.getText ? node.getText() : String(node);
}

function getDecorators(node) {
  // TS 5.x: modifiers include decorators
  const decorators = [];
  if (node.modifiers) {
    for (const mod of node.modifiers) {
      if (ts.isDecorator(mod)) {
        decorators.push(mod);
      }
    }
  }
  // Older TS: node.decorators
  if (node.decorators) {
    for (const d of node.decorators) {
      if (!decorators.includes(d)) decorators.push(d);
    }
  }
  return decorators;
}

function getTypeString(typeNode) {
  if (!typeNode) return "any";
  if (typeNode.getText) return typeNode.getText();
  return "any";
}

// -------------------------------------------------------------------------
// Component extraction
// -------------------------------------------------------------------------

function extractComponent(classNode, sourceFile, projectRoot) {
  const filePath = path.relative(projectRoot, sourceFile.fileName).replace(/\\/g, "/");
  const name = classNode.name ? classNode.name.text : "AnonymousComponent";
  const decorators = getDecorators(classNode);
  const componentDecorator = decorators.find((d) => getDecoratorName(d) === "Component");

  if (!componentDecorator) return null;

  const decoratorArgs = getDecoratorArguments(componentDecorator);

  const component = {
    file_path: filePath,
    name,
    selector: decoratorArgs.selector || null,
    template_file: decoratorArgs.templateUrl || null,
    style_files: decoratorArgs.styleUrls || decoratorArgs.styleUrl ? [decoratorArgs.styleUrl || decoratorArgs.styleUrls].flat() : [],
    decorators: extractDecoratorInfos(decorators),
    inputs: [],
    outputs: [],
    injected_services: [],
    reactive_forms: [],
    template_bindings: null,
    methods: [],
    lifecycle_hooks: [],
    imports: extractImports(sourceFile),
    exports: extractExports(sourceFile),
  };

  // Walk class members
  for (const member of classNode.members) {
    // Constructor → DI
    if (ts.isConstructorDeclaration(member)) {
      for (const param of member.parameters) {
        if (param.type && ts.isIdentifier(param.name)) {
          component.injected_services.push({
            name: param.name.text,
            type: getTypeString(param.type),
          });
        }
      }
    }

    // Properties
    if (ts.isPropertyDeclaration(member)) {
      const memberDecorators = getDecorators(member);
      const memberName = member.name && ts.isIdentifier(member.name) ? member.name.text : null;

      // @Input()
      if (memberDecorators.some((d) => getDecoratorName(d) === "Input")) {
        const inputDecorator = memberDecorators.find((d) => getDecoratorName(d) === "Input");
        const inputArgs = getDecoratorArguments(inputDecorator);
        component.inputs.push({
          name: memberName || "unknown",
          type: member.type ? getTypeString(member.type) : "any",
          alias: inputArgs.alias || null,
          required: inputArgs.required || false,
        });
      }

      // @Output()
      if (memberDecorators.some((d) => getDecoratorName(d) === "Output")) {
        component.outputs.push({
          name: memberName || "unknown",
          type: member.type ? getTypeString(member.type) : "EventEmitter",
        });
      }

      // Reactive forms (FormGroup / FormControl)
      if (member.initializer) {
        const initText = member.initializer.getText ? member.initializer.getText() : "";
        if (initText.includes("FormGroup") || initText.includes("FormBuilder") || initText.includes("FormControl")) {
          const formInfo = extractReactiveForm(memberName, member.initializer);
          if (formInfo) component.reactive_forms.push(formInfo);
        }
      }
    }

    // Methods
    if (ts.isMethodDeclaration(member) && member.name) {
      const methodName = ts.isIdentifier(member.name) ? member.name.text : member.name.getText ? member.name.getText() : "unknown";

      // Lifecycle hooks
      const lifecycleHooks = [
        "ngOnInit", "ngOnDestroy", "ngOnChanges", "ngDoCheck",
        "ngAfterContentInit", "ngAfterContentChecked",
        "ngAfterViewInit", "ngAfterViewChecked",
      ];
      if (lifecycleHooks.includes(methodName)) {
        component.lifecycle_hooks.push(methodName);
      } else if (methodName !== "constructor") {
        component.methods.push({
          name: methodName,
          params: member.parameters.map((p) => ts.isIdentifier(p.name) ? p.name.text : "unknown"),
          is_async: !!member.modifiers?.some((m) => m.kind === ts.SyntaxKind.AsyncKeyword),
        });
      }
    }
  }

  // Parse external template if available
  let templateHtml = null;
  if (component.template_file) {
    const templatePath = path.resolve(path.dirname(sourceFile.fileName), component.template_file);
    component.template_bindings = parseTemplate(templatePath);
    try { templateHtml = fs.readFileSync(templatePath, "utf-8"); } catch { /* ignore */ }
  }

  // Check for inline template
  if (decoratorArgs.template && typeof decoratorArgs.template === "string") {
    component.template_bindings = parseTemplateString(decoratorArgs.template);
    templateHtml = decoratorArgs.template;
  }

  // ---- New enrichment: accessibility from template ----
  if (templateHtml) {
    component.accessibility = extractAccessibilityFromHtml(templateHtml);
    // child_components filled in main() after all selectors known
    component._raw_template_html = templateHtml; // temp storage, removed in main()
  } else {
    component.accessibility = {
      aria_attributes: {}, roles: [], keyboard_events: [],
      has_focus_management: false, alt_texts: [], label_associations: [], accessible_elements: [],
    };
  }

  // ---- New enrichment: API calls in component methods (from method bodies) ----
  component.api_calls = [];
  for (const member of classNode.members) {
    if (ts.isMethodDeclaration(member) && member.body) {
      const calls = extractApiCallsFromMethod(member);
      component.api_calls.push(...calls);
    }
  }

  // ---- New enrichment: dependency graph ----
  component.dependency_graph = buildAngularDependencyNode(name, component.imports);

  // testing_metadata filled in main() after all components known
  component.testing_metadata = null;
  component.child_components = [];

  return component;
}

// -------------------------------------------------------------------------
// Service extraction
// -------------------------------------------------------------------------

function extractService(classNode, sourceFile, projectRoot) {
  const filePath = path.relative(projectRoot, sourceFile.fileName).replace(/\\/g, "/");
  const name = classNode.name ? classNode.name.text : "AnonymousService";
  const decorators = getDecorators(classNode);
  const injectableDecorator = decorators.find((d) => getDecoratorName(d) === "Injectable");

  if (!injectableDecorator) return null;

  const decoratorArgs = getDecoratorArguments(injectableDecorator);

  const service = {
    file_path: filePath,
    name,
    decorators: extractDecoratorInfos(decorators),
    provided_in: decoratorArgs.providedIn || null,
    methods: [],
    injected_services: [],
    // New enrichment
    api_calls: [],
  };

  for (const member of classNode.members) {
    if (ts.isConstructorDeclaration(member)) {
      for (const param of member.parameters) {
        if (param.type && ts.isIdentifier(param.name)) {
          service.injected_services.push({
            name: param.name.text,
            type: getTypeString(param.type),
          });
        }
      }
    }

    if (ts.isMethodDeclaration(member) && member.name) {
      const methodName = ts.isIdentifier(member.name) ? member.name.text : "unknown";
      if (methodName !== "constructor") {
        service.methods.push({
          name: methodName,
          params: member.parameters.map((p) => ts.isIdentifier(p.name) ? p.name.text : "unknown"),
          is_async: !!member.modifiers?.some((m) => m.kind === ts.SyntaxKind.AsyncKeyword),
        });
        // ---- New enrichment: extract API calls from method body ----
        if (member.body) {
          const calls = extractApiCallsFromMethod(member);
          service.api_calls.push(...calls);
        }
      }
    }
  }

  return service;
}

// -------------------------------------------------------------------------
// Module extraction
// -------------------------------------------------------------------------

function extractModule(classNode, sourceFile, projectRoot) {
  const filePath = path.relative(projectRoot, sourceFile.fileName).replace(/\\/g, "/");
  const name = classNode.name ? classNode.name.text : "AnonymousModule";
  const decorators = getDecorators(classNode);
  const ngModuleDecorator = decorators.find((d) => getDecoratorName(d) === "NgModule");

  if (!ngModuleDecorator) return null;

  const args = getDecoratorArguments(ngModuleDecorator);

  return {
    file_path: filePath,
    name,
    declarations: toStringArray(args.declarations),
    imports: toStringArray(args.imports),
    providers: toStringArray(args.providers),
    exports: toStringArray(args.exports),
  };
}

// -------------------------------------------------------------------------
// Routing extraction
// -------------------------------------------------------------------------

function extractRoutes(sourceFile, projectRoot) {
  const routes = [];

  function visit(node) {
    // Look for: const routes: Routes = [ ... ]
    if (ts.isVariableDeclaration(node) && node.initializer && ts.isArrayLiteralExpression(node.initializer)) {
      const typeText = node.type ? node.type.getText() : "";
      if (typeText === "Routes" || (node.name && ts.isIdentifier(node.name) && /routes/i.test(node.name.text))) {
        for (const element of node.initializer.elements) {
          if (ts.isObjectLiteralExpression(element)) {
            const route = objectLiteralToDict(element);
            routes.push({
              path: route.path || "",
              component: route.component || null,
              guard: route.canActivate ? String(route.canActivate) : null,
              lazy_loaded: !!route.loadChildren || !!route.loadComponent,
            });
          }
        }
      }
    }
    ts.forEachChild(node, visit);
  }

  visit(sourceFile);
  return routes;
}

// -------------------------------------------------------------------------
// Template parsing (@angular/compiler)
// -------------------------------------------------------------------------

function parseTemplate(templatePath) {
  if (!fs.existsSync(templatePath)) return null;
  try {
    const html = fs.readFileSync(templatePath, "utf-8");
    return parseTemplateString(html);
  } catch {
    return null;
  }
}

function parseTemplateString(html) {
  const bindings = {
    property_bindings: [],
    event_bindings: [],
    interpolations: [],
    structural_directives: [],
  };

  if (angularCompiler) {
    try {
      const parsed = angularCompiler.parseTemplate(html, "template.html", {
        preserveWhitespaces: false,
      });

      visitTemplateNodes(parsed.nodes, bindings);
      return bindings;
    } catch {
      // Fall through to regex-based extraction
    }
  }

  // Fallback: regex-based extraction when @angular/compiler is unavailable
  const propBindingRe = /\[([^\]]+)\]/g;
  const eventBindingRe = /\(([^)]+)\)/g;
  const interpolationRe = /\{\{([^}]+)\}\}/g;
  const structuralRe = /\*([a-zA-Z]+)/g;

  let match;
  while ((match = propBindingRe.exec(html)) !== null) {
    const binding = `[${match[1]}]`;
    if (!bindings.property_bindings.includes(binding)) bindings.property_bindings.push(binding);
  }
  while ((match = eventBindingRe.exec(html)) !== null) {
    const binding = `(${match[1]})`;
    if (!bindings.event_bindings.includes(binding)) bindings.event_bindings.push(binding);
  }
  while ((match = interpolationRe.exec(html)) !== null) {
    const expr = `{{ ${match[1].trim()} }}`;
    if (!bindings.interpolations.includes(expr)) bindings.interpolations.push(expr);
  }
  while ((match = structuralRe.exec(html)) !== null) {
    const directive = `*${match[1]}`;
    if (!bindings.structural_directives.includes(directive)) bindings.structural_directives.push(directive);
  }

  return bindings;
}

function visitTemplateNodes(nodes, bindings) {
  if (!nodes) return;
  for (const node of nodes) {
    // Element nodes
    if (node.inputs) {
      for (const input of node.inputs) {
        const binding = `[${input.name}]`;
        if (!bindings.property_bindings.includes(binding)) bindings.property_bindings.push(binding);
      }
    }
    if (node.outputs) {
      for (const output of node.outputs) {
        const binding = `(${output.name})`;
        if (!bindings.event_bindings.includes(binding)) bindings.event_bindings.push(binding);
      }
    }
    // Structural directives via template attributes
    if (node.templateAttrs) {
      for (const attr of node.templateAttrs) {
        const directive = `*${attr.name}`;
        if (!bindings.structural_directives.includes(directive)) bindings.structural_directives.push(directive);
      }
    }
    // Bound text / interpolations
    if (node.value && typeof node.value === "string" && /\{\{/.test(node.value)) {
      const interpolationRe = /\{\{([^}]+)\}\}/g;
      let match;
      while ((match = interpolationRe.exec(node.value)) !== null) {
        const expr = `{{ ${match[1].trim()} }}`;
        if (!bindings.interpolations.includes(expr)) bindings.interpolations.push(expr);
      }
    }
    // Recurse into children
    if (node.children) visitTemplateNodes(node.children, bindings);
  }
}

// -------------------------------------------------------------------------
// Shared helpers
// -------------------------------------------------------------------------

function extractDecoratorInfos(decorators) {
  return decorators.map((d) => ({
    name: getDecoratorName(d) || "unknown",
    arguments: getDecoratorArguments(d),
  }));
}

function extractImports(sourceFile) {
  const imports = [];
  ts.forEachChild(sourceFile, (node) => {
    if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
      const source = ts.isStringLiteral(node.moduleSpecifier) ? node.moduleSpecifier.text : "unknown";
      const specifiers = [];
      let isDefault = false;

      if (node.importClause) {
        if (node.importClause.name) {
          specifiers.push(node.importClause.name.text);
          isDefault = true;
        }
        if (node.importClause.namedBindings) {
          if (ts.isNamedImports(node.importClause.namedBindings)) {
            for (const el of node.importClause.namedBindings.elements) {
              specifiers.push(el.name.text);
            }
          } else if (ts.isNamespaceImport(node.importClause.namedBindings)) {
            specifiers.push(`* as ${node.importClause.namedBindings.name.text}`);
          }
        }
      }

      imports.push({ source, specifiers, is_default: isDefault });
    }
  });
  return imports;
}

function extractExports(sourceFile) {
  const exports = [];
  ts.forEachChild(sourceFile, (node) => {
    if (ts.isExportAssignment(node)) {
      exports.push({ name: "default", is_default: true });
    }
    // Exported class/function/variable
    if (node.modifiers && node.modifiers.some((m) => m.kind === ts.SyntaxKind.ExportKeyword)) {
      let name = "unknown";
      if (ts.isClassDeclaration(node) && node.name) name = node.name.text;
      else if (ts.isFunctionDeclaration(node) && node.name) name = node.name.text;
      else if (ts.isVariableStatement(node) && node.declarationList.declarations.length > 0) {
        const decl = node.declarationList.declarations[0];
        if (ts.isIdentifier(decl.name)) name = decl.name.text;
      }
      const isDefault = node.modifiers.some((m) => m.kind === ts.SyntaxKind.DefaultKeyword);
      exports.push({ name, is_default: isDefault });
    }
  });
  return exports;
}

function extractReactiveForm(name, initializer) {
  const controls = [];
  const validators = [];

  const text = initializer.getText ? initializer.getText() : "";

  // Extract control names from FormGroup({ ... })
  const controlRe = /['"](\w+)['"]\s*:/g;
  let match;
  while ((match = controlRe.exec(text)) !== null) {
    if (!controls.includes(match[1])) controls.push(match[1]);
  }

  // Extract validators
  const validatorRe = /Validators\.(\w+)/g;
  while ((match = validatorRe.exec(text)) !== null) {
    const v = `Validators.${match[1]}`;
    if (!validators.includes(v)) validators.push(v);
  }

  return { name: name || "form", controls, validators };
}

function toStringArray(value) {
  if (!value) return [];
  if (Array.isArray(value)) return value.map(String);
  return [String(value)];
}

// -------------------------------------------------------------------------
// Main entry point
// -------------------------------------------------------------------------

function main() {
  const projectPath = process.argv[2];
  if (!projectPath) {
    process.stderr.write("Usage: node angular_parser.js <project_path>\n");
    process.exit(1);
  }

  if (!fs.existsSync(projectPath) || !fs.statSync(projectPath).isDirectory()) {
    process.stderr.write(`Error: project path does not exist or is not a directory: ${projectPath}\n`);
    process.exit(1);
  }

  const allTsFiles = walkDir(projectPath);
  const sourceFiles = allTsFiles.filter((f) => !isTestFile(f));
  const testFiles = allTsFiles.filter((f) => isTestFile(f));

  const components = [];
  const services = [];
  const modules = [];
  let allRoutes = [];

  for (const filePath of sourceFiles) {
    let sourceFile;
    try {
      const code = fs.readFileSync(filePath, "utf-8");
      sourceFile = ts.createSourceFile(filePath, code, ts.ScriptTarget.Latest, true);
    } catch (err) {
      process.stderr.write(`Warning: failed to parse ${filePath}: ${err.message}\n`);
      continue;
    }

    // Extract routes from any file
    const fileRoutes = extractRoutes(sourceFile, projectPath);
    if (fileRoutes.length > 0) allRoutes.push(...fileRoutes);

    // Walk top-level declarations
    ts.forEachChild(sourceFile, (node) => {
      if (ts.isClassDeclaration(node)) {
        const decorators = getDecorators(node);
        const decoratorNames = decorators.map((d) => getDecoratorName(d));

        if (decoratorNames.includes("Component")) {
          const comp = extractComponent(node, sourceFile, projectPath);
          if (comp) components.push(comp);
        }

        if (decoratorNames.includes("Injectable")) {
          const svc = extractService(node, sourceFile, projectPath);
          if (svc) services.push(svc);
        }

        if (decoratorNames.includes("NgModule")) {
          const mod = extractModule(node, sourceFile, projectPath);
          if (mod) modules.push(mod);
        }
      }
    });
  }

  const existingTests = testFiles.map((f) => ({
    file_path: path.relative(projectPath, f).replace(/\\/g, "/"),
    type: "spec",
  }));

  // -----------------------------------------------------------------
  // Post-parse enrichment: child components, testing metadata, relationships
  // -----------------------------------------------------------------

  // Build a set of all known component selectors for child detection
  const knownSelectors = new Set(components.map((c) => c.selector).filter(Boolean));

  // 1. child_components + accessibility (using stored raw HTML)
  for (const comp of components) {
    const html = comp._raw_template_html || null;
    if (html) {
      comp.child_components = extractChildSelectorsFromHtml(html, knownSelectors);
    }
    delete comp._raw_template_html; // remove temp field
  }

  // 2. testing_metadata per component
  for (const comp of components) {
    comp.testing_metadata = buildAngularTestingMetadata(comp);
  }

  // 3. Component relationships
  const componentRelationships = [];
  const compNameToComp = {};
  for (const comp of components) { compNameToComp[comp.selector || comp.name] = comp; }

  for (const comp of components) {
    const rel = {
      component: comp.name,
      parent: null,
      children: comp.child_components || [],
      depth: 0,
    };
    componentRelationships.push(rel);
  }

  // Assign parents
  for (const comp of components) {
    for (const childSelector of comp.child_components || []) {
      const childComp = components.find((c) => c.selector === childSelector || c.name === childSelector);
      const childRel = componentRelationships.find((r) => r.component === (childComp ? childComp.name : childSelector));
      if (childRel && !childRel.parent) childRel.parent = comp.name;
      if (childComp && !childComp.parent_component) childComp.parent_component = comp.name;
    }
  }

  // Compute depth
  function assignDepthAngular(rel, depth, rels) {
    rel.depth = depth;
    for (const childSel of rel.children) {
      const childComp = components.find((c) => c.selector === childSel || c.name === childSel);
      if (childComp) {
        const childRel = rels.find((r) => r.component === childComp.name);
        if (childRel) assignDepthAngular(childRel, depth + 1, rels);
      }
    }
  }
  for (const root of componentRelationships.filter((r) => !r.parent)) {
    assignDepthAngular(root, 0, componentRelationships);
  }

  // 4. Dependency graph (one node per component + service)
  const dependencyGraph = [
    ...components.map((c) => c.dependency_graph || buildAngularDependencyNode(c.name, c.imports || [])),
    ...services.map((s) => buildAngularDependencyNode(s.name, [])),
  ];

  // 5. Test mapping
  const testMapping = [];
  for (const comp of components) {
    const matched = existingTests.find((t) => {
      const base = path.basename(t.file_path, ".spec.ts").replace(/\.spec$/, "");
      const baseClean = base.toLowerCase().replace(/[-_.]/g, "").replace("component", "");
      const compClean = comp.name.toLowerCase().replace(/[-_.]/g, "").replace("component", "");
      return baseClean === compClean;
    });

    let coveredFeatures = [];
    let testingFramework = null;

    if (matched) {
      const testFileFull = path.join(projectPath, matched.file_path);
      if (fs.existsSync(testFileFull)) {
        try {
          const testCode = fs.readFileSync(testFileFull, "utf-8");
          const labelRe = /(?:describe|it|test)\s*\(\s*['"`]([^'"`]+)['"`]/g;
          let m;
          while ((m = labelRe.exec(testCode)) !== null) {
            if (!coveredFeatures.includes(m[1])) coveredFeatures.push(m[1]);
          }
          if (testCode.includes("@angular/core/testing")) testingFramework = "jasmine+testbed";
          else if (testCode.includes("jest")) testingFramework = "jest+testbed";
          else testingFramework = "jasmine";
        } catch { /* ignore */ }
      }
    }

    testMapping.push({
      component: comp.name,
      test_file: matched ? matched.file_path : null,
      testing_framework: testingFramework,
      covered_features: coveredFeatures,
    });
  }

  // Clean up temp fields from components before output
  for (const comp of components) {
    delete comp.dependency_graph; // included in top-level dependencyGraph array
    delete comp.parent_component; // not tracked in Angular schema
  }

  const output = {
    components,
    services,
    modules,
    routing: allRoutes,
    existing_tests: existingTests,
    files_analyzed: sourceFiles.length,
    component_relationships: componentRelationships,
    dependency_graph: dependencyGraph,
    test_mapping: testMapping,
  };

  process.stdout.write(JSON.stringify(output, null, 0));
}

main();
