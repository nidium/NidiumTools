#!/bin/bash

# Preparations to move the 3 repo's to one repo

# {{{ Configuration
OUTPUT_PATH=./test_tmp
DEVEL_PATH=/data/Development/nidium
STUDIO_PATH=$DEVEL_PATH/NativeStudio
SERVER_PATH=$DEVEL_PATH/NativeServer
JSCORE_PATH=$SERVER_PATH/nativejscore
# }}}

# {{{ Todo
# * move libapenetwork to another location (third-party or in src?)
# * https://github.com/nidium/NativeJSCore/pull/40
# * remove https://github.com/nidium/NativeStudio/blob/master/gyp/osx/incbuild.sh
# * move the externals to third-party
# * change configure scripts and configs (third-party path, configuration )
# * change nativetools documentation and autotest build script
# * todo: common.gyp and config.gpyi need manual attention
# * change the test.gyp files for the gtest unittesst
# * check all the cmd that are commented here below
# * build server --unit-test --assume-yes
# * build studio --unit-test --assume-yes
# * change buildbot settings
# * src/Binding/JSConsole.cpp: remove '#if 0' around the for the server parts
# * namespace modules
# * change kontructor path for --module
# * change NativeTools/src/createModule.py for new module path
# * check README.md
# * create ycm_extra.conf
# * create tags.sh
# * commit
# * new repo on github
# * push to github
# * low prio: ycm setup
# * low prio: tags setup
# * low prio: entr setup
# }}}

set -e # stop on error
set -x # spit out commands be for running them

# {{{ cleanup and create
rm -rf $OUTPUT_PATH
mkdir -p $OUTPUT_PATH
cd $OUTPUT_PATH
# }}}

# {{{ structure
git init Nidium
cd Nidium
mkdir -p {doc,bin,src,gyp,patch,build,resources,testrun,third-party}
echo -e "konstructor.log\nconfigurec\bin\nbuild\ntestrun\nthird-party" > .gitignore
echo "" > doc/.gitignore
echo "" > bin/.gitignore
echo "" > src/.gitignore
echo "" > gyp/.gitignore
echo "" > patch/.gitignore
echo "*" > build/.gitignore
echo "*" > testrun/.gitignore
echo "*" > third-party/.gitignore
# }}}

# {{{ LICENSE AND README
touch LICENSE
cat $STUDIO_PATH/LICENSE >> LICENSE
cat $SERVER_PATH/LICENSE >> LICENSE
cat $JSCORE_PATH/LICENSE >> LICENSE
touch README.md
cat $STUDIO_PATH/README.md >> README.md
cat $SERVER_PATH/README.md >> README.md
cat $JSCORE_PATH/README.md >> README.md
# }}}

# {{{ patch
cp  $STUDIO_PATH/var/patch/* patch/
#cp $SERVER_PATH/var/patch/* patch/
cp  $JSCORE_PATH/var/patch/* patch/
# }}}

# {{{ src
mkdir -p src/{Core,IO,Net,Binding,App,Frontend,Graphics,Interface,AV,Tools,Server,Modules}
cp    $STUDIO_PATH/src/Binding/*  src/Binding/
cp    $STUDIO_PATH/src/Frontend/* src/Frontend/
cp    $STUDIO_PATH/src/Graphics/* src/Graphics/
cp    $STUDIO_PATH/src/IO/*       src/IO/
cp    $STUDIO_PATH/src/Tools/*    src/Tools/
cp    $STUDIO_PATH/src/Macros.h   src/
cp -R $STUDIO_PATH/av/*           src/AV/
cp -R $STUDIO_PATH/app/*          src/App/
cp -R $STUDIO_PATH/interface/*    src/Interface/
#todo external
#todo change include headers with 'sed -i'
cp    $SERVER_PATH/src/Server/*   src/Server/
cp    $SERVER_PATH/src/App/*      src/App/
#todo external
#todo change include headers with 'sed -i'

cp    $JSCORE_PATH/src/Core/*     src/Core/
cp    $JSCORE_PATH/src/IO/*       src/IO/
cp    $JSCORE_PATH/src/Net/*      src/Net/
cp    $JSCORE_PATH/src/Binding/*  src/Binding/
#todo change include headers with 'sed -i'

#todo change cppfiles and include path files with 'sed -i'
cp    $STUDIO_PATH/gyp/*.*        gyp/
cp    $SERVER_PATH/gyp/*          gyp/
cp    $JSCORE_PATH/gyp/*          gyp/
rm    gyp/common.gypi gyp/config.gypi
cp    $STUDIO_PATH/gyp/common.gypi gyp/studio_common.gypi
cp    $STUDIO_PATH/gyp/config.gypi gyp/studio_config.gypi
cp    $SERVER_PATH/gyp/common.gypi gyp/server_common.gypi
cp    $SERVER_PATH/gyp/config.gypi gyp/server_config.gypi
cp    $JSCORE_PATH/gyp/common.gypi gyp/jscore_common.gypi
#todo merge the 3 configure files
cp    $STUDIO_PATH/configure      configure_studio
cp    $SERVER_PATH/configure      configure_server
cp    $JSCORE_PATH/configure      configure_nidiumcore
# }}}

# {{{ tools
mkdir tools/
cp -R $STUDIO_PATH/tools/*          tools/
cp $STUDIO_PATH/gyp/osx/incbuild.sh tools/osx_incbuild.sh
echo "*.pyc" > tools/.gitignore
echo "*.pyc" > tools/installer/osx/support.gitignore
#todo: sed -i change gyp file
# }}}

# {{{ tests
mkdir -p tests/{gunittest,jsunittest,jsautotest}

#todo: change Konstructor to generate a autotest file with an unique name
echo "*" >                                           tests/jsautotest/.gitignore
cp -R $STUDIO_PATH/var/js/tests/unittests/*          tests/jsunittest/
#cp -R $STUDIO_PATH/var/studio/tests/unittests/*     tests/gunittest/
#mv tests/gunittest/tests.gyp                         gyp/studio_tests.gyp

cp -R $SERVER_PATH/var/js/tests/unittests/*          tests/jsunittest/
#cp -R $SERVER_PATH/var/server/tests/unittests/*     tests/gunittest/
#mv tests/gunittest/tests.gyp                         gyp/server_tests.gyp

cp -R $JSCORE_PATH/var/js/tests/*.js                 tests/
cp -R $JSCORE_PATH/var/js/tests/unittests/*          tests/jsunittest/
cp -R $JSCORE_PATH/var/nidiumcore/tests/unittests/*  tests/gunittest/
mv tests/gunittest/tests.gyp                         gyp/server_tests.gyp
# }}}

# {{{ doc
echo "*/*.pyc" > doc/.gitignore
cp $STUDIO_PATH/var/rawdoc/* doc/
cp $SERVER_PATH/var/rawdoc/* doc/
cp $JSCORE_PATH/var/rawdoc/* doc/
# }}}

# {{{ Resources
cp -R $STUDIO_PATH/resources/* resources/
# }}}

# {{{ Change rights
chmod -R 664 `find -type f`
chmod 774 `find . -type d`
chmod 774 `find . -type f -a \( -name 'configure' -o -name '*.py' -o -name '*.sh' \)`
touch `find .`
# }}}

#{{{ libapenetwork submodule
# (after the rights have been set)

# disabled to speedup testing
#git submodule add git@github.com:nidium/libapenetwork.git src/libapenetwork
#git submodule init
#git submodule update
#cd src/libapenetwork
#git checkout master
#cd ../..
# }}}

