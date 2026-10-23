import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('iv3_formal_engine', Path(__file__).with_name('876_load.py'))
engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
if __name__ == '__main__':
    raise SystemExit(engine.run('transition'))
