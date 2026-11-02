"""Public documentation checks isolated from models and deployment."""
from collections import Counter
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
from urllib.parse import unquote,urlsplit
import xml.etree.ElementTree as ET

import pytest

ROOT=Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.refs=[];self.h1=0;self.active=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        if a.get('aria-current')=='page':self.active+=1
        for key in ('href','src'):
            if key in a:self.refs.append(a[key])


@pytest.fixture(scope='module')
def generated(tmp_path_factory):
    target=tmp_path_factory.mktemp('documentation')
    shutil.copytree(ROOT/'docs',target/'docs')
    (target/'scripts').mkdir()
    for name in ('README.md','pyproject.toml','LICENSE'):shutil.copy2(ROOT/name,target/name)
    shutil.copy2(ROOT/'scripts/build_docs.py',target/'scripts/build_docs.py')
    subprocess.run([sys.executable,str(target/'scripts/build_docs.py')],check=True,capture_output=True)
    return target


def pages(root):
    result={}
    for path in (root/'docs').glob('*.html'):
        p=Page();p.feed(path.read_text());result[path]=p
    return result


def test_generated_links_headings_and_version(generated):
    version=tomllib.loads((generated/'pyproject.toml').read_text())['project']['version']
    parsed=pages(generated)
    assert len(parsed)==18
    for path,page in parsed.items():
        assert page.h1==1 and page.active==1,path
        assert not [k for k,v in Counter(page.ids).items() if v>1],path
        assert f'Docs · {version}' in path.read_text()
        for ref in page.refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc:continue
            dest=(path.parent/unquote(u.path)).resolve() if u.path else path
            assert dest.exists(),(path.name,ref)
            if u.fragment and dest in parsed:assert u.fragment in parsed[dest].ids,(path.name,ref)
    assert f'<!-- package-version:start -->{version}<!-- package-version:end -->' in (generated/'README.md').read_text()


def test_deterministic_and_current_generated_outputs(generated):
    outputs=list((generated/'docs').glob('*.html'))+[generated/'README.md']
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
    subprocess.run([sys.executable,str(generated/'scripts/build_docs.py')],check=True,capture_output=True)
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
    for p in outputs:assert p.read_bytes()==(ROOT/p.relative_to(generated)).read_bytes(),p.name


def test_original_guide_anchors_preserved(generated):
    original=json.loads((ROOT/'docs/reviews/2026-11-02/anchors-before.json').read_text())
    parsed=pages(generated)
    for name,ids in original.items():assert set(ids)<=set(parsed[generated/'docs'/(name+'.html')].ids),name


def test_markdown_relative_links_work_in_clone():
    for path in [ROOT/'README.md',*(ROOT/'docs/content').glob('*.md')]:
        refs=re.findall(r'\]\(([^\s)]+)\)',path.read_text())+re.findall(r'(?:href|src)="([^"]+)"',path.read_text())
        for ref in refs:
            u=urlsplit(ref)
            if u.scheme or u.netloc or not u.path:continue
            assert (path.parent/unquote(u.path)).exists(),(path.name,ref)


def test_svg_xml():
    for path in (ROOT/'docs').rglob('*.svg'):ET.parse(path)


def test_owner_selected_mit_license():
    project=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']
    assert project['license']=='MIT' and project['license-files']==['LICENSE']
    assert (ROOT/'LICENSE').read_text().startswith('MIT License\n')
    assert '(LICENSE)' in (ROOT/'README.md').read_text()
