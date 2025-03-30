#!/usr/bin/env python3
import json
import argparse
from graphviz import Digraph
import webbrowser
from pathlib import Path

class DependencyVisualizer:
    def __init__(self):
        self.parser = self.setup_parser()
        self.args = self.parser.parse_args()
        self.data = self.load_data()
        
    def setup_parser(self):
        parser = argparse.ArgumentParser(description='Dependency Tree Visualizer')
        parser.add_argument('input', help='JSON input file')
        parser.add_argument('-o', '--output', help='Output file name (without extension)')
        parser.add_argument('-f', '--format', default='png', 
                          choices=['png', 'svg', 'pdf', 'jpg', 'html'],
                          help='Output format')
        parser.add_argument('--vertical', action='store_true', 
                          help='Use vertical layout')
        parser.add_argument('--open', action='store_true',
                          help='Open visualization after generation')
        parser.add_argument('--theme', default='light',
                          choices=['light', 'dark'],
                          help='Color theme for visualization')
        return parser
        
    def load_data(self):
        with open(self.args.input) as f:
            return json.load(f)
    
    def generate_graphviz(self):
        """Generate Graphviz visualization with enhanced shapes"""
        graph = Digraph(
            name='Dependency Tree',
            format=self.args.format if self.args.format != 'html' else 'png',
            graph_attr={
                'rankdir': 'TB' if self.args.vertical else 'LR',
                'splines': 'ortho',
                'nodesep': '0.8',
                'ranksep': '1.2',
                'bgcolor': '#2d2d2d' if self.args.theme == 'dark' else '#ffffff',
            },
            node_attr={
                'style': 'filled',
                'fontname': 'Helvetica',
                'fontsize': '10',
                'penwidth': '1.5'
            },
            edge_attr={
                'arrowsize': '0.8',
                'penwidth': '1.5',
                'color': '#a0a0a0'
            }
        )
        
        # Add nodes and edges with enhanced shapes
        self.add_nodes_and_edges(graph)
        
        # Render graph
        output_name = self.args.output or Path(self.args.input).stem
        graph.render(filename=output_name, cleanup=True, view=False)
        
        if self.args.open and self.args.format != 'html':
            webbrowser.open(f'{output_name}.{self.args.format}')
            
        return graph
    
    def add_nodes_and_edges(self, graph):
        """Add nodes with type-specific shapes and styling"""
        def process_node(node, parent=None):
            node_id = node.get('id', str(id(node)))
            label = node.get('name', node_id)
            node_type = node.get('type', 'default').lower()
            
            # Node attributes based on type
            node_attrs = {
                'shape': self.get_shape_for_type(node_type),
                'fillcolor': self.get_color_for_type(node_type),
                'fontcolor': self.get_font_color(node_type),
                'color': self.get_border_color(node_type)
            }
            
            # Special handling for certain node types
            if node_type == 'database':
                node_attrs['height'] = '1.2'
                node_attrs['width'] = '1.8'
            elif node_type == 'proxy':
                node_attrs['shape'] = 'diamond'
            elif node_type == 'queue':
                node_attrs['shape'] = 'note'
            
            graph.node(node_id, label, **node_attrs)
            
            if parent:
                graph.edge(parent, node_id)
                
            for child in node.get('dependencies', []):
                process_node(child, node_id)
        
        if isinstance(self.data, list):
            for item in self.data:
                process_node(item)
        else:
            process_node(self.data)
    
    def get_shape_for_type(self, node_type):
        """Return appropriate shape for each node type"""
        shapes = {
            'database': 'cylinder',
            'api': 'component',
            'service': 'box3d',
            'proxy': 'diamond',
            'queue': 'note',
            'cache': 'folder',
            'ui': 'tab',
            'microservice': 'hexagon',
            'lambda': 'parallelogram',
            'container': 'rect',
            'default': 'box'
        }
        return shapes.get(node_type, shapes['default'])
    
    def get_color_for_type(self, node_type):
        """Return color based on node type and theme"""
        light_theme = {
            'database': '#4DB6AC',
            'api': '#FF8A65',
            'service': '#64B5F6',
            'proxy': '#BA68C8',
            'queue': '#FFD54F',
            'cache': '#AED581',
            'ui': '#7986CB',
            'microservice': '#4DD0E1',
            'lambda': '#F06292',
            'container': '#81C784',
            'default': '#E0E0E0'
        }
        
        dark_theme = {
            'database': '#00695C',
            'api': '#BF360C',
            'service': '#0D47A1',
            'proxy': '#6A1B9A',
            'queue': '#FF8F00',
            'cache': '#558B2F',
            'ui': '#3949AB',
            'microservice': '#00838F',
            'lambda': '#AD1457',
            'container': '#2E7D32',
            'default': '#424242'
        }
        
        palette = dark_theme if self.args.theme == 'dark' else light_theme
        return palette.get(node_type, palette['default'])
    
    def get_font_color(self, node_type):
        """Determine appropriate font color based on theme"""
        if self.args.theme == 'dark':
            return '#ffffff'
        # For light theme, use dark text except for certain node types
        return '#000000'
    
    def get_border_color(self, node_type):
        """Get border color based on node type"""
        if self.args.theme == 'dark':
            return '#ffffff'
        return {
            'database': '#00796B',
            'api': '#E64A19',
            'service': '#1976D2',
            'proxy': '#7B1FA2',
            'default': '#616161'
        }.get(node_type, '#616161')
    
    def generate_html(self):
        """Generate interactive HTML visualization with enhanced shapes"""
        from jinja2 import Template
        
        # Flatten the hierarchy for D3 with type information
        nodes = []
        links = []
        
        def process_node(node, parent=None):
            node_id = node.get('id', str(id(node)))
            nodes.append({
                'id': node_id,
                'name': node.get('name', node_id),
                'type': node.get('type', 'default').lower(),
                'description': node.get('description', ''),
                'shape': self.get_html_shape(node.get('type', 'default').lower())
            })
            
            if parent:
                links.append({
                    'source': parent,
                    'target': node_id,
                    'type': 'depends_on'
                })
                
            for child in node.get('dependencies', []):
                process_node(child, node_id)
        
        if isinstance(self.data, list):
            for item in self.data:
                process_node(item)
        else:
            process_node(self.data)
        
        # Load HTML template
        template = Template(Path('template.html').read_text())
        
        # Render template with data
        html_content = template.render(
            title='Dependency Tree Visualization',
            nodes=json.dumps(nodes),
            links=json.dumps(links),
            theme=self.args.theme
        )
        
        # Write to file
        output_name = self.args.output or Path(self.args.input).stem
        output_file = f'{output_name}.html'
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        if self.args.open:
            webbrowser.open(output_file)
    
    def get_html_shape(self, node_type):
        """Return shape type for HTML/D3 visualization"""
        shapes = {
            'database': 'database',
            'api': 'api',
            'service': 'service',
            'proxy': 'proxy',
            'queue': 'queue',
            'cache': 'cache',
            'ui': 'ui',
            'microservice': 'microservice',
            'lambda': 'lambda',
            'container': 'container',
            'default': 'default'
        }
        return shapes.get(node_type, shapes['default'])
    
    def run(self):
        if self.args.format == 'html':
            self.generate_html()
        else:
            self.generate_graphviz()

if __name__ == '__main__':
    visualizer = DependencyVisualizer()
    visualizer.run()