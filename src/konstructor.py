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
            Log.debug("No Tests defined")
            return False
        success = True
        for cmd in Tests._tests:
            dir_name = None
            if isinstance(cmd, tuple):
                dir_name = cmd[1]
                cmd = cmd[0]
            Log.debug("Running tests suite : %s" % (cmd))
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
    Variables.set("verbose", True)

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
        if d in AVAILABLE_DEPS["default"]:
            if d in forceDownload:
                Log.info("Forcing download for %s" % d)
                AVAILABLE_DEPS["default"][d].needDownload = True
            if d in forceBuild:
                Log.info("Forcing download for %s" % d)
                AVAILABLE_DEPS["default"][d].needBuild = True
        else:
            Log.warn("Can't force download or build for %s. Dependency not found" % d)
# }}}

# {{{ Platform
import platform
import multiprocessing

class Platform:
    system = platform.system()
    cpuCount = multiprocessing.cpu_count()
    wordSize = 64 if sys.maxsize > 2**32 else 32

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
            print(self.file)
            self.configCache = ConfigCache._read(self.file)
            ConfigCache.CONFIG_INSTANCE[self.file] = self.configCache

        if not self.configCache:
            self.configCache = {}

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
                # Hash exist in cache but for another configuration.
                # Simply return the matching config (since the hash it's the same)
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
            return None

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
                Log.info("    Already applied patch "+ patchFile + " in " + directory + ". Skipping.")
            else:
                Log.info("    Applying patch " + patchFile)

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
                os.unlink(dst)
            except:
                Utils.exit("Can not unlink %s/%s. Manually rename or remove this file" % (os.getcwd(), dst))

        if Platform.system == "Windows":
            # TODO : Not supported
            #import win32file
            #win32file.CreateSymbolicLink(fileSrc, fileTarget, 1)
            Logs.error("no windows support for symlink")
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
    def exit(reason = None):
        if reason:
            Log.echo(reason)
        sys.exit(1)

    @staticmethod
    def run(cmd, **kwargs):
        import subprocess

        Log.debug("Executing :" + cmd)

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

        child = subprocess.Popen(cmd, cwd=dir_name, shell=True, stdin=stdin, stdout=stdout, stderr=stderr)

        output, error = child.communicate()
        code = child.returncode

        if Variables.get("verbose", False) or "verbose" in kwargs and kwargs["verbose"]:
            str = "Command result:\n\tCode: %d " % code
            if output:
                str += "\n\tOutput: '%s'" % output
            if error:
                str += "\n\tError: '%s'" % error
            if code != 0:
                Log.info(str + "\n")
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
            Log.info("Nothing to extract for " + path)
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
        u = urllib2.urlopen(url)
        f = open(os.path.join(downloadDir, file_name), "wb")
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

        Log.echo("Destination %s" % (destinationDir))
        if destinationDir:
            Log.echo("Extracting %s" % (f.name))
            Utils.extract(os.path.join(downloadDir, f.name), destinationDir)
# }}}

# {{{ Logs
class Log:
    @staticmethod
    def echo(string):
        print(string)

    @staticmethod
    def info(string):
        Log.echo(string)

    @staticmethod
    def debug(string):
        Log.echo("[DEBUG] " + string)

    @staticmethod
    def warn(string):
        Log.echo(string)

    @staticmethod
    def success(string):
        Log.echo(string)

    @staticmethod
    def error(string):
        Log.echo(string);
# }}}

# {{{ Deps
# TODO : Cleanup symlink handling (build)
from collections import OrderedDict
AVAILABLE_DEPS = {"default":{}}
DEPS = OrderedDict()
class Dep:
    def __init__(self, name, fun, options={}):
        self.function = fun
        self.options = options
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
        Log.debug("Preparing " + self.name)
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

        if self.cache.get(self.name + "-lastbuild-config"):
            # The current configuration of konstructor is
            # different from the last build of this dep
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
        if not self.needDownload:
            return

        if os.path.isdir(self.extractDir):
            if Utils.promptYesNo("The dependency %s has been updated, download the updated version ? (the directory %s will be removed)" % (self.name, self.extractDir)):
                import shutil
                Log.info("Removing %s" % (self.extractDir))
                shutil.rmtree(self.extractDir)
            else:
                Log.info("Skipping update of %s" % self.name)
                return

        Log.info("Downloading %s" % self.name)
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
                        if cmd.startswith("makeSingle"):
                            cmd = "make -j1"
                        elif cmd.startswith("make"):
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

            if not self.needBuild and self.configChanged and not os.path.exists(destFile):
                # Config has been changed but the destination file does not exists
                # The dependency needs to be rebuilt otherwise we would copy the file
                # from a different configuration
                Log.info("Destination file %s for depedency %s " % (destFile, self.name) +
                    "has not been found.  The last build of the dependency was different " +
                    "from the current build config (%s). " % (" + ".join(Konstruct.getConfigs())) +
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
            if not os.path.isdir(destination):
                Utils.run("git clone %s %s" % (self.location, destination))
            else:
                Utils.run("git fetch --all")

            with Utils.Chdir(destination):
                if self.tag:
                    Utils.run("git checkout tags/" + self.tag)
                elif self.revision:
                    Utils.run("git checkout " + self.revision)
                elif self.branch:
                    Utils.run("git checkout --track origin/" + self.branch)

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
            d = Dep(name, f, kwargs)

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
        def setExec(path):
            Builder.Gyp._exec = path;

        @staticmethod
        def setConfiguration(config):
            Builder.Gyp._config = config;

        def __init__(self, path):
            self.path = os.path.abspath(path)

        def run(self, target=None, parallel=True):
            defines = ""
            for key, value in Builder.Gyp._defines.items():
                defines += " -D%s=%s" % (key, value)
            defines += " "

            code, output = Utils.run("%s --generator-output=%s %s %s %s" % (Builder.Gyp._exec, "build", defines, Builder.Gyp._args, self.path))
            cwd = os.getcwd()

            os.chdir(OUTPUT)

            runCmd = ""

            if Platform.system == "Darwin":
                project = os.path.splitext(self.path)[0]
                runCmd = "xcodebuild -project " + project + ".xcodeproj"
                if parallel:
                    runCmd += " -jobs " + str(Platform.cpuCount)
                if Builder.Gyp._config is not None:
                    runCmd += " -configuration " + Builder.Gyp._config
                if target is not None:
                    runCmd += " -target " + target

            elif Platform.system == "Linux":
                #runCmd = "CC=" + CLANG + " CXX=" + CLANGPP +" make " + target + " -j" + str(nbCpu)
                runCmd = "make"

                if target is not None:
                    runCmd += " " + target
                if Variables.get("verbose", False):
                    runCmd += " V=1"
                if Builder.Gyp._config is not None:
                    runCmd += " BUILDTYPE=" + Builder.Gyp._config
                if parallel:
                    runCmd += " -j%i" % Platform.cpuCount
            else:
                # TODO : Windows support
                Utils.exit("Missing windows support");
            Log.debug("Running gyp. File=%s Target=%s" % (self.path, target));

            code, output = Utils.run(runCmd)

            if code != 0:
                Utils.exit("Failed to build project")

            os.chdir(cwd)

            return True
# }}}

