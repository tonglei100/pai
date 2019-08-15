import requests
import time

server = 'http://127.0.0.1'

# INIT, SUCCESSFUL, RUNING, FAILURE, STOPPING, STOPPED

# --- NEW PLAN ---
plan = {
    'name': 'Fund Clear',  
    'group': 'FUND',
    'index': ['One','Two', 'Three'],  
    'result': 'INIT', 
    'is_timeout': 'N',
    'next': 1565839457,
    'update': int(time.time() * 1000),
    'steps': [
        {'no':0, 'name': 'is file exists', 'agent': 'FUND', 'moudle': 'files', 'function': 'exists', 'data':{'dir': '', 'path': 'app.py'}, 'result': 'INIT', 'is_timeout': 'N', 'wait': []},
        {'no':1, 'name': 'move the file', 'agent': 'FUND', 'moudle': 'files', 'function': 'copy', 'data':{'dir': '', 'source': 'app.py', 'destination': 'test.py'}, 'result': 'INIT', 'is_timeout': 'N', 'wait': [0]}
    ]
    }
r = requests.post(server+'/new_plan', json=plan)


# # --- QUERY PLAN LIST ---
# r = requests.post(server+'/plans', json={'query': {}, 'projection':{'steps': 0}})
# print(r.status_code)
# print(r.json())


# # --- QUERY PLAN ---
# r = requests.post(server+'/plan', json={'query': {'_id': '5d55170e73cfd0d15f918648'}})
# print(r.status_code)
# print(r.json())


# # --- CALL PLAN ---
# r = requests.post(server+'/call_plan', json={'query': {'_id': '5d55170e73cfd0d15f918648'}})
# print(r.status_code)
# print(r.json())


# # --- QUERY TASK LIST ---  
# r = requests.post(server+'/tasks', json={'query': {'newest': 'Y'}})    # newest=Y, return the newest task
# print(r.status_code)
# print(r.json())


# # --- QUERY TASK --- 
# r = requests.post(server+'/task', json={'query': {'_id': '5d5517efa9b7c36e3d064268'}})    # newest=Y, return the newest task
# print(r.status_code)
# print(r.json())