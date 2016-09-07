#!/usr/bin/env python2.7

# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file.

import os, stat
from konstructor import CommandLine
from konstructor import Utils, assumeYes

TEMPLATES_PATH = os.path.abspath(os.path.dirname(__file__))

def loadTemplate(name):
    with open(os.path.join(TEMPLATES_PATH, "module_templates", name), "r") as srcfile:
        src = srcfile.read()

    return src

def createConfigure(name):
    src = loadTemplate("templateConfigure.txt")
    with open("configure", "w") as configure:
        configure.write(src.format(name))

    st = os.stat("configure")
    os.chmod("configure", st.st_mode | stat.S_IEXEC)

def createGyp(name, classname):
    Utils.mkdir("gyp")
    src = loadTemplate("templateGyp.txt")

    with open(os.path.join("gyp", name + ".gyp"), "w") as gypfile:
        gypfile.write(src.format(name, classname))

def createSource(name, classname):
    src = loadTemplate("templateSource.cpp.txt")
    with open(os.path.join(classname + ".cpp"), "w") as cppfile:
        cppfile.write(src.format(name=name, classname=classname))

    src = loadTemplate("templateSource.h.txt")
    with open(os.path.join(classname + ".h"), "w") as cppfile:
        cppfile.write(src.format(name=name, classname=classname))


def createDoc(name, classname):
    Utils.mkdir('docs')
    src = loadTemplate("templateDoc.cpp.py.txt")
    with open(os.path.join('docs', classname + ".cpp.py"), "w") as docfile:
        docfile.write(src.format(name=name, classname=classname))
    src = loadTemplate("templateIDL.txt")
    with open(os.path.join('docs', name + ".idl"), "w") as docfile:
        docfile.write(src.format(name=name, classname=classname))


def createVar(name, classname):
    for path in [
        'tests',
        os.path.join('tests',  'gunittest'),
        os.path.join('tests', 'jsunittest'),
        os.path.join('tests', 'jsautotest') ]:
        Utils.mkdir(path)
        with open(os.path.join(path, ".gitignore"), "w") as cppfile:
            cppfile.write('')

    with open(".gitignore", "w") as cppfile:
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

    moduleDir = (os.path.abspath(os.path.join(path, name)))

    if os.path.exists(moduleDir):
        ret = Utils.promptYesNo("Directory %s exists, any default module files will be overriden. Continue ? " % moduleDir)
        if not ret:
            Utils.exit()
    else:
        if not Utils.promptYesNo("module will be created in %s directory. Continue ?" % moduleDir):
            Utils.exit()

    Utils.mkdir(moduleDir)

    with Utils.Chdir(moduleDir):
        createConfigure(name)
        createGyp(name, classname)
        createSource(name, classname)
        createDoc(name, classname)
        createVar(name, classname)

    print("Your module is now ready. It can be build by adding the argument --module=%s to the configure script of NativeStudio or NativeServer" % (os.path.abspath(os.path.join(path, name))))
    print("You may want to create a repository for your module with 'git init {0}".format(name))

if __name__ == '__main__':
    CommandLine.parse()
