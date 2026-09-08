import ast
import os
import glob

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        info = [f"File: {filepath}", "-" * 40]
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                doc_str = f" [Doc: {doc[:100]}...]" if doc else ""
                info.append(f"Class: {node.name}{doc_str}")
                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef):
                        fdoc = ast.get_docstring(class_node)
                        fdoc_str = f" [Doc: {fdoc[:100]}...]" if fdoc else ""
                        info.append(f"  Method: {class_node.name}{fdoc_str}")
            elif isinstance(node, ast.FunctionDef):
                doc = ast.get_docstring(node)
                doc_str = f" [Doc: {doc[:100]}...]" if doc else ""
                info.append(f"Function: {node.name}{doc_str}")
                
        info.append("\n")
        return "\n".join(info)
    except Exception as e:
        return f"File: {filepath} - Error parsing: {e}\n\n"

def main():
    base_dir = r"c:\Users\tiwar\Desktop\Projects Github\TrueEyeballproject"
    files = []
    for root, dirs, filenames in os.walk(base_dir):
        if 'venv' in root or 'venv_broken' in root or '__pycache__' in root:
            continue
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))
                
    with open(os.path.join(base_dir, 'analysis_report.txt'), 'w', encoding='utf-8') as out:
        for filepath in files:
            out.write(analyze_file(filepath))
            
if __name__ == "__main__":
    main()
