"""
Angular IR Mapper – Module 4.

Maps Angular parser output from Module 3 into a framework-agnostic IR.

Normalizations:
- Angular Component → ComponentIR
- Angular HTML Template / Property Bindings → UIElement
- Angular (click)/(change)/(ngSubmit) & Outputs → UIEvent
- Angular FormControl/FormGroup → FormModel
- Angular HttpClient / Injected Services → ServiceDependency
- Angular Router → RouteModel
- Imports → Dependencies
- Existing Spec Tests → ExistingTestModel
"""

import logging
from typing import Any, Dict, List
from app.models.ir_models import (
    ComponentIR,
    ExistingTestModel,
    FormField,
    FormModel,
    FrameworkAgnosticIR,
    RouteModel,
    ServiceDependency,
    UIElement,
    UIEvent,
)
from app.models.analyzer_models import (
    AccessibilityInfo,
    TestingMetadata,
    DependencyNode,
    TestMapping,
    ComponentRelationshipInfo,
)
from app.services.ir_generator.base_mapper import BaseIRMapper

logger = logging.getLogger(__name__)


def generate_angular_locator(tag: str, role: str | None, aria_label: str | None, alt: str | None) -> str:
    """Generate preferred css locator string for Angular TestBed tests."""
    if aria_label:
        return f"by.css('[aria-label=\"{aria_label}\"]')"
    if alt:
        return f"by.css('[alt=\"{alt}\"]')"
    if role:
        return f"by.css('[role=\"{role}\"]')"
    return f"by.css('{tag}')"


class AngularIRMapper(BaseIRMapper):
    """Mapper implementation for Angular applications."""

    @property
    def framework_name(self) -> str:
        return "Angular"

    def map_to_ir(self, analysis_data: Dict[str, Any], project_name: str = "IngestedProject") -> FrameworkAgnosticIR:
        logger.info("AngularIRMapper: mapping analysis output to framework-agnostic IR")

        raw_analysis = analysis_data.get("analysis", {})
        if not isinstance(raw_analysis, dict):
            raw_analysis = analysis_data

        components_raw = raw_analysis.get("components", [])
        services_raw = raw_analysis.get("services", [])
        routes_raw = raw_analysis.get("routing", [])
        tests_raw = raw_analysis.get("existing_tests", [])

        # Read top level collection fields
        component_relationships_raw = raw_analysis.get("component_relationships", [])
        dependency_graph_raw = raw_analysis.get("dependency_graph", [])
        test_mapping_raw = raw_analysis.get("test_mapping", [])

        ir_components: List[ComponentIR] = []
        ir_elements: List[UIElement] = []
        ir_events: List[UIEvent] = []
        ir_forms: List[FormModel] = []
        ir_services: List[ServiceDependency] = []
        ir_routes: List[RouteModel] = []
        ir_dependencies: List[Dict[str, Any]] = []

        seen_deps = set()

        # 1. Map Components
        for comp in components_raw:
            comp_name = comp.get("name", "UnknownComponent")
            file_path = comp.get("file_path", "")
            selector = comp.get("selector", "app-component")
            inputs = comp.get("inputs", [])
            outputs = comp.get("outputs", [])
            comp_id = f"comp_{comp_name}"

            # Compute parent / children depth mapping
            rel = next((r for r in component_relationships_raw if r.get("component") == comp_name), {})
            parent_name = rel.get("parent")
            parent_id = f"comp_{parent_name}" if parent_name else None
            children_names = rel.get("children", [])
            children_ids = [f"comp_{c}" for c in children_names]
            depth = rel.get("depth", 0)

            # Compute accessibility metadata model
            acc_raw = comp.get("accessibility")
            accessibility = None
            if acc_raw:
                accessibility = AccessibilityInfo(
                    aria_attributes=acc_raw.get("aria_attributes", {}),
                    roles=acc_raw.get("roles", []),
                    keyboard_events=acc_raw.get("keyboard_events", []),
                    has_focus_management=acc_raw.get("has_focus_management", False),
                    alt_texts=acc_raw.get("alt_texts", []),
                    label_associations=acc_raw.get("label_associations", []),
                    accessible_elements=acc_raw.get("accessible_elements", [])
                )

            # Compute testing metadata model
            tm_raw = comp.get("testing_metadata")
            testing_metadata = None
            if tm_raw:
                testing_metadata = TestingMetadata(
                    testable_elements=tm_raw.get("testable_elements", []),
                    interactive_elements=tm_raw.get("interactive_elements", []),
                    mock_dependencies=tm_raw.get("mock_dependencies", []),
                    recommended_test_categories=tm_raw.get("recommended_test_categories", []),
                    recommended_queries=[dict(q) for q in tm_raw.get("recommended_queries", [])],
                    edge_cases=tm_raw.get("edge_cases", []),
                    negative_scenarios=tm_raw.get("negative_scenarios", []),
                    suggested_mocks=[dict(m) for m in tm_raw.get("suggested_mocks", [])]
                )

            # Compute dependency graph node model
            dg_raw = comp.get("dependency_graph")
            dependency_graph = None
            if dg_raw:
                dependency_graph = DependencyNode(
                    component=dg_raw.get("component", comp_name),
                    imports_components=dg_raw.get("imports_components", []),
                    imports_services=dg_raw.get("imports_services", []),
                    imports_utilities=dg_raw.get("imports_utilities", []),
                    imports_contexts=dg_raw.get("imports_contexts", []),
                    imports_hooks=dg_raw.get("imports_hooks", []),
                    imports_stores=dg_raw.get("imports_stores", []),
                    imports_external_libraries=dg_raw.get("imports_external_libraries", [])
                )

            # Map Reactive Forms -> FormModel & FormField
            comp_forms = []
            for form in comp.get("reactive_forms", []):
                form_name = form.get("name", "form")
                form_id = f"form_{comp_name}_{form_name}"
                controls_raw = form.get("controls", [])
                validators = form.get("validators", [])

                fields = []
                for idx, ctrl in enumerate(controls_raw):
                    field_id = f"field_{comp_name}_{form_name}_{ctrl}"
                    fields.append(
                        FormField(
                            name=ctrl,
                            type="control",
                            validators=validators,
                            id=field_id,
                            is_controlled=True,
                            is_required="required" in [v.lower() for v in validators],
                            validation_rules=validators
                        )
                    )

                comp_forms.append(
                    FormModel(
                        name=form_name,
                        component_name=comp_name,
                        controls=fields,
                        validators=validators,
                        id=form_id,
                        element="form",
                        is_controlled=True,
                        submit_handler="onSubmit",
                        reset_handler=None,
                        library="reactive"
                    )
                )
                ir_forms.append(comp_forms[-1])

            # Risk Score Calculation
            risk_score = 1.0
            risk_score += 0.5 * (len(inputs) + len(outputs))
            template = comp.get("template_bindings") or {}
            event_bindings = template.get("event_bindings", [])
            risk_score += 1.0 * len(event_bindings)
            risk_score += 1.0 * len(comp.get("injected_services", []))
            risk_score += 2.0 * len(comp_forms)
            risk_score += 2.0 * len(comp.get("api_calls", []))
            if acc_raw and (acc_raw.get("aria_attributes") or acc_raw.get("roles")):
                risk_score += 0.5

            ir_components.append(
                ComponentIR(
                    name=comp_name,
                    file_path=file_path,
                    type="angular_component",
                    props_inputs=inputs,
                    outputs_events=outputs,
                    id=comp_id,
                    parent_id=parent_id,
                    children_ids=children_ids,
                    depth=depth,
                    risk_score=risk_score,
                    accessibility=accessibility,
                    testing_metadata=testing_metadata,
                    dependency_graph=dependency_graph,
                    forms=comp_forms
                )
            )

            # Map template bindings to UIElement
            prop_bindings = template.get("property_bindings", [])
            directives = template.get("structural_directives", [])
            interpolations = template.get("interpolations", [])
            all_attrs = prop_bindings + directives + interpolations

            if selector or all_attrs:
                element_id = f"elem_{comp_name}_{selector or 'component'}_0"
                aria_label = None
                alt = None
                role = None
                
                # Try to extract alt, role, aria-label if found in attributes or accessibility
                if acc_raw:
                    aria_attrs = acc_raw.get("aria_attributes", {})
                    # Find first key in aria_attrs
                    for k, v in aria_attrs.items():
                        if "label" in k:
                            aria_label = v
                            break
                    if acc_raw.get("roles"):
                        role = acc_raw.get("roles")[0]
                    if acc_raw.get("alt_texts"):
                        alt = acc_raw.get("alt_texts")[0]

                ang_loc = generate_angular_locator(selector or "component", role, aria_label, alt)
                rtl_loc = f"screen.getByRole({repr(role)})" if role else f"container.querySelector({repr(selector)})"

                ir_elements.append(
                    UIElement(
                        tag=selector or "component",
                        component_name=comp_name,
                        attributes=all_attrs,
                        children_count=0,
                        id=element_id,
                        class_name=None,
                        role=role,
                        aria_label=aria_label,
                        placeholder=None,
                        alt=alt,
                        disabled=None,
                        required=None,
                        value_binding=None,
                        event_bindings=[],
                        locator_rtl=rtl_loc,
                        locator_angular=ang_loc,
                        locator_fallback=selector or "component",
                        assertion_hints=["Visible"]
                    )
                )

            # Map event bindings & outputs -> UIEvent
            for idx, eb in enumerate(event_bindings):
                clean_name = eb.strip("()").strip()
                event_id = f"evt_{comp_name}_on_{clean_name}_{idx}"
                
                target_element_id = ir_elements[-1].id if ir_elements else None

                ir_events.append(
                    UIEvent(
                        name=eb,
                        event_type=clean_name,
                        component_name=comp_name,
                        handler_name=f"on_{clean_name}",
                        id=event_id,
                        target_element_id=target_element_id,
                        updates_states=[],
                        service_calls=[],
                        navigation=False,
                        prevent_default=False,
                        stop_propagation=False,
                        assertion_hints=["Callback invoked"]
                    )
                )

            for idx, out in enumerate(outputs):
                out_name = out.get("name", "output")
                event_id = f"evt_{comp_name}_{out_name}_{idx}"
                ir_events.append(
                    UIEvent(
                        name=out_name,
                        event_type="output_emitter",
                        component_name=comp_name,
                        handler_name=out_name,
                        id=event_id,
                        target_element_id=None,
                        updates_states=[],
                        service_calls=[],
                        navigation=False,
                        prevent_default=False,
                        stop_propagation=False,
                        assertion_hints=["Callback invoked"]
                    )
                )

            # Map injected services -> ServiceDependency
            for inj in comp.get("injected_services", []):
                svc_name = inj.get("name", "service")
                svc_type = inj.get("type", "InjectedService")
                svc_id = f"svc_{comp_name}_{svc_type}"
                ir_services.append(
                    ServiceDependency(
                        name=svc_type,
                        component_name=comp_name,
                        type="injected_service",
                        methods=[svc_name],
                        id=svc_id,
                        api_calls=[]
                    )
                )

            # Map component-level API calls
            for api in comp.get("api_calls", []):
                fn_name = api.get("function_name", "apiCall")
                call_type = api.get("type", "service_call")
                svc_id = f"svc_{comp_name}_{fn_name}"
                ir_services.append(
                    ServiceDependency(
                        name=fn_name,
                        component_name=comp_name,
                        type=call_type,
                        methods=[fn_name],
                        id=svc_id,
                        api_calls=[api]
                    )
                )

            # Map imports -> dependencies
            for imp in comp.get("imports", []):
                src = imp.get("source", "")
                if src and src not in seen_deps:
                    seen_deps.add(src)
                    ir_dependencies.append(
                        {
                            "source": src,
                            "specifiers": imp.get("specifiers", []),
                            "is_default": imp.get("is_default", False),
                        }
                    )

        # 2. Map Standalone Angular Services
        for svc in services_raw:
            svc_name = svc.get("name", "Service")
            methods = [m.get("name") for m in svc.get("methods", []) if m.get("name")]
            svc_id = f"svc_global_{svc_name}"
            
            # Map API calls in this service
            api_calls = svc.get("api_calls", [])
            
            ir_services.append(
                ServiceDependency(
                    name=svc_name,
                    component_name=None,
                    type="angular_service",
                    methods=methods,
                    id=svc_id,
                    api_calls=api_calls
                )
            )

        # 3. Map Routes
        for r in routes_raw:
            clean_path = r.get("path", "").replace("/", "_").strip("_") or "root"
            route_id = f"route_{clean_path}"
            ir_routes.append(
                RouteModel(
                    path=r.get("path", ""),
                    component=r.get("component"),
                    guard=r.get("guard"),
                    lazy_loaded=r.get("lazy_loaded", False),
                    id=route_id,
                    redirects=[],
                    route_params=[]
                )
            )

        # 4. Map Existing Tests
        ir_tests = [
            ExistingTestModel(file_path=t.get("file_path", ""), type=t.get("type", "spec"))
            for t in tests_raw
        ]

        # 5. Top-level mapping collections
        component_relationships = [
            ComponentRelationshipInfo(
                component=r.get("component"),
                parent=r.get("parent"),
                children=r.get("children", []),
                depth=r.get("depth", 0)
            )
            for r in component_relationships_raw
        ]

        dependency_graph = [
            DependencyNode(
                component=d.get("component"),
                imports_components=d.get("imports_components", []),
                imports_services=d.get("imports_services", []),
                imports_utilities=d.get("imports_utilities", []),
                imports_contexts=d.get("imports_contexts", []),
                imports_hooks=d.get("imports_hooks", []),
                imports_stores=d.get("imports_stores", []),
                imports_external_libraries=d.get("imports_external_libraries", [])
            )
            for d in dependency_graph_raw
        ]

        test_mapping = [
            TestMapping(
                component=t.get("component"),
                test_file=t.get("test_file"),
                testing_framework=t.get("testing_framework"),
                covered_features=t.get("covered_features", [])
            )
            for t in test_mapping_raw
        ]

        ir = FrameworkAgnosticIR(
            project_name=project_name,
            framework=analysis_data.get("framework", "Angular"),
            components=ir_components,
            elements=ir_elements,
            events=ir_events,
            state=[],
            forms=ir_forms,
            services=ir_services,
            routes=ir_routes,
            dependencies=ir_dependencies,
            existing_tests=ir_tests,
            component_relationships=component_relationships,
            dependency_graph=dependency_graph,
            test_mapping=test_mapping
        )

        logger.info(
            "AngularIRMapper complete: %d components, %d forms, %d services, %d routes mapped",
            len(ir.components),
            len(ir.forms),
            len(ir.services),
            len(ir.routes),
        )
        return ir
