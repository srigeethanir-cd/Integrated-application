import os
import logging
from typing import Dict, List, Set, Tuple, Optional
from app.services.change_impact.dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)


class ImpactAnalyzer:
    """Calculates transitive change impact using dependency graphs."""

    def __init__(self, dep_analyzer: DependencyAnalyzer) -> None:
        self.dep_analyzer = dep_analyzer

    def analyze_changed_files(self, changed_files: List[str]) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
        """Determine impacted components and assign impact categories.

        Returns:
            impacted_components: Dict mapping component_name -> impact_level ("HIGH" | "MEDIUM" | "LOW")
            impact_reasons: Dict mapping component_name -> explanation reason string
            global_reasons: List of high-level project-wide reasons (e.g. unknown file changes)
        """
        impacted_components: Dict[str, str] = {}
        impact_reasons: Dict[str, str] = {}
        global_reasons: List[str] = []

        direct_components: Set[str] = set()
        direct_services: Set[str] = set()
        direct_routes: Set[str] = set()
        
        unknown_files: List[str] = []

        # 1. Map each changed file path to components, services, or routes
        for raw_file in changed_files:
            file_name = raw_file.replace("\\", "/").strip()
            
            # Check if this changed file maps directly to a component
            comp = self.dep_analyzer.get_component_by_file(file_name)
            if comp:
                direct_components.add(comp.name)
                impacted_components[comp.name] = "HIGH"
                impact_reasons[comp.name] = f"Direct modification to component file ({raw_file})"
                continue

            # Check if this maps to a service
            matched_service = False
            for service in self.dep_analyzer.ir.services:
                service_basename = os.path.splitext(os.path.basename(file_name))[0].lower()
                if service.name.lower() in service_basename or service_basename in service.name.lower():
                    direct_services.add(service.name)
                    matched_service = True
                    
            if matched_service:
                continue

            # Check if it maps to a route
            matched_route = False
            for route in self.dep_analyzer.ir.routes:
                route_basename = os.path.splitext(os.path.basename(file_name))[0].lower()
                if route.component and route_basename in route.component.lower():
                    direct_routes.add(route.path)
                    matched_route = True
            
            if matched_route:
                continue

            # Check if it's a component or router file generally by checking path parts
            if "component" in file_name.lower() or file_name.lower().endswith((".jsx", ".tsx", ".js", ".ts", ".html", ".css")):
                # Try finding component match by name matching
                base = os.path.splitext(os.path.basename(file_name))[0]
                matched = False
                for c_name in self.dep_analyzer.components_by_name:
                    if base.lower() in c_name.lower() or c_name.lower() in base.lower():
                        direct_components.add(c_name)
                        impacted_components[c_name] = "HIGH"
                        impact_reasons[c_name] = f"Potential match on modified source file ({raw_file})"
                        matched = True
                if matched:
                    continue

            # Otherwise, classify it as an unknown or global file
            unknown_files.append(raw_file)

        # 2. Propagate impact from directly modified services to components
        for service in direct_services:
            using_comps = self.dep_analyzer.service_to_components.get(service, set())
            for comp_name in using_comps:
                if comp_name not in impacted_components or impacted_components[comp_name] != "HIGH":
                    impacted_components[comp_name] = "HIGH"
                    impact_reasons[comp_name] = f"Directly utilizes modified service API ({service})"

        # 3. Propagate impact from directly modified routes to components
        for route_path in direct_routes:
            route_comps = self.dep_analyzer.route_to_components.get(route_path, set())
            for comp_name in route_comps:
                if comp_name not in impacted_components or impacted_components[comp_name] != "HIGH":
                    impacted_components[comp_name] = "HIGH"
                    impact_reasons[comp_name] = f"Under active route change for path '{route_path}'"

        # 4. Transitive Dependency propagation (BFS/DFS traversal)
        # We start with all HIGH impact components as our root queue
        queue = list(impacted_components.keys())
        visited = set(queue)

        while queue:
            current = queue.pop(0)
            current_level = impacted_components[current]
            
            # Find parent/dependent components that render or import this component
            dependents = self.dep_analyzer.get_parent_components(current)
            for dep in dependents:
                if dep not in visited:
                    visited.add(dep)
                    # Transitively affected gets MEDIUM impact (unless already marked HIGH)
                    if dep not in impacted_components:
                        impacted_components[dep] = "MEDIUM"
                        impact_reasons[dep] = f"Depends on modified component '{current}'"
                    queue.append(dep)

        # 5. Handle Global or Unknown changes safely
        # If config, package.json, or unknown files changed, trigger all tests as LOW priority.
        if unknown_files:
            global_reasons.append(f"Global configuration or asset modifications in: {', '.join(unknown_files[:3])}")
            for comp_name in self.dep_analyzer.components_by_name:
                if comp_name not in impacted_components:
                    impacted_components[comp_name] = "LOW"
                    impact_reasons[comp_name] = f"Triggered due to global configuration/file change"

        return impacted_components, impact_reasons, global_reasons
