"""Build GitHub Pages guides from README.md; run with the project environment."""
from pathlib import Path
import html
import re
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
REPO = 'https://github.com/Dutch-panda/BuildRelay'
PAGES = [
    ('quickstart', 'Quick start', ['Quick start']),
    ('workflow', 'Workflow & alignment', ['How the workflow runs', 'Interactive alignment and execution modes']),
    ('configuration', 'Models & configuration', ['Tiered model routing and token optimization', 'Token usage and cost analytics']),
    ('execution', 'Execution & web research', ['Execution and validation', 'Web and documentation search with guardrails', 'Dynamic progress and project delivery']),
    ('projects', 'Projects & memory', ['Keep related tasks connected', 'What stays on disk']),
    ('resume', 'Resume a task', ['Resume a task']),
    ('architecture', 'Architecture', ['Component connections', 'Repository map', 'Development and documentation']),
    ('testing', 'Testing & integration', []),
    ('limitations', 'Limits & security', ['Current limitations', 'Security and isolation boundaries']),
    ('troubleshooting', 'Troubleshooting', ['Troubleshooting']),
    ('project-tools', 'Sessions, verify & preview', ['Project REPL, Live Verification, and UI Preview']),
    ('quality', 'Supervision & evaluation', ['Quality supervision and evaluation']),
]

def slug(value):
    return re.sub(r'[^\w\- ]', '', value.lower()).replace(' ', '-')

readme = (ROOT / 'README.md').read_text()
sections = dict(re.findall(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)', readme, re.M | re.S))
dev = sections['Development and documentation']
intro, tests = dev.split('### Testing', 1)
sections['Development and documentation'] = intro
sections['Testing'] = tests
PAGES[7][2].append('Testing')
md = MarkdownIt('commonmark', {'html': True}).enable('table')
anchors = {}
for filename, _, headings in PAGES:
    for heading in headings:
        anchors[slug(heading)] = filename + '.html#' + slug(heading)
        for nested in re.findall(r'^#{3,6} (.+)$', sections[heading], re.M):
            anchors[slug(nested)] = filename + '.html#' + slug(nested)

def heading_open(tokens, idx, options, env):
    title = tokens[idx+1].content
    tokens[idx].attrSet('id', slug(title))
    return md.renderer.renderToken(tokens, idx, options, env)
md.renderer.rules['heading_open'] = heading_open

def render(source):
    result = md.render(source)
    result = result.replace('src="docs/', 'src="').replace('href="docs/', 'href="')
    result = re.sub(r'href="(#.*?)"', lambda m: 'href="'+anchors.get(m[1][1:],m[1])+'"', result)
    result = re.sub(r'href="(?!https?://|#)([^"#]+)(#[^"]*)?"',
        lambda m: m[0] if m[1].endswith('.html') or m[1].startswith(('brand/', 'diagrams/')) else 'href="'+REPO+'/blob/main/'+m[1]+(m[2] or '')+'"',result)
    result = re.sub(r'<img ([^>]*src="(diagrams/[^"]+\.svg)"[^>]*)>', r'<a class="diagram-link" href="\2" aria-label="Open diagram at full size"><img \1></a>', result)
    return result

def page(filename, title, content, toc):
    groups = [
        ('GET STARTED', [('index','Introduction'), ('quickstart','Quick start'), ('example','Terminal example')]),
        ('USE BUILDRELAY', [('workflow','Workflow & alignment'), ('configuration','Models & configuration'), ('execution','Execution & web research'), ('projects','Projects & memory'), ('project-tools','Sessions, verify & preview'), ('resume','Resume a task')]),
        ('INSPECT & VERIFY', [('quality','Supervision & evaluation'), ('architecture','Architecture'), ('testing','Testing & integration'), ('limitations','Limits & security'), ('troubleshooting','Troubleshooting')]),
    ]
    nav = ''
    for label, links in groups:
        nav += '<p>'+label+'</p>'
        nav += ''.join(f'<a href="{f}.html"'+(' aria-current="page"' if f==filename else '')+f'>{html.escape(t)}</a>' for f,t in links)
    local=''.join(f'<a href="#{slug(h)}">{html.escape(h)}</a>' for h in toc)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>{html.escape(title)} · BuildRelay</title><meta name="description" content="BuildRelay guides: plan, build, check, and resume development tasks."><link rel="icon" href="brand/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="site.css"><script src="site.js" defer></script><link rel="canonical" href="https://dutch-panda.github.io/BuildRelay/{'' if filename=='index' else filename+'.html'}"></head>
<body><a class="skip" href="#content">Skip to content</a><header><a class="brand" href="index.html"><img src="brand/logo.svg" alt="" width="32" height="32">BuildRelay <span>Docs</span></a><a href="{REPO}">GitHub ↗</a></header><div class="layout"><aside class="sidebar"><details open><summary>Documentation</summary><nav aria-label="Documentation">{nav}</nav></details></aside><main id="content"><div class="breadcrumb">BuildRelay / {html.escape(title)}</div>{content}<footer>Early-stage developer tool · Review generated code and validation results.<br><a href="{REPO}/blob/main/README.md">Source guide on GitHub</a></footer></main><aside class="toc"><nav aria-label="On this page"><p>ON THIS PAGE</p>{local}</nav></aside></div></body></html>'''

for filename,title,headings in PAGES:
    source='\n\n'.join('## '+h+'\n'+sections[h] for h in headings)
    (DOCS/(filename+'.html')).write_text(page(filename,title, '<h1>'+html.escape(title)+'</h1>'+render(source), headings))

home='''<p class="eyebrow">A local Python CLI for AI development</p><h1>Plan. Build. Check.<br><span>Keep your progress.</span></h1><p class="lead">Clarify your request, approve a technical plan, and build through recorded Docker phase checks. Resume saved work and evolve the same project.</p><div class="actions"><a class="button primary" href="quickstart.html">Run your first task →</a><a class="button" href="example.html">See the terminal example</a></div><div class="features"><a href="workflow.html"><strong>Align &amp; approve</strong><span>Intent interviews, backend and UI specs, and approval gates.</span></a><a href="execution.html"><strong>Build &amp; check</strong><span>Ordered phases, recorded results, and bounded repair attempts.</span></a><a href="projects.html"><strong>Resume &amp; iterate</strong><span>Saved checkpoints, project memory, and follow-up features.</span></a></div><h2 id="how-it-works">How it works</h2><p>Natasha routes your request to research, architecture, or implementation. Research-only requests end after Odin. Optional Dana supervision adds model critiques at stage boundaries.</p><img class="diagram" src="diagrams/workflow.svg" alt="Four sequential leads with selected entry points, a research-only exit, and optional Dana supervision."><div class="agent-roster"><div class="agent-card agent-natasha"><div class="agent-badge">Natasha</div><strong>Routing &amp; alignment</strong><p>Clarify intent and select the route.</p></div><div class="agent-card agent-odin"><div class="agent-badge">Odin</div><strong>Research</strong><p>Retrieve vault context, web snippets, and package metadata.</p></div><div class="agent-card agent-taghi"><div class="agent-badge">Taghi</div><strong>Architecture &amp; UI design</strong><p>Define specifications and request approval.</p></div><div class="agent-card agent-meti"><div class="agent-badge">Meti</div><strong>Implementation</strong><p>Execute Docker commands and record phase checks.</p></div></div><h2 id="quality-signals">Quality signals</h2><p>Use phase results, optional Dana model critiques, and a separate static evaluation scorecard together. Scores are diagnostic signals—not proof of correctness or security.</p><div class="guide-links"><a href="quality.html"><strong>Supervision &amp; evaluation</strong><span>Advisory or autonomous steering, audit notes, and heuristic scorecards.</span></a><a href="execution.html"><strong>Two verification tiers</strong><span>Docker checks first; guided live scripts run separately on the host.</span></a></div><h2 id="start-here">Start here</h2><div class="guide-links"><a href="quickstart.html"><strong>Install &amp; choose models</strong><span>Connect a provider and select models for each lead.</span></a><a href="project-tools.html"><strong>Work on an existing project</strong><span>Use sessions, live verification, and local UI preview.</span></a><a href="architecture.html"><strong>Explore the architecture</strong><span>Typed handoffs, persistence, and execution policy.</span></a><a href="testing.html"><strong>Run platform tests</strong><span>Offline unit tests and opt-in integration checks.</span></a></div><h2 id="before-you-run">Before you run</h2><div class="notice"><p>BuildRelay is an early-stage local developer tool. Docker networking is enabled. Project credentials inside the mounted workspace are accessible to container code. Live verification executes generated scripts on the host. Review generated code, scripts, and test quality before relying on results. <a href="limitations.html">Read the limits and security guide →</a></p></div>'''
(DOCS/'index.html').write_text(page('index','Introduction',home,['How it works','Quality signals','Start here','Before you run']))
transcript=(DOCS/'examples/terminal-session.txt').read_text()
example='''<h1>A real terminal capture</h1><p class="lead">Inspect the CLI and its offline tests before running a model-powered task.</p><div class="notice"><strong>What this capture demonstrates</strong><p>This is actual command output recorded locally on 28 October 2026. It shows the CLI capabilities available on that date and deterministic platform checks; newer commands and features are not represented. It is not an AI implementation run, an integration test, or a benchmark.</p></div><img class="diagram" src="examples/terminal-preview.svg" alt="Excerpt of actual CLI help and offline test output; full transcript follows."><h2 id="recorded-output">Recorded output</h2><p>No animation or simulated success messages. <a href="examples/terminal-session.txt">Open the full plain-text transcript</a>.</p><pre class="capture"><code>'''+html.escape(transcript)+'''</code></pre><h2 id="try-a-development-task">Try a development task</h2><p>After <a href="quickstart.html">setup</a>, use this small task as a reproducible demo prompt. The following is a suggested command, not output from the capture above.</p><pre><code>python main.py "Build a Python CSV validator that reports missing required columns and invalid numeric amounts. Include valid and invalid fixtures, automated tests, and a README with run commands." --project csv-demo --image python:3.11-slim --step</code></pre><p>Inspect the plan, generated files, and phase results. Keep provider sign-in and configuration outside any screen recording. Only demonstrate resume with a task that was actually interrupted or failed.</p>'''
(DOCS/'example.html').write_text(page('example','Terminal example',example,['Recorded output','Try a development task']))
print('Built introduction, terminal example, and',len(PAGES),'guides from README.md.')
