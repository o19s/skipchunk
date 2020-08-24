import sq
import os
import shutil

host = 'http://localhost:8983/solr/'
name = 'skipchunk-003'

path = os.path.join(os.getcwd(),'skipchunk_data',name,'solr')
print(path)
if not os.path.isdir(path):
    module_dir = os.path.dirname(sq.__file__)
    pathlen = module_dir.rfind('/')+1
    source = module_dir[0:pathlen] + '/solr_home/configsets/skipchunk-configset'
    shutil.copytree(source,path)

#print(sq.coreExists(host,name))
sq.coreCreate(host,name,path)