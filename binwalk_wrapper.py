#!c:\program files\python38\python.exe

import os
import sys
from threading import Thread

# If installed to a custom prefix directory, binwalk may not be in
# the default module search path(s). Try to resolve the prefix module
# path and make it the first entry in sys.path.
# Ensure that 'src/binwalk' becomes '.' instead of an empty string
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _module_path in [
    # from repo: src/scripts/ -> src/
    _parent_dir,
    # from build dir: build/scripts-3.4/ -> build/lib/
    os.path.join(_parent_dir, "lib"),
    # installed in non-default path: bin/ -> lib/python3.4/site-packages/
    os.path.join(_parent_dir, "lib",
                 "python%d.%d" % (sys.version_info[0], sys.version_info[1]),
                 "site-packages")
]:
    if os.path.exists(_module_path) and _module_path not in sys.path:
        sys.path = [_module_path] + sys.path

import binwalk
import binwalk.modules
from binwalk.core.compat import user_input

def display_status(m):
    # Display the current scan progress when the enter key is pressed.
    while True:
        try:
            user_input()
            percentage = ((float(m.status.completed) / float(m.status.total)) * 100)
            sys.stderr.write("Progress: %.2f%% (%d / %d)\n\n" % (percentage,
                                                                 m.status.completed,
                                                                 m.status.total))
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            pass

def usage(modules):
    sys.stderr.write(modules.help())
    sys.exit(1)

def main():
    modules = binwalk.Modules()

    # Start the display_status function as a daemon thread.
    t = Thread(target=display_status, args=(modules,))
    t.setDaemon(True)
    t.start()

    try:
        if len(sys.argv) == 1:
            usage(modules)
        # If no explicit module was enabled in the command line arguments,
        # run again with the default signature scan explicitly enabled.
        elif not modules.execute():
            # Make sure the Signature module is loaded before attempting 
            # an implicit signature scan; else, the error message received
            # by the end user is not very helpful.
            if hasattr(binwalk.modules, "Signature"):
                modules.execute(*sys.argv[1:], signature=True)
            else:
                sys.stderr.write("Error: Signature scans not supported; ")
                sys.stderr.write("make sure you have python-lzma installed and try again.\n")
                sys.exit(1)
    except binwalk.ModuleException as e:
        sys.exit(1)

if __name__ == '__main__':
    try:
        # Special options for profiling the code. For debug use only.
        if '--profile' in sys.argv:
            import cProfile
            sys.argv.pop(sys.argv.index('--profile'))
            cProfile.run('main()')
        else:
            main()
    except IOError:
        pass
    except KeyboardInterrupt:
        sys.stdout.write("\n")
