from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
import uvicorn
import requests
import pymongo
from bson.objectid import ObjectId
from log import logger
import time
from config import agent


app = Starlette(debug=True)


class DB():

    def __init__(self):
        mongo = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = mongo["pai"]


    def insert_one(self, collection,data):
        one = self.db[collection].insert_one(data)
        return one.inserted_id


    def find(self, collection, query=None, projection=None):
        _data = self.db[collection].find(query, projection)
        data = []
        for d in _data:
            d['_id'] = str(d['_id'])
            data.append(d)
        return data


    def find_one(self, collection, query=None, projection=None):
        _data = self.db[collection].find(query, projection).limit(0)
        data = []
        for d in _data:        
            if d.get('_id'):
                d['_id'] = str(d['_id'])
                data.append(d)
        return data


    def update_one(self, collection, query, data):
        self.db[collection].update_one(query, data)


    def update_many(self, collection, query, data):
        self.db[collection].update_many(query, data)        

mongo = DB()


def start_task(_id):

    def update(_id, key, status):
        mongo.update_one('task', {'_id': _id}, { "$set": { "result": status, "newest": 'Y', 'update': int(time.time() * 1000)} })

    update(_id, 'result', 'RUNING')
    
    while True:
        print('--- true ---')
        data = mongo.find_one('task', {'_id': _id})[0]
        
        steps = data['steps']
        print(f'steps:\n{steps}')
        for step in steps:
            time.sleep(1)
            print(f'--- for ---\n{step}')
            result = data['result']
            if step['result'] == 'RUNING':
                start = step['start']
                timeout = step.get('timeout', 300)
                cost = time.time() - start
                if cost > timeout:
                    mongo.update_one('task', {'_id': _id, 'steps.no': step['no']}, { '$set': { 'steps.$.is_timeout': 'Y', 'steps.$.end': time.time()}})  
                    update(_id, 'is_timeout', 'Y')
                    break
            if result != 'RUNING' or data['is_timeout'] == 'Y':
                break

            if step['result'] == 'INIT' and step.get('wait'):
                flag = 0
                for no in step['wait']:
                    logger.info(f'******no:{no}, {steps[no]["result"]}')
                    if steps[no]['result'] != 'SUCCESSFUL':
                        flag = 1
                if flag:
                    continue

            if step['result'] == 'INIT':
                step['_id'] = str(_id)
                mongo.update_one('task', {'_id': _id, 'steps.no': step['no']}, { '$set': { 'steps.$.result': 'RUNING', 'steps.$.start': time.time()}})  
                requests.post('http://127.0.0.1:80'+'/call_function', json=step)
    
        flag = 0
        for step in steps:
            if step['result'] in ('INIT', 'RUNING') and data['is_timeout'] != 'Y':
                flag = 1
            if step['result'] in ('FAILURE',):
                update(_id, 'result', step['result'])
                flag = step['result']
                break

        if flag == 1:
            continue
        elif flag in ('FAILURE',):
            break
        else:
            if data['result'] in('STOPPING', 'STOPPED'):
                update(_id, 'result', 'STOPPED')
            else:
                update(_id, 'result', 'SUCCESSFUL')
            break
        
        time.sleep(1)
    

    
@app.route('/')
async def home(request):
    data = mongo.find('plan')
    return JSONResponse(data)


@app.route('/new_plan', methods=['POST'])
async def new_plan(request):
    data = await request.json()
    mongo.insert_one('plan', data)
    message = {'code': '0', 'message': 'OK'}
    return JSONResponse(message)


@app.route('/call_plan', methods=['POST'])
async def call_plan(request):
    '''
    data: {'plan': 'ghuadshgdfsdfafdaf'}
    '''    
    _data = await request.json()
    query = _data.get('query', None)
    projection = _data.get('projection', None)
    if query and query.get('_id'):
        query['_id'] = ObjectId(query['_id'])
    if projection:
        projection['_id'] = 0

    projection = _data.get('projection', None)
    data = mongo.find_one('plan', query, projection)

    if data:
        d = data[0]
        d['id'] = d.pop('_id')
        mongo.update_many('task', {'id': d['id']}, { "$set": { "newest": 'N'} })
        _id = mongo.insert_one('task', d)        
        task = BackgroundTask(start_task, _id=_id)
        message = {'code': '0', '_id': str(_id), 'message': 'OK'}
        return JSONResponse(message, background=task)        
    else:
        return JSONResponse({'code': 7, 'message': f'The DB have not find the plan'}, status_code=401)


@app.route('/plan', methods=['post'])
async def plan(request):
    _data = await request.json()
    query = _data.get('query', None)
    projection = _data.get('projection', None)
    if query and query.get('_id'):
        query['_id'] = ObjectId(query['_id'])
    if projection:
        projection['_id'] = 0

    projection = _data.get('projection', None)
    data = mongo.find_one('plan', query, projection)

    if data:
        return JSONResponse({'code': 0, 'data': data[0]})
    else:
        return JSONResponse({'code': 6, 'message': f'The DB have no record: {str(query["_id"])}'}, status_code=401)


@app.route('/plans', methods=['post'])
async def plans(request):
    _data = await request.json()
    query = _data.get('query', None)
    projection = _data.get('projection', None)
    data = mongo.find('plan', query, projection)
    return JSONResponse({'code': 0, 'data': data})


@app.route('/task', methods=['post'])
async def task(request):
    _data = await request.json()
    query = _data.get('query', None)
    projection = _data.get('projection', None)
    if query and query.get('_id'):
        query['_id'] = ObjectId(query['_id'])
    if projection:
        projection['_id'] = 0

    projection = _data.get('projection', None)
    data = mongo.find_one('task', query, projection)

    if data:
        return JSONResponse({'code': 0, 'data': data[0]})
    else:
        return JSONResponse({'code': 6, 'message': f'The DB have no record: {str(query["_id"])}'}, status_code=401)


@app.route('/tasks', methods=['post'])
async def tasks(request):
    _data = await request.json()
    query = _data.get('query', None)
    projection = _data.get('projection', None)
    data = mongo.find('task', query, projection)
    return JSONResponse({'code': 0, 'data': data})

  
@app.route('/update_function_status', methods=['POST'])
async def update_function_status(request):
    data = await request.json()
    print(f'--- data ---\n{data}')
    _id = data['_id']
    no =  data['no']   
    code = data['code']
    message = data['message']

    # insert into MongoDB
    mongo.update_one('task', {'_id': ObjectId(data['_id']), 'steps.no': no}, { '$set': { 'steps.$.result': code, 'steps.$.message': message, 'steps.$.end': time.time()}})       

    if code != 'SUCCESSFUL':
        mongo.update_one('task', {'_id': ObjectId(data['_id'])}, { '$set': {'result': 'FAILURE'}})

    logger.info(f'POST /update_function_status, _id: {_id}, step: {no+1}, code: {code}, message: {message}')

    message = {'code': 0, 'message': 'OK'}
    return JSONResponse(message)


@app.route('/call_function', methods=['POST'])
async def call_function(request):
    data = await request.json()

    # 入参完整性判断
    no_key = []
    for k in ('_id', 'agent', 'moudle', 'function'):
        if k not in data:
            no_key.append(k)
    if no_key:
        logger.info(f'POST /call, data: {data}')
        logger.error(f'the request have no key: {",".join(no_key)}') 
        return JSONResponse({'code': '1', 'message': f'the request have no key: {",".join(no_key)}'})

    agent_url = agent.get(data['agent'])
    if not agent_url:
        logger.info(f'POST /call_function, data: {data}')
        logger.error(f'the server config is no agent: {data["agent"]}') 
        return JSONResponse({'code': '2', 'message': f'the server config is no agent: {data["agent"]}'})

    logger.info(f'POST /call_function, data: {data}')

    r = requests.post(agent_url+'/call', json=data)
    return JSONResponse(r.json(), status_code = r.status_code)

    
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=80)    