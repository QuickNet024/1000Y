from pathlib import Path
import sys

def add_project_root_to_path():
    """添加项目根目录到Python路径"""
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root)) 