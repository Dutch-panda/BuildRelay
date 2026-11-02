"""Generate Pages from maintained Markdown sources without executing examples."""
from pathlib import Path
import html
import posixpath
import re
import tomllib
from urllib.parse import unquote,urlsplit
from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parent.parent
DOCS=ROOT/'docs'
CONTENT=DOCS/'content'
REPO='https://github.com/Dutch-panda/BuildRelay'
VERSION=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
GROUPS=[
 ('GET STARTED',[('index','Introduction'),('task-fit','Task fit'),('quickstart','Quick start')]),
 ('WORK ON A PROJECT',[('workflow','Workflow & alignment'),('projects','Projects & memory'),('resume','Resume a task'),('project-tools','Sessions, verify & preview')]),
 ('REFERENCE',[('configuration','Models & configuration'),('commands','Command boundaries'),('execution','Execution & web research'),('troubleshooting','Troubleshooting')]),
 ('INSPECT THE EVIDENCE',[('example','Historical terminal capture'),('showcase','Showcase (pending)'),('quality','Supervision & evaluation'),('testing','Testing & integration')]),
 ('UNDERSTAND THE DESIGN',[('architecture','Architecture'),('design','Design rationale (proposed)'),('limitations','Limits & security')]),
]
PAGES=[p for _,entries in GROUPS for p in entries]


def slug(value):
 return re.sub(r'[^\w\- ]','',value.lower()).replace(' ','-')


def source_for(name):
 source=(CONTENT/(name+'.md')).read_text()
 if '{{TERMINAL_TRANSCRIPT}}' in source:
  capture=(DOCS/'examples/terminal-session.txt').read_text()
  source=source.replace('{{TERMINAL_TRANSCRIPT}}','<pre class="capture"><code>'+html.escape(capture)+'</code></pre>')
 return source


def resolve(ref,name):
 parsed=urlsplit(ref)
 if parsed.scheme or parsed.netloc or ref.startswith('#'):return ref
 target=(CONTENT/name).parent/unquote(parsed.path)
 target=Path(posixpath.normpath(str(target)))
 fragment=('#'+parsed.fragment) if parsed.fragment else ''
 if target.parent==CONTENT and target.suffix=='.md' and target.stem in dict(PAGES):
  return target.stem+'.html'+fragment
 if target.parent==CONTENT:
  return REPO+'/blob/main/'+target.relative_to(ROOT).as_posix()+fragment
 if target.is_relative_to(DOCS):return target.relative_to(DOCS).as_posix()+fragment
 if target.is_relative_to(ROOT):return REPO+'/blob/main/'+target.relative_to(ROOT).as_posix()+fragment
 raise ValueError('Documentation link escapes project: '+ref)


def render(source,name):
 md=MarkdownIt('commonmark',{'html':True}).enable('table')
 used={}
 headings=re.findall(r'<h[23] id="([^"]+)">([^<]+)</h[23]>',source)
 def heading_open(tokens,idx,options,env):
  label=tokens[idx+1].content
  base=slug(label);count=used.get(base,0);used[base]=count+1
  identifier=base+('-'+str(count) if count else '')
  tokens[idx].attrSet('id',identifier)
  if tokens[idx].tag in ('h2','h3'):headings.append((identifier,label))
  return md.renderer.renderToken(tokens,idx,options,env)
 md.renderer.rules['heading_open']=heading_open
 result=md.render(source)
 result=re.sub(r'(href|src)="([^"]+)"',lambda m:m[1]+'="'+html.escape(resolve(html.unescape(m[2]),name+'.md'),quote=True)+'"',result)
 result=re.sub(r'<img ([^>]*src="((?:diagrams|examples)/[^" ]+\.svg)"[^>]*)>',r'<a class="diagram-link" href="\2" aria-label="Open image at full size"><img \1></a>',result)
 result=re.sub(r'<pre([^>]*)>',r'<pre\1 tabindex="0" aria-label="Code block; scroll horizontally if needed">',result)
 return result,headings


def page(name,title,body,toc):
 nav=''
 for label,entries in GROUPS:
  nav+='<p>'+label+'</p>'
  for dest,text in entries:
   active=' aria-current="page"' if dest==name else ''
   nav+=f'<a href="{dest}.html"{active}>{html.escape(text)}</a>'
 links=''.join(f'<a href="#{i}">{html.escape(label)}</a>' for i,label in toc)
 canonical='https://dutch-panda.github.io/BuildRelay/'+('' if name=='index' else name+'.html')
 lead='' if name=='index' else '<h1>'+html.escape(title)+'</h1>'
 return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>{html.escape(title)} · BuildRelay {VERSION}</title><meta name="description" content="BuildRelay {VERSION}: setup, task guides, execution boundaries and recorded evidence."><meta property="og:title" content="{html.escape(title)} · BuildRelay"><meta property="og:description" content="Experimental local AI development workflow. Inspect plans, phase checks and limits."><meta property="og:url" content="{canonical}"><link rel="canonical" href="{canonical}"><link rel="icon" href="brand/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="site.css"><script src="site.js" defer></script></head>
<body><a class="skip" href="#content">Skip to content</a><header><a class="brand" href="index.html"><img src="brand/logo.svg" alt="" width="32" height="32">BuildRelay <span>Docs · {VERSION}</span></a><a href="{REPO}">GitHub ↗</a></header><div class="layout"><aside class="sidebar"><details open><summary>Documentation</summary><nav aria-label="Documentation">{nav}</nav></details></aside><main id="content" tabindex="-1"><div class="breadcrumb">BuildRelay / {html.escape(title)}</div>{lead}{body}<footer>BuildRelay {VERSION} · Experimental developer tool · Review generated code and checks.<br><a href="{REPO}/blob/main/docs/content/{name}.md">Edit this guide on GitHub</a> · <a href="{REPO}/issues">Report a reproducible issue</a> · <a href="{REPO}/blob/main/LICENSE">MIT license</a></footer></main><aside class="toc"><nav aria-label="On this page"><p>ON THIS PAGE</p>{links}</nav></aside></div></body></html>'''


def build():
 readme=ROOT/'README.md'
 source=re.sub(r'<!-- package-version:start -->.*?<!-- package-version:end -->','<!-- package-version:start -->'+VERSION+'<!-- package-version:end -->',readme.read_text())
 readme.write_text(source)
 for name,title in PAGES:
  body,toc=render(source_for(name),name)
  (DOCS/(name+'.html')).write_text(page(name,title,body,toc))
 print(f'Built {len(PAGES)} pages from docs/content; package version {VERSION}.')


if __name__=='__main__':build()
