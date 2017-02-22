#!/usr/bin/env python2.7

# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file

import sys,os
from pprint import pprint


LOG_FILE = open('./konstruct.log', 'w')
OUTPUT = "build/"
ROOT = os.getcwd()

# {{{ Variables
class Variables:
    _store = {}

    @staticmethod
    def set(key, value):
        Variables._store[key] = value

    @staticmethod
    def get(key, default=None):
        if key in Variables._store:
            return Variables._store[key]
        else:
            return default
# }}}

# {{{ Konstruct
class Konstruct:
    _configuration = ["default"]
    _hooks = {
        "start": [],
        "preBuild": [],
        "postBuild": [],
        "preTests": [],
        "postTests": [],
    }

    @staticmethod
    def start():
        CommandLine.parse()

        Konstruct._runHook("start")

        Deps._process()

        Konstruct._runHook("preBuild")

        success = Build.run()

        Konstruct._runHook("postBuild", success)

    @staticmethod
    def hook(name):
        def decorator(f):
            Konstruct._hooks[name].append(f)

        return decorator

    @staticmethod
    def _runHook(name, *args):
        for hook in Konstruct._hooks[name]:
            hook(*args)

    @staticmethod
    def config(*args):
        for config in args:
            if config in Konstruct._configuration:
                return True

    @staticmethod
    def setConfigs(configs):
        for config in configs:
            if config not in Konstruct._configuration:
                Konstruct._configuration.append(config)

    @staticmethod
    def getConfigs():
        return Konstruct._configuration
# }}}

# {{{ Tests
class Tests:
    _tests = []

    @staticmethod
    def register(suites, builders=[]):
        for builder in builders:
            Build.add(builder)

        for suite in suites:
            Tests._tests.append(suite)

    @staticmethod
    def run():
        if len(Tests._tests) == 0:
            Log.debug("No tests defined")
            return False
        success = True
        for cmd in Tests._tests:
            dir_name = None
            if isinstance(cmd, tuple):
                dir_name = cmd[1]
                cmd = cmd[0]
            Log.info("Running tests suite : %s" % (cmd))
            code, output = Utils.run(cmd, verbose=True, failExit=False, cwd=dir_name)
            if code != 0:
                success = False
        return success

    @staticmethod
    def runTest(success):
        count = len(Tests._tests)
        if count == 0:
            Log.error("Unit tests are missing :(")
        elif Utils.promptYesNo("Build is finished, do you want to run %d tests?" % (count)):
            Konstruct._runHook("preTests")

            success = Tests.run()

            if success:
                Log.success("All test passed \o/")
            else:
                Log.error("Unit tests failed :(")

            Konstruct._runHook("postTests", success)

        return success
# }}}

# {{{ ComandLine
from collections import OrderedDict
from argparse import ArgumentParser
import types
class CommandLine:
    optionParser = ArgumentParser()
    _options = OrderedDict()

    @staticmethod
    def parse():
        options = CommandLine.optionParser.parse_args()

        out = {}

        for name, command in CommandLine._options.items():
            for option in command:
                passedOption = getattr(options, name)
                callback = option["function"]
                if option["required"] and getattr(options, name) is None:
                    CommandLine.optionParser.error("You need to specify %s argument" % required)


                if passedOption is None and option["default"] is None:
                    if option["prompt"]:
                        while True:
                            tmp = Utils.prompt("%s : " % option["prompt"])
                            if not tmp:
                                print("Please specify a value")
                            else:
                                passedOption = tmp
                                break

                if callback not in out:
                    out[callback] = []

                out[callback].append(passedOption)
        for callback, args in out.items():
            callback(*args)

    @staticmethod
    def option(name, **kwargs):
        # Add the option now, so we can keep the order of options
        if name not in CommandLine._options:
            CommandLine._options[name] = []

        def decorator(f):
            default = None
            action = "store"
            t = str
            prompt = False
            required = False

            if "required" in kwargs:
                required = True

            if "prompt" in kwargs:
                prompt = kwargs["prompt"]
                del kwargs["prompt"]

            if "default" in kwargs:
                default = kwargs["default"]
                del kwargs["default"]

                if type(default) == bool:
                    t = None
                    if default is True:
                        action = "store_false"
                    else:
                        action = "store_true"
                elif type(default) == int:
                    t = int

            if "action" in kwargs:
                action = kwargs["action"]
                del kwargs["action"]

            if "type" in kwargs:
                t = kwargs["type"]
                del kwargs["type"]

            exists = (name in CommandLine._options and len(CommandLine._options[name]) > 0)

            CommandLine._options[name].append({
                "function": f,
                "prompt": prompt,
                "required": required,
                "default": default
            })

            if not exists:
                if t != None:
                    CommandLine.optionParser.add_argument(name, dest=name, default=default, action=action, type=t, **kwargs)
                else:
                    CommandLine.optionParser.add_argument(name, dest=name, default=default, action=action, **kwargs)

            return f

        return decorator

@CommandLine.option("--assume-yes", default=False)
def assumeYes(assumeYes):
    Utils.promptAssumeYes(assumeYes)

@CommandLine.option("--configuration", default="")
def configuration(config):
    if not config:
        return

    config = config.split(",")
    if len(config) > 0:
        Konstruct.setConfigs(config)

@CommandLine.option("--verbose", default=False)
def verbose(verbose):
    Variables.set("verbose", verbose)
    Log.loglevel = Log.LogLevel.ALL

@CommandLine.option("--ignore-build", default="")
def ignoreBuild(ignoreBuild):
    if not ignoreBuild:
        return

    for dep in ignoreBuild.split(","):
        if dep in AVAILABLE_DEPS["default"]:
            AVAILABLE_DEPS["default"][dep].ignoreBuild = True

@CommandLine.option("--force-download", default="")
@CommandLine.option("--force-build", default="")
@CommandLine.option("--force", default="")
def forceDownload(forceDownload, forceBuild, force):
    if forceDownload:
        forceDownload = forceDownload.split(",")
    else:
        forceDownload = []

    if forceBuild:
        forceBuild = forceBuild.split(",")
    else:
        forceBuild = []

    if force:
        force = force.split(",")
        forceDownload += force
        forceBuild += force

    for d in forceDownload + forceBuild:
        if d in forceDownload:
            Deps.forceDownload(d)
        if d in forceBuild:
            Deps.forceBuild(d)
# }}}

# {{{ Platform
import platform
import multiprocessing

class Platform:
    system = platform.system()
    cpuCount = multiprocessing.cpu_count()
    wordSize = 64 if sys.maxsize > 2**32 else 32

    @staticmethod
    def getEnviron(name, default=""):
        return os.environ.get(name, default)

    @staticmethod
    def setEnviron(*args):
        for env in args:
            tmp = env.split("=", 1)
            if tmp[0].endswith("+"):
                key = tmp[0][:-1]
                current = os.environ.get(key, "")
                if current:
                    os.environ[key] = current + os.pathsep + tmp[1]
                else:
                    os.environ[key] = tmp[1]
            else:
                os.environ[tmp[0]] = tmp[1]

# }}}

# {{{ ConfigCache
class ConfigCache:
    CONFIG_INSTANCE = {}
    def __init__(self, f):
        self.file = f;

        if self.file in ConfigCache.CONFIG_INSTANCE:
            self.configCache = ConfigCache.CONFIG_INSTANCE[self.file]
        else:
            Log.debug("Reading cache: " + self.file)
            self.configCache = ConfigCache._read(self.file)
            ConfigCache.CONFIG_INSTANCE[self.file] = self.configCache

    def set(self, key, value):
        self.configCache[key] = value
        self._updateCacheFile();

    def get(self, key):
        return self.configCache.get(key, None)

    def setConfig(self, key, entry):
        eHash = entry["hash"]
        eConfig = entry["config"]

        if key not in self.configCache:
            # entry does not exists in cache
            self.configCache[key] = {eHash: eConfig}
        else:
            if eHash not in self.configCache[key]:
                # Cache for the data is new (different config)

                # We can only have one cache entry per config per dep
                # find and remove duplicate
                for h in list(self.configCache[key].keys()):
                    cachedConf = self.configCache[key][h]
                    if h != eHash and cachedConf == eConfig:
                        del self.configCache[key][h]

                self.configCache[key][eHash] = eConfig
            else:
                # Entry already exists
                # Nothing to save
                pass

        self._updateCacheFile()

    def getConfig(self, key, data):
        newCacheHash = ConfigCache._generateHash(data)
        config = ConfigCache.getConfigStr()
        ret = {"new": True, "hash":  newCacheHash, "config": config}

        if key in self.configCache:
            if newCacheHash in self.configCache[key]:
                ret["new"] = False
                ret["config"] = self.configCache[key][newCacheHash]

        return ret


    def _updateCacheFile(self):
        ConfigCache._write(self.configCache, self.file)

    @staticmethod
    def _generateHash(data):
        import pickle
        import hashlib
        return hashlib.md5(pickle.dumps(data)).hexdigest()

    @staticmethod
    def _write(stamps, dst):
        import json
        open(dst, "w").write(json.dumps(stamps, indent=4))

    @staticmethod
    def _read(location):
        import json
        try:
            return json.loads(open(location, "r").read())
        except:
            return {}

    @staticmethod
    def getConfigStr():
        return "-".join(Konstruct.getConfigs())
# }}}

# {{{ Utils
class Utils:
    _promptAssumeYes = False

    class Chdir:
        def __init__(self, dir):
            self.cwd = os.getcwd()
            self.dir = dir

        def __enter__(self):
            os.chdir(self.dir)

        def __exit__(self, type, value, traceback):
            os.chdir(self.cwd)

    @staticmethod
    def findLinuxDistribution():
        import re
        # {{{ parseReleaseFile()
        def _parseReleaseFile(firstline):
            _lsb_release_version = re.compile(r'(.+)'
                                               ' release '
                                               '([\d.]+)'
                                               '[^(]*(?:\((.+)\))?')
            _release_version = re.compile(r'([^0-9]+)'
                                           '(?: release )?'
                                           '([\d.]+)'
                                           '[^(]*(?:\((.+)\))?')


            # Default to empty 'version' and 'id' strings.  Both defaults are used
            # when 'firstline' is empty.  'id' defaults to empty when an id can not
            # be deduced.
            version = ''
            id = ''

            # Parse the first line
            m = _lsb_release_version.match(firstline)
            if m is not None:
                # LSB format: "distro release x.x (codename)"
                return tuple(m.groups())

            # Pre-LSB format: "distro x.x (codename)"
            m = _release_version.match(firstline)
            if m is not None:
                return tuple(m.groups())

            # Unknown format... take the first two words
            l = firstline.strip().split()
            if l:
                version = l[0]
                if len(l) > 1:
                    id = l[1]
            return '', version, id
        # }}}
        try:
            etc = os.listdir("/etc")
        except OSError:
            # Probably not a Unix system
            return None

        etc.sort()

        _release_filename = re.compile(r'(\w+)[-_](release|version)')
        _supported_dists = (
            'suse', 'debian', 'ubuntu', 'fedora', 'redhat', 'centos',
            'mandrake', 'mandriva', 'rocks', 'slackware', 'yellowdog', 'gentoo',
            'unitedlinux', 'turbolinux', 'arch', 'mageia')


        for file in etc:
            m = _release_filename.match(file)
            if m is not None:
                _distname, dummy = m.groups()
                _distname = _distname.lower()
                if _distname in _supported_dists:
                    distname = _distname
                    break
        else:
            #return _dist_try_harder(distname, version, id)
            return None

        with open(os.path.join("/etc", file), 'r') as f:
            firstline = f.readline()
        _distname, _version, _id = _parseReleaseFile(firstline)

        if _distname and full_distribution_name:
            distname = _distname
        if _version:
            version = _version
        if _id:
            id = _id
        return distname


    @staticmethod
    def findExec(name):
        from distutils.spawn import find_executable
        return find_executable(name)

    @staticmethod
    def patch(directory, patchFile, pNum=1):
        if not os.path.exists(directory):
            Utils.exit("Directory %s does not exist. Not patching." % directory)

        if not os.path.exists(patchFile):
            Utils.exit("Patch file %s does not exist. Not patching." % patchFile)

        import subprocess

        pNum = "-p" + str(pNum);
        patch = open(patchFile)
        nullout = open(os.devnull, 'w')

        with Utils.Chdir(directory):
            # First check if the patch might have been already aplied
            applied = subprocess.call(["patch", pNum, "-N", "-R", "--dry-run", "--silent"], stdin=patch, stdout=nullout, stderr=subprocess.STDOUT)

            if applied == 0:
                Log.info("Already applied patch "+ patchFile + " in " + directory + ". Skipping.")
            else:
                Log.info("Applying patch " + patchFile)

                # Check if the patch will succeed
                patch.seek(0)
                patched = subprocess.call(["patch", pNum, "-N", "--dry-run", "--silent"], stdin=patch, stderr=subprocess.STDOUT)
                if patched == 0:
                    patch.seek(0)
                    success, output = Utils.run("patch " + pNum + " -N", stdin=patch)
                    if success != 0:
                        Utils.exit("Failed to patch")
                else:
                    Utils.exit("Failed to patch")

            patch.close()
            nullout.close()

    @staticmethod
    def symlink(src, dst):
        if os.path.lexists(dst):
            try:
                if Platform.system == 'Windows':
                    os.rmdir(dst)
                else: 
                    os.unlink(dst)
            except:
                Utils.exit("Can not unlink %s/%s. Manually rename or remove this file" % (os.getcwd(), dst))

        if Platform.system == "Windows":
            import win32file
            try:
                win32file.CreateSymbolicLink(dst, src, 1)
            except:
                Log.error("""Insufficicient rights to create symlinks.
You can try the following:
1) Run 'secpol.msc' as administrator,
   Select 'Local Policies > User Rights Assignment > Create symbolic links' and add your user. Click Apply to save your changes.
2) Press "Windows  R" and run 'GPUpdate /Force' to activate your changes""")
                Utils.exit()
        else:
            os.symlink(src, dst)

    @staticmethod
    def mkdir(path):
        import errno
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise

    @staticmethod
    def exit(reason = None, code=1):
        if reason:
            Log.echo(reason)
        sys.exit(code)

    @staticmethod
    def run(cmd, **kwargs):
        import subprocess

        Log.info("Executing " + cmd)

        dir_name = None
        if "cwd" in kwargs:
            dir_name = kwargs["cwd"]

        stdin = stdout = stderr = None
        if "stdin" in kwargs:
            stdin = kwargs["stdin"]

        failExit = True
        if "failExit" in kwargs:
            failExit = kwargs["failExit"]

        if "returnOutput" in kwargs:
            stdout = stderr = subprocess.PIPE

        child = subprocess.Popen(cmd, cwd=dir_name, shell=True, stdin=stdin, stdout=stdout, stderr=stderr, env=os.environ)

        output, error = child.communicate()
        code = child.returncode

        if Variables.get("verbose", False) or "verbose" in kwargs and kwargs["verbose"]:
            str = "Command result:\n\tCode: %d " % code
            if output:
                str += "\n\tOutput: '%s'" % output
            if error:
                str += "\n\tError: '%s'" % error
            if code != 0:
                Log.debug(str + "\n")
        elif output is not None:
            LOG_FILE.write(output)
            LOG_FILE.flush()

        if code != 0:
            if failExit:
                Utils.exit("Failed to run previous command")
        else:
            Log.success("Success")

        return code, output

    @staticmethod
    def prompt(string):
        # Python 2/3 compatibility
        try: input = raw_input
        except NameError: pass

        return input(string)


    @staticmethod
    def promptAssumeYes(assumeYes):
        Utils._promptAssumeYes = assumeYes

    @staticmethod
    def promptYesNo(string, default="yes"):
        valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}

        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        if Utils._promptAssumeYes:
            print(string + prompt)
            print("Yes (--assume-yes given)")
            return True

        while True:
            choice = Utils.prompt(string + prompt).lower()

            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                print("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")


    @staticmethod
    def extract(path, destination=None):
        import shutil

        if os.path.isdir(path):
            return

        extension = os.path.splitext(path)[1]
        if extension == ".zip":
            from zipfile import ZipFile
            zip = ZipFile(path)
            zip.extractall(destination)
            zip.close()
        elif extension in [".tar", ".gz", ".bz2", ".bzip2", ".tgz"]:
            import tarfile
            tar = tarfile.open(path)
            tar.extractall(destination)
            tar.close()
        else:
            # Single file downloaded, not an archive
            # Nothing to do
            Log.debug("Nothing to extract for " + path)
            return

        with Utils.Chdir(destination):
            # Detect if the archive have been extracted to a subdirectory of destination
            # if it's the case, move the content of the directory to the parent dir
            files = os.listdir(".")
            if len(files) == 1 and os.path.isdir(files[0]):
                for f in os.listdir(os.path.join(".", files[0])):
                    shutil.move(os.path.join(files[0], f), ".")
                os.rmdir(files[0])

    @staticmethod
    def download(location, downloadDir=None, destinationDir=None):
        import types

        if downloadDir is None:
            downloadDir = tempfile.gettempdir()

        isStr = False
        try:
            isStr = isinstance(location, basestring)
        except NameError:
            isStr = isinstance(location, str)

        if not isStr:
            return location.download(destinationDir)
        else:
            if location.startswith("http"):
                return Utils._httpDownload(location, downloadDir, destinationDir)
            else:
                Utils.exit("Protocol not supported for downloading " + location)

    @staticmethod
    def _httpDownload(url, downloadDir, destinationDir):
        import urllib2
        import tempfile

        file_name = url.split('/')[-1]
        extractDir = os.path.join(downloadDir, file_name)
        exists = os.path.exists(file_name)
        if exists:
            if Utils.promptYesNo("The downloadfile %s is already present, download a fresh version ?" % (file_name)):
                Log.debug("Removing %s" % (file_name))
                os.unlink(file_name)
                exists = False
        if not exists:
            u = urllib2.urlopen(url)
            f = open(extractDir, "wb")
            meta = u.info()
            #file_size = int(meta.getheaders("Content-Length")[0])

            file_size_dl = 0
            block_sz = 8192
            while True:
                buff = u.read(block_sz)
                if not buff:
                    break

                file_size_dl += len(buff)
                f.write(buff)
            f.close()
        if destinationDir:
            Log.info("Extracting %s" % (file_name))
            Utils.extract(os.path.join(downloadDir, file_name), destinationDir)
# }}}

# {{{ Logs
class Log:
    class LogLevel:
        ALL = 0
        DEBUG = 1
        INFO = 2
        WARN = 3
        ERROR = 4
        FATAL = 5
        OFF = 6
    loglevel = LogLevel.INFO
    @staticmethod
    def echo(string):
        print(string)

    @staticmethod
    def info(string):
        if Log.LogLevel.INFO >= Log.loglevel:
            Log.echo("[INFO  ] " + string)

    @staticmethod
    def debug(string):
        if Log.LogLevel.DEBUG >= Log.loglevel:
            Log.echo("[DEBUG ] " + string)

    @staticmethod
    def warn(string):
        if Log.LogLevel.WARN >= Log.loglevel:
            Log.echo("[WARN  ] " + string)

    @staticmethod
    def error(string):
        if Log.LogLevel.FATAL >= Log.loglevel:
           Log.echo("[ERROR ] " +string);

    @staticmethod
    def success(string):
        if Log.LogLevel.OFF >= Log.loglevel:
            Log.echo("[SUCCES] " + string)
# }}}

# {{{ Deps
# TODO : Cleanup symlink handling (build)
from collections import OrderedDict
AVAILABLE_DEPS = {"default":{}}
DEPS = OrderedDict()
class Dep:
    def __init__(self, name, fun):
        self.function = fun
        self.options = {}
        self.name = name

        self.needDownload = False
        self.needBuild = False
        self.ignoreBuild = False
        self.configChanged = False

        self.linkDir = None
        self.outputFiles = []
        self.extractDir = None
        self.outputsDir = None

        self.downloadConfig = None
        self.buildConfig = None
        self.cache = ConfigCache(os.path.join(ROOT, "third-party", "konstruct.cache"))

    def prepare(self):
        Log.debug("=> Preparing " + self.name)
        if self.function is not None:
            options = self.function()
            if options is not None:
                # merge decoration options with the options
                # returned by the decorated function
                self.options.update(options.items())

        # Check if we need to download the dep
        if "location" in self.options:
            cache = self.cache.getConfig(self.name + "-download", self.options["location"])
            self.downloadConfig = cache

            self.linkDir = {"src": os.path.join("." + cache["config"], self.name), "dest": self.name}
            self.extractDir = self.linkDir['src']
            exists = os.path.exists(self.extractDir)
            if cache["new"]:
                if exists and not self.cache.get("%s-download" % (self.name)):
                    # Downloaded dir exists but no cache at all exists for this dep.
                    # The third-party/konstruct.cache file has been removed/corrupted
                    # In such case we consider the dependency up to date, so 
                    # update the cache.
                    self.cache.setConfig(self.name + "-download", self.downloadConfig);
                    Log.info("No cache found for \"%s\" but the directory \"%s\" " % (self.name, self.extractDir) + 
                             "already exists. Not downloading again, use "+ 
                             "--force-download=%s to download again this dependency" % (self.name))
                else:
                    Log.debug("Need download because configuration for '%s/%s' is new" % (cache["config"], self.name))
                    self.needDownload = True
            elif not exists:
                Log.debug("Need download because output dir '%s' does not exists" % (self.extractDir))
                self.needDownload = True
            elif not os.path.islink(self.linkDir["dest"]):
                Log.debug("Need symlink because destination dir '%s' does not exists" % (self.linkDir["dest"]))
                Utils.symlink(self.linkDir["src"], self.linkDir["dest"])

        # Define some variables needed for building/symlinking
        cache = self.cache.getConfig(self.name + "-build", self.options)
        self.buildConfig = cache
        lastBuildConfig = self.cache.get(self.name + "-lastbuild-config")

        if lastBuildConfig != ConfigCache.getConfigStr():
            # The current configuration of konstructor is
            # different from the last build of this dep.

            if self.linkDir and not self.needDownload:
                # Dep has already been downloaded but the current config
                # is not the same as the previous one.
                # The directory of  the dep might not point to the correct
                # directory of the dep for the current config. Update it.
                Utils.symlink(self.linkDir["src"], self.linkDir["dest"])

            self.configChanged = True

        self.outputsDir = os.path.join(ROOT, OUTPUT, "third-party", "." + cache["config"])
        Utils.mkdir(self.outputsDir)

        if self.needDownload:
            self.needBuild = True
        elif not self.needBuild:
            if cache["new"]:
                Log.debug("Need build, because configuration for this dep is new")
                self.needBuild = True
            elif "outputs" in self.options:
                # If we don't have any configuration change, make sure that the outputs
                # exists and are more recent than the downloaded/extracted directory

                # Get the time of the directory
                srcDir = self._getDir();
                try:
                    dirTime = os.path.getmtime(os.path.realpath(srcDir))
                except:
                    self.needBuild = True
                    return

                for output in self.findOutputs():
                    if output["found"] is False:
                        Log.debug("Need build %s, because output file %s havn't been found" % (self.name, output["src"]))
                        self.needBuild = True
                        break
                    # This code have some issues
                    # - It does not detect change made in subdirectories
                    # - Changing configuration might trigger a rebuild
                    #   since the outputs could be older than the directory when depdency is rebuilt in another configuration
                    #
                    # Until a better alternative is found, do not check if output is more recent
                    """
                    else:
                        import datetime
                        try:
                            outFileTime = os.path.getmtime(os.path.join(self.outputsDir, output["file"]))
                        except:
                            # Symlink does not exist, it will be created back at link time
                            continue

                        if dirTime is None:
                            # Make sure dest file is more recent than src file
                            if outFileTime > os.path.getmtime(output["src"]):
                                Log.debug("Need build, because dep (%s) file %s is more recent than ouput file %s " % (self.name, output["src"], output["file"]))
                                self.needBuild = True
                        elif dirTime > outFileTime:
                            Log.debug("Need build, because dep (%s) is more recent than ouput file %s (%s / %s)" % (srcDir, output["file"],
                                datetime.datetime.fromtimestamp(dirTime).strftime('%Y-%m-%d %H:%M:%S'),
                                datetime.datetime.fromtimestamp(outFileTime).strftime('%Y-%m-%d %H:%M:%S'),
                            ))
                            self.needBuild = True
                            break
                    """
            if self.ignoreBuild:
                Log.debug("Build discarded because of --ignore-build flag")
                self.needBuild = False

    def download(self):
        import shutil
        if not self.needDownload:
            return

        # If the link dir is not a symlink, the user probably overriden the dep.
        # In such case, warn the user about the dep update, and ask for confirmation
        # before removing the directory.
        if self.linkDir and os.path.exists(self.linkDir["dest"]) and not os.path.islink(self.linkDir["dest"]):
            if Utils.promptYesNo("The dependency %s has been updated, download the updated version ? (the directory %s will be removed)" % (self.name, self.extractDir)):
                Log.debug("Removing %s" % (self.linkDir["dest"]))
                shutil.rmtree(self.linkDir["dest"])
                self.needDownload = True
            else:
                Log.info("Skipping update of %s" % self.name)
                return

        if os.path.isdir(self.extractDir):
            Log.debug("Removing previous version of %s in directory %s" % (self.name, self.extractDir))
            shutil.rmtree(self.extractDir)

        Log.info("Downloading %s" % (self.name))
        Utils.download(self.options["location"], downloadDir=".", destinationDir=self.extractDir)

        if self.linkDir:
            # Make the dep directory point to the directory matching the configuration
            Utils.symlink(self.linkDir["src"], self.linkDir["dest"])

        self.cache.setConfig(self.name + "-download", self.downloadConfig);

    def patch(self):
        if "patchs" not in self.options:
            return

        Log.debug("Patching " + self.name)
        for p in self.options["patchs"]:
            Utils.patch(self.name, p)

    def _getDir(self):
        newDir = "."
        if "location" in self.options:
            newDir = self.name
        if "chdir" in self.options:
            newDir = os.path.join(newDir, self.options["chdir"])

        return newDir

    def build(self):
        newDir = self._getDir()

        if not os.path.exists(newDir):
            Utils.mkdir(newDir)

        with Utils.Chdir(newDir):
            if self.needBuild and "build" in self.options:
                Log.info("Bulding " + self.name)
                for cmd in self.options["build"]:
                    if hasattr(cmd, '__call__'):
                        cmd()
                    else:
                        if cmd.startswith("make"):
                            if "-j" not in cmd:
                                cmd += " -j" + str(Platform.cpuCount)
                        elif cmd.startswith("xcodebuild"):
                            if "-jobs" not in cmd:
                                cmd += " -jobs " + str(Platform.cpuCount)
                        Utils.run(cmd)

                self.cache.set(self.name + "-lastbuild-config", ConfigCache.getConfigStr())

            self.symlinkOutput()

        self.cache.setConfig(self.name + "-build", self.buildConfig)

    def findOutputs(self):
        import re

        outputs = []

        if "outputs" not in self.options:
            return outputs

        depDir = os.path.join(Deps.path, self._getDir())
        with Utils.Chdir(depDir):
            for output in self.options["outputs"]:
                rename = None
                found = False
                copy = False

                # First, build the path of the file
                if type(output) == list:
                    rename = output[1]
                    outFile = output[0]
                elif type(output) == dict:
                    copy = True
                    outFile = output["src"]
                else:
                    outFile = output

                path, name = os.path.split(outFile)
                if path == "":
                    path = "."

                out = {
                    "copyOnly": False,
                    "found": False,
                    "src": os.path.join(depDir, path, name)
                }

                # Then, makes sure the directory exists
                try:
                    files = os.listdir(path)
                except:
                    outputs.append(out)
                    continue

                # And find which file in the directory match our output
                for f in files:
                    if re.match(name, f):
                        out["found"] = True
                        if rename:
                            out["file"] = re.sub(name, rename, f)
                        elif copy:
                            out["copyOnly"] = True
                            out["file"] = output["dst"]
                        else:
                            out["file"] = f

                        # Since the file name may be a regex,
                        # update the "src" with the real file name
                        out["src"] = os.path.join(depDir, path, f)
                        break

                outputs.append(out)

        return outputs

    def symlinkOutput(self):
        import shutil
        import re

        if "outputs" not in self.options:
            Log.debug("No need for outputs of " + self.name)
            return

        outputs = self.findOutputs()
        for output in outputs:
            if not output["found"]:
                Utils.exit("Output %s for %s not found" % (output["src"], self.name))

            destDir = os.path.join(Deps.getDir(), "..", OUTPUT, "third-party", "." + self.buildConfig["config"])
            destFile = os.path.join(destDir, output["file"])
            Utils.mkdir(destDir)

            if not self.needBuild and self.configChanged and not os.path.exists(destFile) and not self.ignoreBuild:
                # Config has been changed but the destination file does not exists
                # The dependency needs to be rebuilt otherwise we would copy the file
                # from a different configuration
                Log.info("Destination file %s for depedency %s " % (destFile, self.name) +
                    "has not been found.  The last build of the dependency was different " +
                    "from the current build config (%s). " % (" - ".join(Konstruct.getConfigs())) +
                    "The dependency will be rebuilt.")

                with Utils.Chdir(Deps.path):
                    self.needBuild = True
                    self.configChanged = False
                    self.build()

            if self.needBuild or not os.path.exists(destFile) :
                # New outputs have been generated
                # Copy them to the build dir
                Log.debug("Need output %s, copy to %s" % (output["src"], destFile))
                shutil.copy(output["src"], destFile)

            # Symlink the current config
            if not output["copyOnly"]:
                Log.debug("Need symlink src=%s dst=%s" % (destFile, os.path.join(self.outputsDir, "..", output["file"])))
                Utils.symlink(destFile, os.path.join(self.outputsDir, "..", output["file"]))

class Deps:
    path = os.path.abspath("third-party")
    deps = []

    class Konstruct:
        def __init__(self, name, location):
            self.location = location
            self.name = name

        def importDep(self):
            import imp
            Log.debug("Importing konstruct dependency " + self.name)

            path, file = os.path.split(self.location)
            if path == "":
                path = "./"
            # Since dependency can be nested in directories we need to chdir
            with Utils.Chdir(path):
                try:
                    imp.load_source(self.name, os.path.realpath(file))
                except Exception as e:
                    import traceback

                    Log.error("Failed to import konstruct dependency %s : %s" % (self.location, e))
                    traceback.print_exc()

                    Utils.exit()

    class Repo:
        def __init__(self, location, revision=None):
            self.location = location
            self.revision = str(revision)

    class SvnRepo(Repo):
        def download(self, destination):
            if not os.path.isdir(destination):
                Utils.run("svn checkout %s %s" % (self.location, destination))

            with Utils.Chdir(destination):
                if self.revision:
                    Utils.run("svn up -r" + self.revision)

    class Command:
        def __init__(self, cmd):
            self.cmd = cmd

        def download(self, destination):
            Utils.mkdir(destination)
            with Utils.Chdir(destination):
                Utils.run(self.cmd)

    class Gclient():
        _exec = "gclient"

        @staticmethod
        def setExec(path):
            Deps.Gclient._exec = os.path.abspath(path)
            os.environ["PATH"] += os.pathsep + os.path.dirname(path)

        def __init__(self, location, revision=None):
            self.location = location
            self.revision = revision

        def download(self, destination):
            Utils.run("%s config --name %s --unmanaged %s" % (Deps.Gclient._exec, destination, self.location))
            Utils.run("%s sync %s" % (Deps.Gclient._exec, "--revision=" + self.revision if self.revision else ""))


    class GitRepo:
        def __init__(self, location, revision=None, branch=None, tag=None):
            self.location = location
            self.revision = revision
            self.branch = branch
            self.tag = tag

        def download(self, destination):
            verbose = ' -q'
            if Variables.get("verbose", False) or Log.LogLevel.INFO < Log.loglevel:
                verbose = ''
            if not os.path.isdir(destination):
                Utils.run("git clone %s %s %s" % (verbose, self.location, destination))
            else:
                Utils.run("git fetch --all")

            with Utils.Chdir(destination):
                if self.tag:
                    Utils.run("git checkout tags/" + self.tag + verbose)
                elif self.revision:
                    Utils.run("git checkout " + self.revision + verbose)
                elif self.branch:
                    Utils.run("git checkout --track origin/" + self.branch + verbose)

    @staticmethod
    def _process():
        Utils.mkdir(Deps.path)
        Utils.mkdir(os.path.join(OUTPUT, "third-party"))

        for name in Deps.deps:
            """
            for config in Konstruct.getConfigs():
                if name in AVAILABLE_DEPS[config]:
                    DEPS[name] = AVAILABLE_DEPS[config][name]
                    break
            """


            if name in AVAILABLE_DEPS["default"]:
                DEPS[name] = AVAILABLE_DEPS["default"][name]
            else:
                Utils.exit("Dependency %s is not available" % name)

        """
        if name not in DEPS:
            if Konstruct.config("default") and name in AVAILABLE_DEPS["default"]:
                DEPS[name] = AVAILABLE_DEPS["default"][name]
            else:
                Utils.exit("Dependency %s is not available" % name)
        """

        with Utils.Chdir(Deps.path):
            for name, d in DEPS.items():
                d.prepare()
                d.download()

            for name, d in DEPS.items():
                d.patch()
                d.build()

    @staticmethod
    def register(name, **kwargs):
        def decorator(f):
            d = Dep(name, f)

            configuration = "default"

            if configuration not in AVAILABLE_DEPS:
                AVAILABLE_DEPS[configuration] = {}

            AVAILABLE_DEPS[configuration][name] = d
            """
            if "configuration" in kwargs:
                configuration = kwargs["configuration"]

                if type(configuration) == list:
                    for config in configuration:
                        if config not in AVAILABLE_DEPS:
                            AVAILABLE_DEPS[config] = {}

                        AVAILABLE_DEPS[config][name] = d
                else:
                    if configuration not in AVAILABLE_DEPS:
                        AVAILABLE_DEPS[configuration] = {}

                    AVAILABLE_DEPS[configuration][name] = d
            """

        return decorator

    @staticmethod
    def forceDownload(dep):
        if dep in AVAILABLE_DEPS["default"]:
            Log.debug("Forcing download for %s" % dep)
            AVAILABLE_DEPS["default"][dep].needDownload = True
        else:
            Log.warn("Can't force download for %s. Dependency not found" % d)

    @staticmethod
    def forceBuild(dep):
        if dep in AVAILABLE_DEPS["default"]:
            Log.debug("Forcing build for %s" % dep)
            AVAILABLE_DEPS["default"][dep].needBuild = True
        else:
            Log.warn("Can't force build for %s. Dependency not found" % d)

    @staticmethod
    def setDir(path):
        Deps.path = os.path.abspath(path);

    @staticmethod
    def getDir():
        return Deps.path

    @staticmethod
    def set(*args):
        offset = 0
        for dep in args:
            if isinstance(dep, Deps.Konstruct):
                dep.importDep()
            else:
                Deps.deps.insert(offset, dep)
                offset += 1
# }}}

# {{{ Builders
BUILD = []
class Build:
    @staticmethod
    def add(builder):
        BUILD.append(builder)

    @staticmethod
    def run():
        for b in BUILD:
            Log.debug("Building %s" % (b.path))
            b.run()

        # Right now, in case of failure, Konstructor always exit()
        return True

class Builder:
    class Gyp:
        _args = ""
        _config = None
        _defines = {}
        _exec = None

        @staticmethod
        def setArgs(args):
            Builder.Gyp._args = args;

        @staticmethod
        def set(key, value):
            Builder.Gyp._defines[key] = value

        @staticmethod
        def get(key, default_value):
            if key in Builder.Gyp._defines:
                return Builder.Gyp._defines[key]
            return default_value

        @staticmethod
        def setExec(path):
            Builder.Gyp._exec = path;

        @staticmethod
        def setConfiguration(config):
            Builder.Gyp._config = config;

        def __init__(self, path, defines={}):
            self.path = os.path.abspath(path)
            self.defines = defines

        def run(self, target=None, parallel=True):
            defines = ""
            for key, value in Builder.Gyp._defines.items() + self.defines.items():
                defines += " -D%s=%s" % (key, value)
            defines += " "
            gyp = "%s --generator-output=%s %s %s %s" % (Builder.Gyp._exec, "build", defines, Builder.Gyp._args, self.path)
            if Platform.system == "Windows":
                gyp += " -f msvs"
                if Platform.wordSize == 32:
                    gyp += " -G Platform=Win32" # it seems to be ignored by gyp
                    #gyp += " -dgeneral"
            code, output = Utils.run(gyp)
            cwd = os.getcwd()
            os.chdir(OUTPUT)
            runCmd = ""
            project = os.path.splitext(self.path)[0]
            if Platform.system == "Darwin":
                runCmd = "xcodebuild -project " + project + ".xcodeproj"
                if parallel:
                    runCmd += " -jobs " + str(Platform.cpuCount)
                if Builder.Gyp._config is not None:
                    runCmd += " -configuration " + Builder.Gyp._config
                if target is not None:
                    runCmd += " -target " + target
            elif Platform.system == "Linux":
                #runCmd = "CC=" + CLANG + " CXX=" + CLANGPP +" make " + target + " -j" + str(nbCpu)
                runCmd = "make "
                if target is not None:
                    runCmd += " " + target
                if Variables.get("verbose", False):
                    runCmd += " V=1"
                if Builder.Gyp._config is not None:
                    runCmd += " BUILDTYPE=" + Builder.Gyp._config
                if parallel:
                    runCmd += " -j%i" % Platform.cpuCount
            elif Platform.system == "Windows":
                runCmd = "MSBuild.exe /nologo /nodeReuse:True" #"/preprocess:all_in_one.txt"
                if target is not None:
                    runCmd += " /target:" + target
                if Variables.get("verbose", False):
                    runCmd += " /detailedsummary /verbosity:1"
                if Builder.Gyp._config is not None:
                    runCmd += " BUILDTYPE=" + Builder.Gyp._config
                if parallel:
                    runCmd += " /maxcpucount:%i" % Platform.cpuCount
                if True: #WTF? Platform.wordSize == 32:
                    runCmd += " /p:Platform=x64"
                runCmd += " %s.vcxproj" % (project) 
            else:
                Utils.exit("Missing support for %s platform" % (Platform.system));
            Log.debug("Running gyp. File=%s Target=%s" % (self.path, target));

            code, output = Utils.run(runCmd)

            if code != 0:
                Utils.exit("Failed to build project")

            os.chdir(cwd)

            return True
# }}}

# {{{ PackageManager
class PackageManger:
    COMMAND = None
    UPDATE_COMMAND = None
    UPDATE_DONE = False

    @staticmethod
    def install(name, prompt=True):
        cmd = "%s %s" % (PackageManger.COMMAND, name)
        if not prompt or (prompt and Utils.promptYesNo("Software \"%s\" is required, would you like to install it ? (%s %s)" % (name, PackageManger.COMMAND, name))):
            if not PackageManger.UPDATE_DONE and PackageManger.UPDATE_COMMAND:
                Log.info("Updating package manager (%s)" % (PackageManger.UPDATE_COMMAND))
                Utils.run(PackageManger.UPDATE_COMMAND)
                PackageManger.UPDATE_DONE = True

            code, output = Utils.run(cmd)

        return code == 0

    @staticmethod
    def detect():
        if Platform.system == "Darwin":
            if Utils.findExec("brew"):
                PackageManger.COMMAND = "brew install"
            elif Utils.promptYesNo("Homebrew (OSX package manager) hasn't been found. Would you like to install it ?"):
                code, output = Utils.run("/usr/bin/ruby -e \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\"")
                if code != 0:
                    Utils.exit("Failed to install Homebrew. Please install it manually from : http://brew.sh/")
                else:
                    PackageManger.COMMAND = "brew install"
            PackageManger.UPDATE_COMMAND = "brew update"
        elif Platform.system == "Linux":
            dist = Utils.findLinuxDistribution()
            isRoot = (os.geteuid() == 0)

            if dist == "debian" or dist == "ubuntu":
                PackageManger.UPDATE_COMMAND = "apt-get update"
                PackageManger.COMMAND = "apt-get install"
            elif dist == "arch":
                PackageManger.COMMAND = "pacman -S"

            if not isRoot and PackageManger.COMMAND is not None:
                PackageManger.COMMAND = "sudo %s" % PackageManger.COMMAND
                if PackageManger.UPDATE_COMMAND is not None:
                    PackageManger.UPDATE_COMMAND = "sudo %s" % PackageManger.UPDATE_COMMAND

        return PackageManger.COMMAND
# }}}
