import pymongo

mongo = pymongo.MongoClient("mongodb://localhost:27017/")
pai = mongo['pai']

plans  = pai['plan'].find({})
for plan in plans:
    plan['_id'] = str(plan['_id'])
    print(plan)


tasks  = pai['task'].find({})
for task in tasks:
    task['_id'] = str(task['_id'])
    print(task)