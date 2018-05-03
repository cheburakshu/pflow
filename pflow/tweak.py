import re
import os
import shutil
import pathlib
import ast
import sys
import time
import importlib

# 
try:
    from pkg_resources import resource_filename
except:
    pass


class Tweak(object):
    def __init__(self, package_or_directory_name=None, filter_file_name=None):
        self.package_or_directory_name = package_or_directory_name
        self.file_name = filter_file_name

        self.decode_input()

        self.report_dir_name = 'report'
        self.backup_dir_name = 'backup'
        self.output_dir_name = 'output'
        self.log_dir_name = 'log'
        self.report_dir = None
        self.backup_dir = None
        self.log_dir = None
        self.resource_dir = None
        self.output_dir = None
        self.tweak_files = []
        self.cwd = None
        self.ok = False
        self.precheck_err = 0
        self.postcheck_err = 0

    def decode_input(self):
        try:
            # Check if input is a package
            module_spec = importlib.util.find_spec(self.package_or_directory_name)
            if not module_spec: # Not a package, passed a directory
                self.directory = self.package_or_directory_name
                assert os.path.exists(self.directory), "Directory {} does not exist.".format(self.directory)
                return
            
            path = module_spec.submodule_search_locations
            if path:
                self.directory = path[0]
                return
    
            path = module_spec.origin
            if path:
                self.directory = path
                return
        except:
            self.directory = self.package_or_directory_name
            assert os.path.exists(self.directory), "Directory {} does not exist.".format(self.directory)


    def do(self):
        self.set_roots()
        self.create_dirs()
        self.traverse_files()
        self.backup()
        self.pre_verify_syntax()
        self.tweak()
        self.verify_syntax()
        self.finalize()

    def finalize(self):
        if self.ok:
            for root, file in self.tweak_files:
                basename = self.trim_slash(root)
                self.print_status('Finalizing - {}'.format(os.path.normpath(root + '/' + file)))
                try:
                    shutil.copy(os.path.join(self.output_dir, basename, file), os.path.join(root, file))
                except shutil.SameFileError:
                    pass
            if self.precheck_err + self.postcheck_err == 0:
                self.print_status('Tweak Success!')
            else:
                self.print_status('Tweak Success! [Conditional => {} compiler error(s) in source code when started.]'.format(self.precheck_err))
            print()
        else:
            self.print_status('Tweak Failed!')
            print()

    def undo(self):
        self.set_roots()
        self.traverse_files()
        self.restore()

    def restore(self):
        for root, file in self.tweak_files:
            basename = self.trim_slash(root)
            self.print_status('Restoring - {}'.format(os.path.normpath(root + '/' + file)))
            try:
                shutil.copy(os.path.join(self.backup_dir, basename, file), os.path.join(root, file))
            except shutil.SameFileError:
                pass
        self.print_status('Restore Success!\n')



    def print_status(self, data, persist=False):
        print(' '*150 + '\r',end='')
        print(data, end='')
        if not persist:
            print('\r', end='')
        time.sleep(0.01)


    def verify_syntax(self):
        cnt_success= 0
        cnt_fail = 0
        for root, file in self.tweak_files:
            basename = self.trim_slash(root)
            with open(os.path.join(self.output_dir, basename, file), 'r') as f:
                try:
                    ast.parse(f.read())
                    cnt_success += 1
                except:
                    cnt_fail += 1
                    print('Post-check:  => ' + root + '/' + file + ' => ' + str(sys.exc_info()))
                self.postcheck_err = cnt_fail
                self.print_status('Post-check: Success - {}, Failed - {}, Processed - {}%, Total - {}'.format(cnt_success,
                                                                                                      cnt_fail,
                                                                                                      100 * (cnt_success + cnt_fail)//len(self.tweak_files),
                                                                                                      len(self.tweak_files)
                                                                                                      ))
        if cnt_fail == 0 or (self.precheck_err == self.postcheck_err):
            self.ok = True
        print()

    def pre_verify_syntax(self):
        cnt_success = 0
        cnt_fail = 0
        for root, file in self.tweak_files:
            basename = self.trim_slash(root)
            with open(os.path.join(self.backup_dir, basename, file), 'r') as f:
                try:
                    ast.parse(f.read())
                    cnt_success += 1
                except:
                    cnt_fail += 1
                    print('Pre-check :  => ' + root + '/' + file + ' => ' + str(sys.exc_info()))
                self.precheck_err = cnt_fail
                self.print_status('Pre-check : Success - {}, Failed - {}, Processed - {}%, Total - {}'.format(cnt_success,
                                                                                                      cnt_fail,
                                                                                                      100 * (cnt_success + cnt_fail)//len(self.tweak_files),
                                                                                                      len(self.tweak_files)
                                                                                                      ))
        print()


    def tweak(self):
        profile_line = 'probe.profile()\n'
        import_line = 'from pflow import probe\n'
        cnt_success = 0
        for root,file in self.tweak_files:
            cnt_success += 1
            basename = self.trim_slash(root)
            self.print_status('Tweaking file {}/{} - {}'.format(cnt_success, len(self.tweak_files), os.path.normpath(root + '/' + file)))
            if not os.path.exists(os.path.join(self.output_dir, basename)):
                try:
                    pathlib.Path(os.path.join(self.output_dir, basename)).mkdir(parents=True, exist_ok=True)
                except:
                    os.makedirs(os.path.join(self.output_dir,basename), exist_ok=True)

            with open(os.path.join(self.output_dir, basename, file), 'w') as b:
                with open(os.path.join(root, file), 'r') as f:
                    found_def = False
                    found_colon = False
                    window = False
                    def_start = 0
                    import_written = False
                    pattern_future = re.compile(r'(.*)__future__(.*)') # import __future__ or from __future__ should be the first line
                    pattern_comment = re.compile(r'(\s*#)')
                    pattern_def = re.compile(r'(^\s*)(def .*)|(^\s*)(async\s+def .*)')
                    pattern_colon = re.compile(r'\)\s*:')
                    pattern_any = re.compile(r'(\s*)(.*\n)') # All lines expected to end with a new line. If not indent_start will be set to zero
                    pattern_import = re.compile(r'^import(.*)')
                    pattern_from_import = re.compile(r'^from(.*)import(.*)')
                    import_found = False
                    import_written = False
                    for line in f:

                        has_future = pattern_future.search(line)
                        has_def = pattern_def.search(line)
                        has_comment = pattern_comment.search(line)
                        has_colon = pattern_colon.search(line)
                        has_import = pattern_import.search(line) # Expects an import before inserting its own.
                        has_from_import = pattern_from_import.search(line) # Expects an import before inserting its own.

                        if (has_import or has_from_import):
                            import_found = True

                        if not import_written and not has_future and not has_comment and import_found:
                            if import_line != line:
                                b.write(import_line)
                            import_written = True

                        if pattern_any.search(line):
                            indent_start = pattern_any.search(line).end(1)
                        else:
                            indent_start = 0

                        if window is True and indent_start > 0:
                            if not import_written:
                                new_import_line = ' ' * indent_start + import_line
                                if new_import_line != line:
                                    b.write(new_import_line)

                            new_line = ' ' * indent_start + profile_line
                            if new_line != line:
                                b.write(new_line)

                            window = False

                        if has_def:
                            found_def = True
                            def_start = has_def.start(2)
                            found_colon = False

                        if has_colon:
                            found_colon = True

                        if found_def and found_colon:
                            window = True
                            found_def = False
                            found_colon = False

                        b.write(line)

    def trim_slash(self, path):
        if path[:1] == '/' :
            return path[1:]
        else:
            return path

    def backup(self):
        cnt=0
        for root,file in self.tweak_files:
            cnt += 1
            basename = self.trim_slash(root)
            self.print_status('Creating backup {}/{} - {}'.format(cnt, len(self.tweak_files), os.path.normpath(root + '/' + file)))
            try:
                if not os.path.exists(os.path.join(self.backup_dir,basename)):

                    try:
                        pathlib.Path(os.path.join(self.backup_dir,basename)).mkdir(parents=True, exist_ok=True)
                    except:
                        os.makedirs(os.path.join(self.backup_dir,basename), exist_ok=True)

                shutil.copy(os.path.join(root,file), os.path.join(self.backup_dir,basename))
            except shutil.SameFileError:
                pass

    def traverse_files(self):
        for root, dirs, files in os.walk(self.resource_dir, topdown=True):
            for name in files:
                if self.file_name:
                    if self.file_name != name:
                        continue
                if name[-3:] != '.py':
                    continue
                self.print_status('Selecting file - {}'.format(os.path.normpath(root + '/' + name)))
                self.tweak_files.append((root, name))
                if self.file_name:
                    return
            #if not self.scan_subdir:
            #    break

    def set_roots(self):
        self.cwd = os.getcwd()
        self.report_dir = os.path.join(self.cwd, self.report_dir_name)
        self.log_dir = os.path.join(self.cwd, self.log_dir_name)
        self.backup_dir = os.path.join(self.cwd, self.backup_dir_name)
        self.output_dir = os.path.join(self.cwd, self.output_dir_name)
        self.resource_dir = os.path.normpath(self.directory)

    def create_dirs(self):
        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

        if not os.path.exists(self.backup_dir):
            os.mkdir(self.backup_dir)

        if not os.path.exists(self.report_dir):
            os.mkdir(self.report_dir)

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

    # TODO:
    def compare(self):
        pass

    # TODO:
    def write_report(self):
        pass

#Tweak(resource='.', resource_type='dir', scan_file_name='test.py').do()

#Tweak(resource = './hyper-h2', resource_type='dir', scan_subdir=True).do()

#Tweak(resource = './hyper-h2/h2', resource_type='dir', scan_file_name='connection.py', scan_subdir=True).do()

#Tweak(resource = './hyper-h2', resource_type='dir', scan_subdir=True).undo()
