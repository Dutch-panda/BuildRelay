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
    return result

def page(filename, title, content, toc):
    links = [('index', 'Introduction'), ('example', 'Terminal example')] + [(f,t) for f,t,_ in PAGES]
    nav=''.join(f'<a href="{f}.html"'+(' aria-current="page"' if f==filename else '')+f'>{html.escape(t)}</a>' for f,t in links)
    local=''.join(f'<a href="#{slug(h)}">{html.escape(h)}</a>' for h in toc)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>{html.escape(title)} · BuildRelay</title><meta name="description" content="BuildRelay guides: plan, build, check, and resume development tasks."><link rel="icon" href="brand/logo.svg" type="image/svg+xml"><link rel="stylesheet" href="site.css"><script src="site.js" defer></script><link rel="canonical" href="https://dutch-panda.github.io/BuildRelay/{'' if filename=='index' else filename+'.html'}"></head>
<body><a class="skip" href="#content">Skip to content</a><header><a class="brand" href="index.html"><img src="brand/logo.svg" alt="" width="32" height="32">BuildRelay <span>Docs</span></a><a href="{REPO}">GitHub ↗</a></header><div class="layout"><aside class="sidebar"><details open><summary>Documentation</summary><nav aria-label="Documentation"><p>GET STARTED & BUILD</p>{nav}</nav></details></aside><main id="content"><div class="breadcrumb">BuildRelay / {html.escape(title)}</div>{content}<footer>Early-stage developer tool · Review generated code and validation results.<br><a href="{REPO}/blob/main/README.md">Source guide on GitHub</a></footer></main><aside class="toc"><nav aria-label="On this page"><p>ON THIS PAGE</p>{local}</nav></aside></div></body></html>'''

for filename,title,headings in PAGES:
    source='\n\n'.join('## '+h+'\n'+sections[h] for h in headings)
    (DOCS/(filename+'.html')).write_text(page(filename,title, '<h1>'+html.escape(title)+'</h1>'+render(source), headings))

home='''<p class="eyebrow">A Python CLI for AI development workflows</p><h1>Plan. Build. Check.<br><span>Keep your progress.</span></h1><p class="lead">Turn a development request into a technical plan, Docker-built code, and recorded phase checks—with saved stages you can resume.</p><div class="actions"><a class="button primary" href="quickstart.html">Run your first task →</a><a class="button" href="example.html">See the terminal example</a></div><div class="features"><a href="workflow.html"><strong>Align & plan</strong><span>Interactive Grill-Me alignment, dual backend & UI/UX design specs, and approval gates.</span></a><a href="execution.html"><strong>Check & refine</strong><span>Backend-first Docker verification and live smoke delivery.</span></a><a href="resume.html"><strong>Resume saved work</strong><span>Keep stage outputs and phase history.</span></a><a href="workflow.html#continuous-feature-iteration-post-delivery-enhancement-gate"><strong>Iterate & enhance</strong><span>Continuous feature iteration loops, live verification, and project REPL sessions.</span></a><a href="workflow.html#automated-multi-dimensional-deliverable-evaluation-scoring-harness"><strong>Evaluate & score</strong><span>Multi-dimensional scoring across test integrity, formula security, UI surface usability, and live readiness.</span></a><a href="workflow.html#dana-quality-supervisor-autonomous-oversight"><strong>Supervise & steer</strong><span>Dana quality supervisor: advisory critique cards, autonomous steering, and stage audit notes.</span></a></div><h2 id="how-it-works">How it works</h2><p>BuildRelay coordinates a sequential, role-based engineering team overseen by Dana Quality Supervisor. Tasks flow from prompt alignment through research and dual specifications to container-isolated execution and live verification:</p><img class="diagram" src="diagrams/workflow.svg" alt="BuildRelay 4-lead workflow overseen by Dana Quality Supervisor with interactive grill alignment, dual specifications, backend-first Docker verification, and continuous feature iteration."><h3 id="autonomous-leads">The 5-Lead Autonomous Engineering Team</h3><p>Every lead operates with typed inputs, explicit contracts, and dedicated domain expertise:</p><div class="agent-roster"><div class="agent-card agent-natasha"><div class="agent-badge">Natasha</div><div class="agent-title">Coordinator & Alignment</div><ul class="agent-bullets"><li>Produces typed task brief and 5-sentence intent alignment brief.</li><li>Conducts interactive Grill-Me interviews (up to 10 questions) to clarify edge cases.</li><li>Routes cleanly to research, design, or implementation.</li></ul></div><div class="agent-card agent-odin"><div class="agent-badge">Odin</div><div class="agent-title">Researcher</div><ul class="agent-bullets"><li>Traverses local Markdown vault knowledge graph via Graphify.</li><li>Verifies external package registries (PyPI, npm) and Tavily search snippets.</li><li>Tasks marked <code>--research-only</code> complete cleanly after Odin.</li></ul></div><div class="agent-card agent-taghi"><div class="agent-badge">Taghi</div><div class="agent-title">Architect & UI Designer</div><ul class="agent-bullets"><li>Dual specifications: <code>spec.md</code> (Backend) and <code>ui.md</code> (UI/UX).</li><li>Conducts dedicated UI/UX Ergonomics Grill and presents unified proposal gate.</li><li>Mandates offline Docker mocks and backend-first phased execution.</li></ul></div><div class="agent-card agent-meti"><div class="agent-badge">Meti</div><div class="agent-title">Phased Implementer</div><ul class="agent-bullets"><li>Executes inside Docker container sandbox with zero host leakage.</li><li>Verifies core backend logic and Tier 1 unit tests first.</li><li>Constructs responsive Tailwind UI surfaces and Tier 2 live smoke scripts.</li></ul></div><div class="agent-card agent-dana"><div class="agent-badge">Dana</div><div class="agent-title">Quality Supervisor</div><ul class="agent-bullets"><li>Supervises intermediate deliverables across all stages against 5 core criteria.</li><li>Advisory critique cards (<code>--dana</code>) or autonomous lead steering (<code>--supervise autonomous</code>).</li><li>Persists structured audit notes under <code>vault/supervision/</code>.</li></ul></div></div><h3 id="two-tier-verification">Two-Tier Verification Architecture</h3><p>AI-generated code frequently breaks when external cloud dependencies or credentials fail. BuildRelay eliminates flakiness with a two-tier verification architecture: offline deterministic unit tests inside Docker (Tier 1) followed by guided live smoke verification on the host (Tier 2).</p><img class="diagram" src="diagrams/two-tier-verification.svg" alt="Two-Tier Verification Architecture: Tier 1 automated Docker sandbox with zero network and deterministic service adapters; Tier 2 guided live verification runner with real credentials."><h2 id="start-here">Start here</h2><div class="guide-links"><a href="quickstart.html"><strong>Install & run</strong><span>Set up a provider and try a first task.</span></a><a href="projects.html"><strong>Project memory & REPL</strong><span>Explore interactive project sessions, live verification, and UI preview.</span></a><a href="example.html"><strong>Inspect a real terminal capture</strong><span>CLI options and the actual offline test suite.</span></a><a href="architecture.html"><strong>Explore the architecture</strong><span>Typed handoffs, persistence, and execution policy.</span></a><a href="limitations.html"><strong>Understand the boundaries</strong><span>Validation, network access, and isolation limits.</span></a><a href="workflow.html#dual-specification-architecture-uiux-design-standards"><strong>Dual-spec & UI preview</strong><span>Dedicated backend and UI/UX design specs with local web preview server.</span></a></div><h2 id="before-you-run">Before you run</h2><p>You need Python 3.11+, Docker, and a configured model provider or compatible local endpoint. This is a local, single-user tool. Passing phase commands does not guarantee correctness; review the code and checks before relying on them.</p>'''
(DOCS/'index.html').write_text(page('index','Introduction',home,['How it works','Autonomous leads','Two-tier verification','Start here','Before you run']))
transcript=(DOCS/'examples/terminal-session.txt').read_text()
example='''<h1>A real terminal capture</h1><p class="lead">Inspect the CLI and its offline tests before running a model-powered task.</p><div class="notice"><strong>What this capture demonstrates</strong><p>This is actual command output recorded locally on 28 October 2026. It shows CLI capabilities and deterministic platform checks. It is not an AI implementation run, an integration test, or a benchmark.</p></div><img class="diagram" src="examples/terminal-preview.svg" alt="Excerpt of actual CLI help and offline test output; full transcript follows."><h2 id="recorded-output">Recorded output</h2><p>No animation or simulated success messages. <a href="examples/terminal-session.txt">Open the full plain-text transcript</a>.</p><pre class="capture"><code>'''+html.escape(transcript)+'''</code></pre><h2 id="try-a-development-task">Try a development task</h2><p>After <a href="quickstart.html">setup</a>, use this small task as a reproducible demo prompt. The following is a suggested command, not output from the capture above.</p><pre><code>python main.py "Build a Python CSV validator that reports missing required columns and invalid numeric amounts. Include valid and invalid fixtures, automated tests, and a README with run commands." --project csv-demo --image python:3.11-slim --step</code></pre><p>Inspect the plan, generated files, and phase results. Keep provider sign-in and configuration outside any screen recording. Only demonstrate resume with a task that was actually interrupted or failed.</p>'''
(DOCS/'example.html').write_text(page('example','Terminal example',example,['Recorded output','Try a development task']))
print('Built introduction, terminal example, and',len(PAGES),'guides from README.md.')
