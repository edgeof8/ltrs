# dependency_manager.py
from __future__ import annotations
from typing import Set, Dict
import re
from config import VARIABLE_REGEX
from gui_items.calculation_node import CalculationNode
from gui_items.plot_node import PlotNode

class DependencyGraphManager:
    def __init__(self):
        self.dependencies: Dict[str, Set[CalculationNode | PlotNode]] = {}
        self.node_definitions: Dict[CalculationNode | PlotNode, str] = {}

    def update_dependencies_for_node(self, node: CalculationNode | PlotNode) -> None:
        """
        Updates the dependency graph for a given node, tracking which variables it depends on
        and whether it defines a variable.
        """
        if node in self.node_definitions:
            old_var_name = self.node_definitions.pop(node)
            # Note: Calculator variable deletion is handled elsewhere if needed

        if hasattr(node, 'dependencies') and node.dependencies:
            for var in node.dependencies:
                if var in self.dependencies:
                    self.dependencies[var].discard(node)

        if isinstance(node, CalculationNode):
            match = re.match(r"^\s*(\$[a-zA-Z_]\w*)\s*=", node.expression_str)
            if match:
                node.defined_variable = match.group(1)
                if node.defined_variable is not None:
                    self.node_definitions[node] = node.defined_variable
            else:
                node.defined_variable = None
                if node in self.node_definitions:
                    del self.node_definitions[node]
            node.dependencies = set(VARIABLE_REGEX.findall(node.expression_str))
        elif isinstance(node, PlotNode):
            node.defined_variable = None
            node.dependencies = set(VARIABLE_REGEX.findall(node.expression) +
                                   VARIABLE_REGEX.findall(node.start_val) +
                                   VARIABLE_REGEX.findall(node.end_val))

        for var in node.dependencies:
            var_name = f"${var}"
            if var_name not in self.dependencies:
                self.dependencies[var_name] = set()
            self.dependencies[var_name].add(node)

    def get_dependents(self, var_name: str) -> Set[CalculationNode | PlotNode]:
        """
        Returns the set of nodes that depend on the given variable name.
        """
        return self.dependencies.get(var_name, set())

    def clear(self) -> None:
        """
        Resets the dependency graph and node definitions.
        """
        self.dependencies.clear()
        self.node_definitions.clear()
