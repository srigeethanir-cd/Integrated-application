import logging
import os
from typing import Dict, List, Set, Optional
from app.models.ir_models import FrameworkAgnosticIR, ComponentIR

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Deterministic graph representation of component and module dependencies."""

    def __init__(self, ir: FrameworkAgnosticIR) -> None:
        self.ir = ir
        self.components_by_name: Dict[str, ComponentIR] = {}
        self.components_by_file: Dict[str, ComponentIR] = {}
        self.parent_to_children: Dict[str, List[str]] = {}
        self.child_to_parent: Dict[str, str] = {}
        
        # Dependency mappings
        self.imports_components: Dict[str, Set[str]] = {}  # comp -> set of comp names it imports
        self.imported_by: Dict[str, Set[str]] = {}          # comp -> set of comps importing it
        
        self.service_to_components: Dict[str, Set[str]] = {}  # service_name -> set of comps using it
        self.route_to_components: Dict[str, Set[str]] = {}    # route_path -> set of comps rendered
        
        self._build_graph()

    def _normalize_path(self, path: str) -> str:
        """Helper to normalize path separators for safe cross-platform comparisons."""
        if not path:
            return ""
        return path.replace("\\", "/").lower().strip("./")

    def _build_graph(self) -> None:
        """Analyze IR component data and construct directed dependency relationship graphs."""
        # 1. Map components by name and source file
        for comp in self.ir.components:
            self.components_by_name[comp.name] = comp
            if comp.file_path:
                self.components_by_file[self._normalize_path(comp.file_path)] = comp
            if comp.source_file:
                self.components_by_file[self._normalize_path(comp.source_file)] = comp

            self.imports_components[comp.name] = set()
            self.imported_by[comp.name] = set()

        # 2. Build parent-child relationships
        for relation in self.ir.component_relationships:
            parent = relation.parent
            child = relation.component
            if parent and child:
                self.child_to_parent[child] = parent
                if parent not in self.parent_to_children:
                    self.parent_to_children[parent] = []
                self.parent_to_children[parent].append(child)
                
                # Also treat parent rendering child as a dependency
                if parent in self.imports_components:
                    self.imports_components[parent].add(child)
                if child in self.imported_by:
                    self.imported_by[child].add(parent)

        # 3. Build imports graph from dependency_graph nodes
        dep_nodes = self.ir.dependency_graph
        for node in dep_nodes:
            comp_name = node.component
            if comp_name not in self.imports_components:
                self.imports_components[comp_name] = set()

            # Process component imports
            for imported_comp in node.imports_components:
                self.imports_components[comp_name].add(imported_comp)
                if imported_comp not in self.imported_by:
                    self.imported_by[imported_comp] = set()
                self.imported_by[imported_comp].add(comp_name)

            # Process service imports
            for service in node.imports_services:
                if service not in self.service_to_components:
                    self.service_to_components[service] = set()
                self.service_to_components[service].add(comp_name)

        # 4. Map routes to components
        for route in self.ir.routes:
            if route.component:
                if route.path not in self.route_to_components:
                    self.route_to_components[route.path] = set()
                self.route_to_components[route.path].add(route.component)

    def get_component_by_file(self, file_path: str) -> Optional[ComponentIR]:
        """Find corresponding component by its source file path."""
        norm_path = self._normalize_path(file_path)
        
        # Direct lookup
        if norm_path in self.components_by_file:
            return self.components_by_file[norm_path]
            
        # Partial match: if the path ends with any registered component's path
        for comp_file, comp in self.components_by_file.items():
            if norm_path.endswith(comp_file) or comp_file.endswith(norm_path):
                return comp
                
        # Fallback check by basename
        base_name = os.path.splitext(os.path.basename(file_path))[0].lower()
        for name, comp in self.components_by_name.items():
            if name.lower() == base_name:
                return comp
                
        return None

    def get_parent_components(self, component_name: str) -> Set[str]:
        """Get the set of components that render or import the target component directly."""
        parents = set()
        # Direct parent relations
        p = self.child_to_parent.get(component_name)
        if p:
            parents.add(p)
        # Import relations
        if component_name in self.imported_by:
            parents.update(self.imported_by[component_name])
        return parents
