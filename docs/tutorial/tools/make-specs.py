#!/usr/bin/env python3
"""Builds the Octoloom screenshot specs for the tutorial.

Each build step of the two example networks becomes a cut-down agent-network.yaml
(what you have on the canvas after that step) and one screenshot spec.

Matches Octoloom 0.9.25 (octoloom-local-checks-0925.vsix).

Usage: python3 make-specs.py <wrapper-repo> <out-dir>
Then, from the Octoloom repo:
  OUT=<shots> node .claude/skills/octoloom-screenshot/shot.mjs <out-dir>/*.json
"""
import copy, json, os, sys
import yaml

repo, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
ex = os.path.join(repo, 'examples')
GUIDES = ['v1', 'v2', 'agent']
THEMES = ['dark', 'light']
SEL = "const n=document.querySelector(%s)?.closest('.nc'); if(n){const r=n.getBoundingClientRect(); const o={bubbles:true,clientX:r.left+40,clientY:r.top+14,pointerId:1}; n.dispatchEvent(new PointerEvent('pointerdown',o)); n.dispatchEvent(new PointerEvent('pointerup',o));}"


def dump(d):
    return yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=200)


def spec(name, view, messages, size='1500,900', after=None, state=None):
    s = {'name': name, 'view': view, 'themes': THEMES, 'size': size, 'messages': messages}
    if after:
        s['after'] = after
    if state:
        s['state'] = state
    json.dump(s, open(os.path.join(out, name + '.json'), 'w'), indent=1)


def net_doc(name, project, version, text, after=None, size='1800,950', ctx=None, state=None):
    m = {'type': 'doc', 'kind': 'network', 'fileName': 'agent-network.yaml',
         'uri': f'file:///demo/{project}/agent-network.yaml', 'text': text, 'guidesSeen': GUIDES,
         'network': ctx or {'version': version}}
    spec(name, 'network', [m], size=size, after=after, state=state)


def select(label):
    return SEL % json.dumps('.nc-tile[title="Minimize %s to its icon"]' % label)


# ---------------------------------------------------------------- v1 Library Loans
v1 = yaml.safe_load(open(os.path.join(ex, 'v1-library-loans', 'agent-network.yaml')))
B1 = 'jev_lib1_library-broker'
broker = v1['brokers'][B1]


def v1_step(llm=False, mcp=False, agents=False, instr=False):
    d = {'schemaVersion': v1['schemaVersion'], 'label': v1['label']}
    b = copy.deepcopy(broker)
    sp = b['spec']
    if not llm:
        sp.pop('llm')
    if not mcp:
        sp.pop('tools')
    if not agents:
        sp['links'] = []  # Add broker writes an empty list
    if not instr:
        sp['instructions'] = ['You help library members borrow books.']
        for k in ('maxNumberOfLoops', 'maxConsecutiveErrors', 'taskTimeoutSecs'):
            sp.pop(k)
    d['brokers'] = {B1: b}
    conns = {}
    if llm:
        d['llmProviders'] = v1['llmProviders']
        conns['jev-lib1-llm-connection'] = v1['connections']['jev-lib1-llm-connection']
    if mcp:
        conns['jev-lib1-catalog-mcp-connection'] = v1['connections']['jev-lib1-catalog-mcp-connection']
    if agents:
        for k in ('jev-lib1-membership-agent-connection', 'jev-lib1-recommendation-agent-connection'):
            conns[k] = v1['connections'][k]
    if conns:
        d['connections'] = conns
    if mcp:
        d['mcpServers'] = v1['mcpServers']
    if agents:
        d['agents'] = v1['agents']
    return dump(d)


P1 = 'jev-library-loans-v1'
# What Octoloom 0.9.25 writes: a blank project, then "Add broker" (the broker refers to an LLM "openai"
# that is not defined yet), then "+ > LLM provider" defines "openai" and "openai-connection".
BLANK1 = 'schemaVersion: 1.0.0\nlabel: "%s"\nbrokers: {}\n' % P1
ADDED1 = dump({'schemaVersion': '1.0.0', 'label': P1, 'brokers': {'my-broker': {
    'card': {'protocolVersion': '0.3.0', 'name': 'my-broker', 'description': 'Describe what this broker does.', 'url': '${ingressgw.url}/my-broker',
             'version': '1.0.0', 'capabilities': {'streaming': False, 'pushNotifications': False, 'stateTransitionHistory': False},
             'defaultInputModes': ['application/json', 'text/plain'], 'defaultOutputModes': ['application/json', 'text/plain'], 'skills': []},
    'spec': {'llm': {'ref': {'name': 'openai'}, 'configuration': {'model': 'gpt-5-mini'}}, 'instructions': ['You are a helpful broker.'], 'links': []}}}})
ADD_MENU = "document.querySelector('.fab.primary')?.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:60,clientY:170}))"
net_doc('v1-01-empty', P1, 'v1', BLANK1)
net_doc('v1-02-broker-added', P1, 'v1', ADDED1)
net_doc('v1-add-menu', P1, 'v1', ADDED1, after=ADD_MENU + ";setTimeout(()=>{const it=[...document.querySelectorAll('.menu button, .menu [role=menuitem], .menu .mi')].find(b=>b.textContent.includes('LLM provider')); if(it){it.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true})); it.dispatchEvent(new MouseEvent('mouseover',{bubbles:true})); it.click();}},120)")
# "+ > LLM provider": defines openai and openai-connection (the broker's reference now resolves)
DEF1 = yaml.safe_load(ADDED1)
DEF1['llmProviders'] = {'openai': {'label': 'OpenAI', 'metadata': {'platform': 'OpenAI', 'models': ['gpt-5-mini', 'gpt-5']}}}
DEF1['connections'] = {'openai-connection': {'kind': 'llm', 'ref': {'name': 'openai'}, 'spec': {'url': 'https://api.openai.com/v1', 'configuration': {'apiKey': '${openai.apiKey}'}}}}
net_doc('v1-02b-openai-defined', P1, 'v1', dump(DEF1), after=select('OpenAI'))
net_doc('v1-03-llm', P1, 'v1', v1_step(llm=True), after=select('Jev OpenAI Wrapper'))
net_doc('v1-04-mcp', P1, 'v1', v1_step(llm=True, mcp=True), after=select('Library Catalog MCP'))
net_doc('v1-05-agents', P1, 'v1', v1_step(llm=True, mcp=True, agents=True))
full1 = open(os.path.join(ex, 'v1-library-loans', 'agent-network.yaml')).read()
net_doc('v1-06-broker', P1, 'v1', full1, after=select(B1))
net_doc('v1-07-code', P1, 'v1', full1, state={'mode': 'code'})

# ---------------------------------------------------------------- v2 Restaurant Booking
v2 = yaml.safe_load(open(os.path.join(ex, 'v2-restaurant-booking', 'agent-network.yaml')))
B2 = 'jev_rb2_booking_broker'
P2 = 'jev-restaurant-booking-v2'
flow = open(os.path.join(ex, 'v2-restaurant-booking', 'brokers', 'booking-broker.agent')).read()


def v2_step(llm=False, mcp=False, agents=False):
    d = {'agentNetwork': v2['agentNetwork'], 'info': v2['info'], 'registry': {}}
    r, conns = d['registry'], {}
    if agents:
        r['agents'] = v2['registry']['agents']
        for k in ('jev_rb2_menu_agent_connection', 'jev_rb2_loyalty_agent_connection'):
            conns[k] = v2['context']['connections'][k]
    if mcp:
        r['mcps'] = v2['registry']['mcps']
        conns['jev_rb2_tables_mcp_connection'] = v2['context']['connections']['jev_rb2_tables_mcp_connection']
    if llm:
        r['llms'] = v2['registry']['llms']
        conns['jev_rb2_llm_connection'] = v2['context']['connections']['jev_rb2_llm_connection']
    if not r:
        d.pop('registry')
    if conns:
        d['context'] = {'connections': conns}
    d['brokers'] = v2['brokers']
    return dump(d)


all_conns = {'jev_rb2_menu_agent_connection': 'a2a', 'jev_rb2_loyalty_agent_connection': 'a2a',
             'jev_rb2_tables_mcp_connection': 'mcp', 'jev_rb2_llm_connection': 'llm'}
ctx2 = {'version': 'v2', 'brokerFiles': {B2: 'brokers/booking-broker.agent'},
        'brokerTargets': {B2: list(all_conns)}}
BLANK2 = 'agentNetwork: 2.0.0\ninfo:\n  label: "%s"\n  version: v1\nbrokers: {}\n' % P2
ADDED2 = dump({'agentNetwork': '2.0.0', 'info': {'label': P2, 'version': 'v1'}, 'brokers': {'my_broker': {
    'kind': 'AgentScript', 'implementation': './brokers/my_broker.agent', 'interfaces': {'a2a': {'card': {
        'name': 'My Broker', 'description': 'Describe what this broker does.', 'version': '1.0.0',
        'capabilities': {'streaming': True, 'pushNotifications': False}, 'defaultInputModes': ['text/plain'], 'defaultOutputModes': ['text/plain'], 'skills': []}}}}}})
net_doc('v2-01-empty', P2, 'v2', BLANK2)
net_doc('v2-02-broker-added', P2, 'v2', ADDED2, ctx={'version': 'v2', 'brokerFiles': {'my_broker': 'brokers/my_broker.agent'}, 'brokerTargets': {'my_broker': ['openai_connection']}})
DEF2 = yaml.safe_load(ADDED2)
DEF2['registry'] = {'llms': {'openai': {'info': {'label': 'OpenAI'}, 'metadata': {'platform': 'OpenAI', 'models': ['gpt-5-mini', 'gpt-5']}}}}
DEF2['context'] = {'connections': {'openai_connection': {'kind': 'llm', 'ref': {'name': 'openai'}, 'url': 'https://api.openai.com/v1', 'authentication': {'kind': 'apiKey', 'apiKey': '${openai.apiKey}'}}}}
DEF2 = {k: DEF2[k] for k in ('agentNetwork', 'info', 'registry', 'context', 'brokers')}
net_doc('v2-02b-openai-defined', P2, 'v2', dump(DEF2), after=select('OpenAI'),
        ctx={'version': 'v2', 'brokerFiles': {'my_broker': 'brokers/my_broker.agent'}, 'brokerTargets': {'my_broker': ['openai_connection']}})
net_doc('v2-03-llm', P2, 'v2', v2_step(llm=True), after=select('Jev OpenAI Wrapper'),
        ctx={'version': 'v2', 'brokerFiles': {B2: 'brokers/booking-broker.agent'}, 'brokerTargets': {B2: ['jev_rb2_llm_connection']}})
net_doc('v2-04-upstreams', P2, 'v2', v2_step(llm=True, mcp=True, agents=True),
        ctx={'version': 'v2', 'brokerFiles': {B2: 'brokers/booking-broker.agent'}, 'brokerTargets': {B2: ['jev_rb2_llm_connection']}})
full2 = open(os.path.join(ex, 'v2-restaurant-booking', 'agent-network.yaml')).read()
net_doc('v2-06-network', P2, 'v2', full2, ctx=ctx2, after=select('Jev Restaurant Booking'))


def agent_doc(name, text, after=None):
    m = {'type': 'doc', 'kind': 'agent', 'fileName': 'booking-broker.agent',
         'uri': f'file:///demo/{P2}/brokers/booking-broker.agent', 'text': text, 'guidesSeen': GUIDES,
         'agent': {'brokerKey': B2, 'connections': all_conns}}
    spec(name, 'agent', [m], size='1500,900', after=after)


agent_doc('v2-05-flow', flow)

# ---------------------------------------------------------------- New project dialog (Blank, "Add a starter broker" off)
for v, n, pname in (('v1', 'v1-00-new-project', P1), ('v2', 'v2-00-new-project', P2)):
    spec(n, 'newProject', [{'type': 'newProjectInit', 'version': v, 'templates': [], 'source': 'bundled', 'folder': '/Users/demo/projects'}],
         size='1300,900', after="[...document.querySelectorAll('.np-tab')].find(b=>b.textContent.startsWith('Blank'))?.click(); setTimeout(()=>{const i=[...document.querySelectorAll('input')].find(x=>x.type!=='checkbox'&&!x.closest('.np-blank')); if(i){const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; s.call(i,%s); i.dispatchEvent(new Event('input',{bubbles:true}));}},60)" % json.dumps(pname))

# ---------------------------------------------------------------- Projects & Deploy, deploy form
def project(dirname, version, brokers):
    return {'dir': f'/tmp/demo/{dirname}', 'name': dirname, 'version': version, 'assetVersion': '1.0.0',
            'networkUri': f'file:///tmp/demo/{dirname}/agent-network.yaml', 'exchangeUri': f'file:///tmp/demo/{dirname}/exchange.json',
            'brokers': brokers, 'secrets': [{'key': 'jev.apiKey', 'description': 'Key of the Jev OpenAI wrapper (its wrapper.apiKey; secret, injected at deploy time)'}]}


status = {'type': 'status', 'status': {'anypoint': {'host': 'anypoint.mulesoft.com', 'org': 'Demo Org', 'env': 'Sandbox'}, 'a2d': True}}
cli = {'node': {'ok': True}, 'java': {'ok': True}, 'cli': {'version': '1.6.20'}, 'plugin': {'version': '1.5.0'}}
gws = {'type': 'gateways', 'env': 'Sandbox', 'gateways': [{'name': 'my-gateway', 'status': 'RUNNING', 'space': 'Cloudhub-US-East-2', 'spaceType': 'shared-space'}]}
spaces = {'type': 'spaces', 'spaces': [{'name': 'Cloudhub-US-East-2', 'type': 'shared', 'region': 'us-east-2'}]}
for name, dirname, version, brokers in (
        ('v1-08-deploy', P1, 'v1', []),
        ('v2-07-deploy', P2, 'v2', [{'key': B2, 'file': 'brokers/booking-broker.agent', 'uri': f'file:///tmp/demo/{P2}/brokers/booking-broker.agent'}])):
    spec(name, 'project', [status, {'type': 'projects', 'cli': cli, 'projects': [project(dirname, version, brokers)]}, gws, spaces], size='560,900',
         after="setTimeout(()=>{document.querySelector('.pcard-h, .pcard .ph, .pcard')?.click(); setTimeout(()=>document.querySelector('button[title=\"Deploy\"]')?.click(),80); setTimeout(()=>{const i=document.querySelector('.deploy input'); if(i){const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; s.call(i,'my-gateway'); i.dispatchEvent(new Event('input',{bubbles:true}));}},200);},50)")

# ---------------------------------------------------------------- Chat (replies are the real 1.2.0 regression answers)
def chat(name, project, version, netfile, key, title, url, proto, turns, uses, ctx):
    convs = {key: {'turns': []}}
    t0 = 1794811000000
    for i, (q, a, ms) in enumerate(turns):
        convs[key]['turns'].append({'id': 2 * i + 1, 'role': 'user', 'text': q, 'at': t0 + i * 60000})
        convs[key]['turns'].append({'id': 2 * i + 2, 'role': 'agent', 'text': a, 'at': t0 + i * 60000 + ms,
                                    'reply': {'ok': True, 'text': '', 'state': 'completed', 'httpStatus': 200, 'ms': ms}})
    msg = {'type': 'chatInit', 'dir': f'/tmp/{project}', 'project': project, 'version': version, 'network': netfile,
           'brokers': [{'key': key, 'name': title, 'url': url, 'protocol': proto, 'skills': []}],
           'deployment': {'env': 'Sandbox', 'gateway': 'my-gateway', 'status': 'running',
                          'brokers': [{'key': key, 'url': url, 'protocol': proto, 'ok': True, 'http': 200}]},
           'uses': {key: uses}, 'networkCtx': ctx}
    spec(name, 'chat', [msg], size='1500,900', state={'chat:broker': key, 'chat:target': 'deployed', 'chat:convs': convs, 'chat:left': 'network'})


chat('v1-09-chat', P1, 'v1', full1, B1, 'Library Broker', f'https://my-gateway.example.com/{B1}/', '0.3.0', [
    ('I am member M-666. Please check my membership and place a hold on Dune for me.',
     "You are currently blocked from placing a hold on 'Dune' because you have unpaid fines of 18.50 EUR. Please pay your fines to be able to hold books.", 9200),
    ('I am member M-501. Is Dune available? If not, please place a hold for me.',
     "The book 'Dune' is currently not available for borrowing. However, a hold has been successfully placed for you, member M-501. Your hold ID is **HLD-7781**, and you are in the 2nd position in the queue for pickup at the Main branch.", 11800),
    ('I loved Dune. Can you recommend similar books?',
     'You might enjoy these books similar to Dune: **Hyperion** by Dan Simmons and **Foundation** by Isaac Asimov. Both are available.', 6100),
], list(v1['connections']), {'version': 'v1'})
chat('v2-08-chat', P2, 'v2', full2, B2, 'Jev Restaurant Booking Broker', f'https://my-gateway.example.com/{B2}/', '1.0', [
    ('Table for 4 on 2026-11-20 at 19:30 for Maria Rossi. One guest has a nut allergy.',
     'Your table for 4 has been successfully booked for Maria Rossi on November 20, 2026, at 19:30.\n\n- **Booking ID:** RSV-5521\n- **Safe Dishes for Nut Allergy:** Grilled salmon, risotto ai funghi, lemon sorbet. Please avoid the pesto pasta and the praline cake.\n- **Loyalty Perks:** As a Gold member, Maria has 1,240 points, which includes a free welcome drink for the table and 10% off the bill.', 14500),
], list(all_conns), ctx2)

print('\n'.join(sorted(os.listdir(out))))
