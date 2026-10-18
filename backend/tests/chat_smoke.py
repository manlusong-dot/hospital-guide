import urllib.request, json

# Test 1: Create a new chat session
data = json.dumps({'message': '我牙疼', 'dept_id': None, 'session_id': None}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/chat', data=data, headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req).read().decode())
print('=== Test 1: New session ===')
print('session_id:', resp['session_id'])
print('is_question:', resp.get('is_question'))
print('step key:', resp['step']['key'] if resp['step'] else None)
print()

sid = resp['session_id']

# Test 2: Ask '药怎么吃' - should be a question, not advance step
data = json.dumps({'message': '药怎么吃', 'session_id': sid}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/chat', data=data, headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req).read().decode())
print('=== Test 2: 药怎么吃 ===')
print('is_question:', resp.get('is_question'))
print('step key:', resp['step']['key'] if resp['step'] else None)
print('reply:', resp['reply'][:80])
print()

# Test 3: Say '下一步' - should advance step
data = json.dumps({'message': '下一步', 'session_id': sid}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/chat', data=data, headers={'Content-Type': 'application/json'})
resp = json.loads(urllib.request.urlopen(req).read().decode())
print('=== Test 3: 下一步 ===')
print('is_question:', resp.get('is_question'))
print('step key:', resp['step']['key'] if resp['step'] else None)
print()

# Test 4: List sessions
resp = json.loads(urllib.request.urlopen('http://127.0.0.1:8000/api/chat/sessions').read().decode())
print('=== Test 4: Sessions list ===')
for s in resp:
    status = 'finished' if s['finished'] else 'ongoing'
    print(f"  {s['session_id']}: {s['dept_name']} - {status}")
