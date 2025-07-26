# visualizations.py - Erweiterung für den Bot mit Visualisierungen

import ast
import os
import re
from typing import Dict, List, Set, Tuple, Optional
import json
from pathlib import Path
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import pandas as pd
from fastapi import HTTPException


class CodeAnalyzer:
    """Analysiert Code-Struktur und Abhängigkeiten"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dependencies = defaultdict(set)
        self.file_info = {}
        self.import_graph = nx.DiGraph()

    def analyze_python_file(self, filepath: Path) -> Dict:
        """Analysiert eine Python-Datei"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Sammle Informationen
            imports = []
            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}" if module else alias.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)

                    classes.append({
                        'name': node.name,
                        'lineno': node.lineno,
                        'methods': methods,
                        'bases': [base.id for base in node.bases if isinstance(base, ast.Name)]
                    })

            # Zähle Zeilen
            lines = content.split('\n')
            loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])

            return {
                'filepath': str(filepath),
                'imports': imports,
                'functions': functions,
                'classes': classes,
                'loc': loc,
                'total_lines': len(lines)
            }

        except Exception as e:
            print(f"Fehler beim Analysieren von {filepath}: {e}")
            return None

    def analyze_javascript_file(self, filepath: Path) -> Dict:
        """Analysiert eine JavaScript-Datei (vereinfacht)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Regex für Imports
            import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
            require_pattern = r'require\s*\([\'"]([^\'"]+)[\'"]\)'

            imports = re.findall(import_pattern, content) + re.findall(require_pattern, content)

            # Regex für Funktionen (vereinfacht)
            function_pattern = r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)'
            functions = [f for f in re.findall(function_pattern, content) for f in f if f]

            # Regex für Klassen
            class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
            classes = re.findall(class_pattern, content)

            lines = content.split('\n')
            loc = len([l for l in lines if l.strip() and not l.strip().startswith('//')])

            return {
                'filepath': str(filepath),
                'imports': imports,
                'functions': functions,
                'classes': [{'name': c[0], 'extends': c[1] if c[1] else None} for c in classes],
                'loc': loc,
                'total_lines': len(lines)
            }

        except Exception as e:
            print(f"Fehler beim Analysieren von {filepath}: {e}")
            return None

    def analyze_project(self):
        """Analysiert das gesamte Projekt"""
        for root, dirs, files in os.walk(self.project_path):
            # Ignoriere versteckte Ordner und node_modules
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']

            for file in files:
                filepath = Path(root) / file

                if file.endswith('.py'):
                    info = self.analyze_python_file(filepath)
                elif file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    info = self.analyze_javascript_file(filepath)
                else:
                    continue

                if info:
                    rel_path = filepath.relative_to(self.project_path)
                    self.file_info[str(rel_path)] = info

                    # Baue Import-Graph
                    for imp in info['imports']:
                        self.import_graph.add_edge(str(rel_path), imp)


class ProjectVisualizer:
    """Erstellt Visualisierungen für Projekt-Struktur"""

    def __init__(self, analyzer: CodeAnalyzer):
        self.analyzer = analyzer

    def create_dependency_graph(self, output_path: str = "dependency_graph.html"):
        """Erstellt interaktives Abhängigkeits-Diagramm"""
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
        net.barnes_hut()

        # Füge Knoten hinzu
        for file_path, info in self.analyzer.file_info.items():
            size = min(20 + info['loc'] / 10, 50)  # Größe basiert auf LOC

            # Farbe basiert auf Dateityp
            if file_path.endswith('.py'):
                color = "#3776ab"  # Python blau
            elif file_path.endswith(('.js', '.jsx')):
                color = "#f7df1e"  # JavaScript gelb
            else:
                color = "#61dafb"  # TypeScript/React blau

            net.add_node(file_path,
                         label=os.path.basename(file_path),
                         size=size,
                         color=color,
                         title=f"{file_path}\nLOC: {info['loc']}\nFunctions: {len(info['functions'])}\nClasses: {len(info['classes'])}")

        # Füge Kanten hinzu (Abhängigkeiten)
        for source, target in self.analyzer.import_graph.edges():
            if target in self.analyzer.file_info:
                net.add_edge(source, target)

        # Konfiguriere Physics
        net.set_options("""
        var options = {
          "nodes": {
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "arrows": {
              "to": {
                "enabled": true,
                "scaleFactor": 0.5
              }
            },
            "color": {
              "color": "#848484",
              "highlight": "#ffffff"
            },
            "smooth": {
              "type": "continuous"
            }
          },
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -8000,
              "centralGravity": 0.3,
              "springLength": 95
            }
          }
        }
        """)

        net.save_graph(output_path)
        return output_path

    def create_file_tree_visualization(self) -> Dict:
        """Erstellt Baum-Struktur für D3.js Visualisierung"""
        root = {"name": os.path.basename(self.analyzer.project_path), "children": []}

        # Gruppiere Dateien nach Verzeichnis
        file_tree = defaultdict(list)
        for file_path in self.analyzer.file_info:
            parts = file_path.split(os.sep)
            if len(parts) > 1:
                dir_path = os.sep.join(parts[:-1])
                file_tree[dir_path].append(parts[-1])
            else:
                file_tree[''].append(parts[0])

        def build_tree(path, node):
            # Verarbeite Unterverzeichnisse
            subdirs = set()
            for p in file_tree:
                if p.startswith(path) and p != path:
                    relative = p[len(path):].lstrip(os.sep)
                    if os.sep in relative:
                        subdirs.add(relative.split(os.sep)[0])

            for subdir in sorted(subdirs):
                if path:
                    full_path = os.path.join(path, subdir)
                else:
                    full_path = subdir

                child = {"name": subdir, "children": []}
                node["children"].append(child)
                build_tree(full_path, child)

            # Füge Dateien hinzu
            if path in file_tree:
                for file in sorted(file_tree[path]):
                    file_path = os.path.join(path, file) if path else file
                    info = self.analyzer.file_info.get(file_path, {})
                    node["children"].append({
                        "name": file,
                        "size": info.get('loc', 0),
                        "type": "file",
                        "language": "python" if file.endswith('.py') else "javascript"
                    })

        build_tree('', root)
        return root

    def create_code_metrics_dashboard(self, output_path: str = "metrics_dashboard.html"):
        """Erstellt ein Dashboard mit Code-Metriken"""
        # Sammle Metriken
        metrics = {
            'total_files': len(self.analyzer.file_info),
            'total_loc': sum(info['loc'] for info in self.analyzer.file_info.values()),
            'total_functions': sum(len(info['functions']) for info in self.analyzer.file_info.values()),
            'total_classes': sum(len(info['classes']) for info in self.analyzer.file_info.values()),
            'files_by_type': Counter(Path(f).suffix for f in self.analyzer.file_info),
            'largest_files': sorted(
                [(f, info['loc']) for f, info in self.analyzer.file_info.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

        # Erstelle HTML Dashboard
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Code Metrics Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #1e1e1e;
                    color: #ffffff;
                    padding: 20px;
                }}
                .dashboard {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }}
                .metric-card {{
                    background-color: #2d2d2d;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                .metric-value {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #4CAF50;
                }}
                .metric-label {{
                    font-size: 1.2em;
                    color: #888;
                }}
                #treeMap, #dependencyGraph {{
                    width: 100%;
                    height: 500px;
                    background-color: #2d2d2d;
                    border-radius: 8px;
                }}
                canvas {{
                    max-height: 300px;
                }}
            </style>
        </head>
        <body>
            <h1>📊 Code Metrics Dashboard</h1>

            <div class="dashboard">
                <div class="metric-card">
                    <div class="metric-value">{total_files}</div>
                    <div class="metric-label">Dateien</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{total_loc:,}</div>
                    <div class="metric-label">Lines of Code</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{total_functions}</div>
                    <div class="metric-label">Funktionen</div>
                </div>

                <div class="metric-card">
                    <div class="metric-value">{total_classes}</div>
                    <div class="metric-label">Klassen</div>
                </div>
            </div>

            <div class="dashboard" style="margin-top: 30px;">
                <div class="metric-card">
                    <h3>Dateitypen</h3>
                    <canvas id="fileTypesChart"></canvas>
                </div>

                <div class="metric-card">
                    <h3>Größte Dateien (LOC)</h3>
                    <canvas id="largestFilesChart"></canvas>
                </div>
            </div>

            <div style="margin-top: 30px;">
                <h2>🌳 Projekt-Struktur (Treemap)</h2>
                <div id="treeMap"></div>
            </div>

            <script>
                // Dateitypen Chart
                const fileTypesCtx = document.getElementById('fileTypesChart').getContext('2d');
                new Chart(fileTypesCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {file_types_labels},
                        datasets: [{{
                            data: {file_types_data},
                            backgroundColor: ['#3776ab', '#f7df1e', '#61dafb', '#4CAF50', '#FF6384']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{
                                labels: {{
                                    color: 'white'
                                }}
                            }}
                        }}
                    }}
                }});

                // Größte Dateien Chart
                const largestFilesCtx = document.getElementById('largestFilesChart').getContext('2d');
                new Chart(largestFilesCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {largest_files_labels},
                        datasets: [{{
                            label: 'Lines of Code',
                            data: {largest_files_data},
                            backgroundColor: '#4CAF50'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        indexAxis: 'y',
                        plugins: {{
                            legend: {{
                                display: false
                            }}
                        }},
                        scales: {{
                            x: {{
                                ticks: {{
                                    color: 'white'
                                }},
                                grid: {{
                                    color: 'rgba(255, 255, 255, 0.1)'
                                }}
                            }},
                            y: {{
                                ticks: {{
                                    color: 'white'
                                }},
                                grid: {{
                                    color: 'rgba(255, 255, 255, 0.1)'
                                }}
                            }}
                        }}
                    }}
                }});

                // Treemap
                const treeData = {tree_data};

                const width = document.getElementById('treeMap').clientWidth;
                const height = 500;

                const treemap = d3.treemap()
                    .size([width, height])
                    .padding(2)
                    .round(true);

                const root = d3.hierarchy(treeData)
                    .sum(d => d.size)
                    .sort((a, b) => b.value - a.value);

                treemap(root);

                const svg = d3.select("#treeMap")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);

                const color = d3.scaleOrdinal()
                    .domain(["python", "javascript", "folder"])
                    .range(["#3776ab", "#f7df1e", "#666"]);

                const leaf = svg.selectAll("g")
                    .data(root.leaves())
                    .join("g")
                    .attr("transform", d => `translate(${{d.x0}},${{d.y0}})`);

                leaf.append("rect")
                    .attr("fill", d => color(d.data.language || "folder"))
                    .attr("width", d => d.x1 - d.x0)
                    .attr("height", d => d.y1 - d.y0);

                leaf.append("text")
                    .attr("x", 3)
                    .attr("y", 15)
                    .text(d => d.data.name)
                    .attr("font-size", "11px")
                    .attr("fill", "white");
            </script>
        </body>
        </html>
        """

        # Bereite Daten für Charts vor
        file_types = metrics['files_by_type']
        largest_files = metrics['largest_files']

        html = html_template.format(
            total_files=metrics['total_files'],
            total_loc=metrics['total_loc'],
            total_functions=metrics['total_functions'],
            total_classes=metrics['total_classes'],
            file_types_labels=json.dumps(list(file_types.keys())),
            file_types_data=json.dumps(list(file_types.values())),
            largest_files_labels=json.dumps([os.path.basename(f[0]) for f in largest_files]),
            largest_files_data=json.dumps([f[1] for f in largest_files]),
            tree_data=json.dumps(self.create_file_tree_visualization())
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def create_complexity_heatmap(self, output_path: str = "complexity_heatmap.png"):
        """Erstellt eine Heatmap der Code-Komplexität"""
        # Erstelle Matrix für Heatmap
        files = list(self.analyzer.file_info.keys())[:20]  # Top 20 Dateien

        data = []
        for file in files:
            info = self.analyzer.file_info[file]
            data.append([
                info['loc'],
                len(info['functions']),
                len(info['classes']),
                len(info['imports'])
            ])

        df = pd.DataFrame(data,
                          index=[os.path.basename(f) for f in files],
                          columns=['LOC', 'Functions', 'Classes', 'Imports'])

        # Normalisiere Daten
        df_normalized = (df - df.min()) / (df.max() - df.min())

        plt.figure(figsize=(10, 8))
        sns.heatmap(df_normalized,
                    annot=df.values,
                    fmt='d',
                    cmap='YlOrRd',
                    cbar_kws={'label': 'Normalized Value'})
        plt.title('Code Complexity Heatmap')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return output_path


# Integration in den Bot
def add_visualization_endpoints(app, bot):
    """Fügt Visualisierungs-Endpoints zur FastAPI App hinzu"""

    @app.get("/api/visualize/dependencies")
    async def visualize_dependencies():
        """Erstellt Abhängigkeits-Graph"""
        analyzer = CodeAnalyzer(bot.repo_path or ".")
        analyzer.analyze_project()

        visualizer = ProjectVisualizer(analyzer)
        graph_path = visualizer.create_dependency_graph("static/dependency_graph.html")

        return {"status": "success", "path": graph_path}

    @app.get("/api/visualize/metrics")
    async def visualize_metrics():
        """Erstellt Metriken-Dashboard"""
        analyzer = CodeAnalyzer(bot.repo_path or ".")
        analyzer.analyze_project()

        visualizer = ProjectVisualizer(analyzer)
        dashboard_path = visualizer.create_code_metrics_dashboard("static/metrics_dashboard.html")

        return {"status": "success", "path": dashboard_path}

    @app.get("/api/visualize/structure")
    async def visualize_structure():
        """Gibt Projekt-Struktur als JSON zurück"""
        analyzer = CodeAnalyzer(bot.repo_path or ".")
        analyzer.analyze_project()

        visualizer = ProjectVisualizer(analyzer)
        tree_data = visualizer.create_file_tree_visualization()

        return tree_data

    @app.get("/api/analyze/file/{file_path:path}")
    async def analyze_file(file_path: str):
        """Analysiert eine spezifische Datei"""
        analyzer = CodeAnalyzer(bot.repo_path or ".")
        full_path = Path(bot.repo_path or ".") / file_path

        if full_path.suffix == '.py':
            info = analyzer.analyze_python_file(full_path)
        elif full_path.suffix in ['.js', '.jsx', '.ts', '.tsx']:
            info = analyzer.analyze_javascript_file(full_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        return info