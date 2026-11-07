import json
import os
from pathlib import Path

def read(path, default):
    return json.loads(Path(path).read_text(encoding='utf-8')) if Path(path).exists() else default

def write(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    content=json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if path.exists() and path.read_text(encoding='utf-8')==content: return False
    temp=path.with_suffix('.tmp'); temp.write_text(content,encoding='utf-8'); os.replace(temp,path)
    return True
