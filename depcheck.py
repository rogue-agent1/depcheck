#!/usr/bin/env python3
"""depcheck - Check Python files for missing/unused dependencies."""
import ast, os, argparse, sys, importlib.util

STDLIB = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else {
    'os','sys','re','json','csv','math','time','datetime','collections','itertools',
    'functools','pathlib','subprocess','argparse','hashlib','hmac','secrets','uuid',
    'socket','http','urllib','email','html','xml','sqlite3','logging','unittest',
    'typing','dataclasses','enum','abc','io','struct','base64','shutil','glob',
    'tempfile','configparser','threading','multiprocessing','concurrent','asyncio',
    'ssl','ctypes','copy','pprint','textwrap','string','operator','statistics',
    'random','pickle','shelve','dbm','gzip','zipfile','tarfile','lzma','bz2',
    'signal','contextlib','weakref','types','inspect','dis','code','codeop',
    'compileall','py_compile','traceback','linecache','tokenize','token','keyword',
    'ast','symtable','marshal','importlib','pkgutil','platform','sysconfig',
    'warnings','atexit','gc','resource','site','builtins','__future__',
}

def get_imports(filepath):
    with open(filepath) as f:
        try: tree = ast.parse(f.read())
        except SyntaxError: return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split('.')[0])
    return imports

def check_available(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False

def main():
    p = argparse.ArgumentParser(description='Check Python dependencies')
    p.add_argument('path', nargs='?', default='.', help='File or directory')
    p.add_argument('--missing', action='store_true', help='Show missing only')
    p.add_argument('--stdlib', action='store_true', help='Include stdlib')
    p.add_argument('-j', '--json', action='store_true')
    args = p.parse_args()

    files = []
    if os.path.isfile(args.path):
        files = [args.path]
    else:
        for root, dirs, fnames in os.walk(args.path):
            dirs[:] = [d for d in dirs if d not in {'.git','__pycache__','venv','.venv','node_modules'}]
            files.extend(os.path.join(root, f) for f in fnames if f.endswith('.py'))

    all_imports = set()
    for f in files:
        all_imports |= get_imports(f)

    third_party = all_imports - STDLIB - {'__main__'}
    if not args.stdlib:
        check_set = third_party
    else:
        check_set = all_imports

    results = {'available': [], 'missing': []}
    for mod in sorted(check_set):
        avail = check_available(mod)
        if avail:
            results['available'].append(mod)
        else:
            results['missing'].append(mod)

    if args.json:
        print(json.dumps(results, indent=2))
    elif args.missing:
        for m in results['missing']:
            print(f"  ✗ {m}")
    else:
        if results['missing']:
            print("Missing:")
            for m in results['missing']:
                print(f"  ✗ {m}")
        print(f"\nThird-party: {len(third_party)} | Available: {len(results['available'])} | Missing: {len(results['missing'])}")

    sys.exit(1 if results['missing'] else 0)

if __name__ == '__main__':
    main()
