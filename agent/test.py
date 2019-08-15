from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
import uvicorn
import requests
from log import logger
from config import server


app = Starlette(debug=True)


def call(moudle, function, _id, no, data):
    update_function_status = server + '/update_function_status'
    code = f'''from lib.{moudle} import {function}
try:
    {function}(data)
except Exception as e:
    error = {{'_id': '{_id}', 'code': 'FAILURE', 'message': str(e)}}
    logger.info('call {moudle}.{function}, data:' + str(error))
    r = requests.post('{update_function_status}', json=error)
else:
    ok = {{'_id': '{_id}', 'no': {no}, 'code': 'SUCCESSFUL', 'message': ''}}
    logger.info('call {moudle}.{function}, data:' + str(ok))
    r = requests.post('{update_function_status}', json=ok)
'''
    exec(code)


@app.route('/')
async def homepage(request):
    return JSONResponse({'Pai Agent': '0.1'})


@app.route('/call', methods=['POST'])
async def _call(request):
    _data = await request.json()
    _id = _data['_id']
    no = _data['no']
    moudle = _data['moudle']
    function = _data['function']
    data = _data['data']

    logger.info(f'POST /call, data: {_data}')

    try:
        code = f'from lib.{moudle} import {function}'
        exec(code)
    except:
        message = {'code': '2', 'message': f'the agent have no function: {moudle}.{function}'}
        return JSONResponse(message, status_code=401)

    task = BackgroundTask(
        call, moudle=moudle, function=function, _id=_id, no=no, data=data)
    message = {'code': '0', 'message': 'OK'}
    return JSONResponse(message, background=task)

    
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)    