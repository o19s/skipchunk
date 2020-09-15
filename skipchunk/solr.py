import json
import requests
import datetime

import jsonpickle

def pretty(obj):
    print(jsonpickle.encode(obj,indent=2))

## -------------------------------------------
## Java-Friendly datetime string format

def timestamp():
    return datetime.datetime.now().isoformat() + 'Z'

## -------------------------------------------
## Core Admin!
## TODO: These will eventually be abstracted for both Solr and Elasticsearch 

def indexExists(host,name):
    uri = host + 'admin/cores?action=STATUS&core=' + name
    r = requests.get(uri)
    if r.status_code == 200:
        data = r.json()
        if name in data['status'].keys():
            if "name" in data['status'][name].keys():
                if data['status'][name]["name"]==name:
                    return True
    return False


def indexCreate(host,name,path,timeout=10000):

    #Set this to true only when core is created
    success = False

    if not indexExists(host,name):
        try:            
            #Create the core in solr
            uri = host + 'admin/cores?action=CREATE&name='+name+'&instanceDir='+path+'/conf&config=solrconfig.xml&dataDir='+path+'/data'
            r = requests.get(uri)
            if r.status_code == 200:
                success = True
                #Say cheese
                print('Core',name,'created!')
            else:
                print('SOLR ERROR! Core',name,'could not be created! Have a nice day.')
                print(json.dumps(r.json(),indent=2))

        except:
            print('NETWORK ERROR! Could not connect to Solr server on',host,' ... Have a nice day.')

    return success

def indexList(host):
    cores = []
    try:            
        #Lookup all the cores:
        uri = host + 'admin/cores?action=STATUS'
        r = requests.get(uri)
        if r.status_code == 200:
            #Say cheese
            cores = list(r.json()['status'].keys())

        else:
            print('SOLR ERROR! Cores could not be listed! Have a nice day.')
            print(json.dumps(r.json(),indent=2))

    except:
        print('NETWORK ERROR! Could not connect to Solr server on',host,' ... Have a nice day.')
    
    return cores

## -------------------------------------------
## Pass-through query!
## Just take the query as provided, run it against solr, and return the raw response

def passthrough(uri):
    req = requests.get(uri)
    return req.text,req.status_code
    