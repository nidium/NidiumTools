#!/usr/bin/env python2.7

import os, stat
from konstructor import CommandLine

def createConfigure(path, name):
    content = """#!/usr/bin/env python2.7
from konstructor import Build
from konstructor import Builder

Build.add(Builder.Gyp('gyp/{0}.gyp'));
"""

    f = os.path.join(path, name, "configure")
    with open(f, "w") as configure:
        configure.write(content.format(name))

    st = os.stat(f)
    os.chmod(f, st.st_mode | stat.S_IEXEC)

def createGyp(path, name, classname):
    content = """{{
    'targets': [{{
        'target_name': '{0}',
        'type': 'shared_library',
        'dependencies': [
            '<(native_nativejscore_path)/gyp/nativejscore.gyp:nativejscore-includes', 
            '<(native_network_path)/gyp/network.gyp:nativenetwork-includes'
        ],
        'include_dirs': [
            '<(third_party_path)/'
        ],
        'sources': [ '../{1}.cpp'],
        'conditions': [
            ['OS=="mac"', {{
                'xcode_settings': {{
                    'OTHER_LDFLAGS': [
                        '-undefined suppress',
                        '-flat_namespace'
                    ],
                }},
            }},{{
                'cflags': [
                    '-fPIC',
                ],
                'ldflags': [
                    '-fPIC',
                ],
            }}]
        ],
    }}],
}}"""

    with open(os.path.join(path, name, "gyp", name + ".gyp"), "w") as gypfile:
        gypfile.write(content.format(name, classname))

def createSource(path, name, classname):
    currentDir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(currentDir, "module_templates", "templateSource.txt"), "r") as srcfile:
        src = srcfile.read()

    with open(os.path.join(path, name, classname + ".cpp"), "w") as cppfile:
        cppfile.write(src.format(classname=classname))

    with open(os.path.join(currentDir, "module_templates", "templateSourceHeader.txt"), "r") as srcfile:
        src = srcfile.read()

    with open(os.path.join(path, name, classname + ".h"), "w") as cppfile:
        cppfile.write(src.format(classname=classname))


@CommandLine.option("--name", prompt="The module name", help='What\'s the module name.')
@CommandLine.option("--classname")
@CommandLine.option("--path")
def createmodule(name, classname, path):
    """Create a new Native Module."""

    if classname is None:
        classname = name

    if path is None:
        path = os.getcwd()

    try:
        os.makedirs(os.path.join(path, name, "gyp"))
    except:
        pass

    print("Creating new module in %s " % (os.path.abspath(os.path.join(path, name))))

    createConfigure(path, name)
    createGyp(path, name, classname)
    createSource(path, name, classname)

    print("Now build by adding --module=%s to the configure script of NativeStudio or NativeServer" % (os.path.abspath(os.path.join(path, name))))

if __name__ == '__main__':
    CommandLine.parse()
