#!/usr/bin/env python3
"""Run only pinned AutoGPT parsing/loading/package validators, without a database.

Supply the two inspected public source files. Their Git blobs are checked before
whitelisted definitions are compiled; no module imports or upstream skill code
are executed. Requires PyYAML and pydantic in addition to the standard library.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import posixpath
import re
import sys
import types
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

SEED_BLOB = '05014f04317b1a820a0df6db89c4de515d80f68f'
SKILLS_BLOB = '0425ccea6aeea1e805d9874e0e3f2c08f41a5497'
FUNCTIONS = {'parse_skill_markdown','render_skill_markdown','_validate_name','validate_skill_content','validate_package','_package_path_error'}
CLASSES = {'ParsedSkill','SkillPackageError','SkillFile','SkillPackage'}
CONSTANTS = {'MAX_NAME_CHARS','MAX_DESCRIPTION_CHARS','MAX_BODY_CHARS','MAX_TRIGGERS','MAX_TRIGGER_CHARS','MAX_PACKAGE_FILES','MAX_PACKAGE_FILE_BYTES','MAX_PACKAGE_BYTES','MAX_PACKAGE_PATH_DEPTH','_NAME_RE','_FRONTMATTER_RE','_CARRIED_FRONTMATTER_KEYS','_PACKAGE_SEGMENT_RE','_ROOT_SKILL_MD'}

def read_pinned(path: Path, expected: str) -> str:
    data = path.read_bytes()
    actual = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if actual != expected:
        raise ValueError(f'{path.name}: source differs from the inspected Git blob ({actual})')
    return data.decode('utf-8')

def canonical_categories(values):
    allowed={'marketing','sales','finance','support','operations','research','content','development'}
    if not set(values) <= allowed:
        raise ValueError('unknown catalog category')
    return values

def probe(root: Path, seed_path: Path, skills_path: Path) -> dict:
    seed = ast.parse(read_pinned(seed_path,SEED_BLOB))
    skills = ast.parse(read_pinned(skills_path,SKILLS_BLOB))
    module = types.ModuleType('_autogpt_catalog_import_probe')
    sys.modules[module.__name__] = module
    scope = module.__dict__
    scope.update({'Any':Any,'Mapping':Mapping,'Iterable':Iterable,'dataclass':dataclass,'field':field,'BaseModel':BaseModel,'Path':Path,'re':re,'yaml':yaml,'os':os,'posixpath':posixpath,'_DEFAULT_SKILLS_BY_NAME':{'agent_building_guide':None},'CatalogEntry':dict,'CATALOG_FILE':'catalog.yml','SKILLS_DIR':'skills','validate_canonical_categories':canonical_categories})
    nodes = [ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]
    for node in skills.body:
        if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS:
            nodes.append(node)
        elif isinstance(node,ast.ClassDef) and node.name in CLASSES:
            nodes.append(node)
        elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in CONSTANTS:
            nodes.append(node)
    selected = {n.name for n in nodes if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    assert selected == FUNCTIONS | CLASSES
    for node in seed.body:
        if isinstance(node,ast.FunctionDef) and node.name in {'load_catalog','_load','_package_files','_optional_str','_attribution_value'}:
            nodes.append(node)
    tree=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
    exec(compile(tree,'pinned-autogpt-import-validators','exec'),scope)
    results=[]
    for entry in scope['load_catalog'](root):
        try:
            parsed, files=scope['_load'](root,entry)
            path=root/'skills'/entry['slug']/'SKILL.md'
            original_frontmatter=yaml.safe_load(path.read_text(encoding='utf-8').split('---',2)[1])
            roundtrip=scope['render_skill_markdown'](parsed)
            rendered_frontmatter=yaml.safe_load(roundtrip.split('---',2)[1])
            metadata=parsed.extra.get('metadata') or {}
            results.append({'slug':entry['slug'],'result':'accepted','supplementary_files':len(files),'package_bytes':len(path.read_bytes())+sum(f.size_bytes for f in files),'source':scope['_attribution_value'](parsed,metadata,'source'),'source_url':scope['_attribution_value'](parsed,metadata,'source_url'),'license':scope['_optional_str'](parsed.extra.get('license')),'native_fields_dropped_by_parser_renderer':sorted(set(original_frontmatter)-set(rendered_frontmatter))})
        except (ValueError,OSError) as exc:
            results.append({'slug':entry['slug'],'result':'rejected','reason':str(exc)})
    return {'checked_date':'2026-09-25','seed_git_blob':SEED_BLOB,'skills_git_blob':SKILLS_BLOB,'method':'Executed only exact AST-selected load_catalog, _load, _package_files, parsing/rendering, attribution helpers, package/content/path validators and their types/constants. Used actual pydantic models. Category validation uses the documented eight-category allowlist; built-in-name lookup supplies agent_building_guide. No database, platform services, networking or upstream skill execution.','accepted':sum(r['result']=='accepted' for r in results),'rejected':sum(r['result']=='rejected' for r in results),'runtime_verified':False,'limitation':'Import acceptance does not test database persistence, installation, metadata enforcement, native plugin dispatch, service accounts or execution. The seed stores a subset of parsed fields; parser round-trip preservation does not establish database preservation.','results':results}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--seed-source',type=Path,required=True)
    parser.add_argument('--skills-source',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=probe(args.root,args.seed_source,args.skills_source)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'accepted':result['accepted'],'rejected':result['rejected'],'runtime_verified':False}))
    return int(bool(result['rejected']))

if __name__=='__main__':
    raise SystemExit(main())
