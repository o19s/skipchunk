"""
https://github.com/listatree/convert_md_2_rst/

Convert Markdown to reStructuredText extension for Sphinx Doc
Scans for '.md' files and converts them to '.rst' files using pandoc.
For use it just copy this file to your source directory and add
'convert_md_2_rst' to the 'extensions' value of your 'conf.py' file.
Ensure that the source path is in the Python sys path. For that
purpose you may add this line to 'conf.py':
sys.path.insert(0, os.path.abspath('.'))

"""

import os
import pypandoc

def setup():
    path = os.path.abspath('.')
    for dir,subdir,files in os.walk(path):
        for file in files:
            filename = os.path.join(dir, file)
            filename_parts = os.path.splitext(filename)
            if len(filename_parts) > 1:
                filename_ext = filename_parts[1]
                if filename_ext == '.md':
                    convert_md_2_rst_process(filename_parts[0])

def convert_md_2_rst_process(filename_root):
    filename_source = filename_root + ".md"
    filename_target = filename_root + ".rst"
    print('Converting', os.path.basename(filename_source), 'to', os.path.basename(filename_target))
    file_source = open(filename_source)
    lines = file_source.readlines()
    file_source.close()
    data = '\n'.join(lines)
    data = data.encode('utf-8')
    data = pypandoc.convert(data, 'rst', format='markdown')
    file_target = open(filename_target, "w")
    file_target.write(data)
    file_target.flush()
    file_target.close()

setup()