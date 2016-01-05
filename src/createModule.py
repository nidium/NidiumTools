#!/usr/bin/env python2.7

import os, stat
from konstructor import CommandLine

def createConfigure(path, name):
    currentDir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(currentDir, "module_templates", "templateConfigure.txt"), "r") as srcfile:
        src = srcfile.read()

    f = os.path.join(path, name, "configure")
    with open(f, "w") as configure:
        configure.write(src.format(name))

    st = os.stat(f)
    os.chmod(f, st.st_mode | stat.S_IEXEC)

def createGyp(path, name, classname):
    currentDir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(currentDir, "module_templates", "templateGyp.txt"), "r") as srcfile:
        src = srcfile.read()

    with open(os.path.join(path, name, "gyp", name + ".gyp"), "w") as gypfile:
        gypfile.write(src.format(name, classname))

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

def createDocAndVar(path, name, classname):
    basePath = os.path.join(path, name)

    os.makedirs(basePath + "/doc")
    with open("%s/doc/.gitignore" % (name), "w") as cppfile:
        cppfile.write('')

    os.makedirs(basePath + "/var/js/tests/unittests")
    with open("%s/var/js/tests/unittests/.gitignore" % (name), "w") as cppfile:
        cppfile.write('')

    os.makedirs(basePath + "/var/rawdoc")
    with open("%s/var/rawdoc/.gitignore" % (name), "w") as cppfile:
        cppfile.write('*.pyc\n')

    with open("%s/.gitignore" % (name), "w") as cppfile:
        cppfile.write('*.pyc\nkonstruct.log\nlockfile\nbuild\nthird-party\n')

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
    createDocAndVar(path, name, classname)

    print("You probably want to create a repository with 'git init {0}".format(name))
    print("Now build by adding --module=%s to the configure script of NativeStudio or NativeServer" % (os.path.abspath(os.path.join(path, name))))

if __name__ == '__main__':
    CommandLine.parse()
