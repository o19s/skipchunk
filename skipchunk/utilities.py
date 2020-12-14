import os
import datetime

## -------------------------------------------
## Java-Friendly datetime string format

def timestamp():
    return datetime.datetime.now().isoformat() + 'Z'


## -------------------------------------------
## Gets the root path of this module

def configPath(target_dir):
    module_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = module_dir[0:module_dir.rfind('/')]
    graph_source = os.path.join(source_dir,target_dir)
    return graph_source
