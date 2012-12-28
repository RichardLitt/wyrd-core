#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

"""
import argparse
import datetime
import os.path
import pytz

from nlp.parsers import parse_timedelta, parse_interval


# TODO Public fields and methods.
__all__ = []

# Constants
FTYPE_CSV = 0
FTYPE_PICKLE = 1
FTYPE_XML = 2

# Variables
session = None
DEBUG = False
# DEBUG = True


class ClArgs():
    """Class to hold command line attributes."""
    pass

_cl_args = ClArgs()


class Session(object):
    """
    Represents a user session, gathering such information as current
    configuration or the user's set of tasks.

    """
    def __init__(self):
        # Set the default configuration.
        self.config = {
            'PROJECTS_FNAME': 'projects.lst',
            'TASKS_FNAME_IN': 'tasks.xml',
            'TASKS_FTYPE_IN': FTYPE_XML,
            'TASKS_FNAME_OUT': 'tasks.xml',
            'TASKS_FTYPE_OUT': FTYPE_XML,
            'LOG_FNAME_IN': 'tasks.xml',
            'LOG_FTYPE_IN': FTYPE_XML,
            'LOG_FNAME_OUT': 'tasks.xml',
            'LOG_FTYPE_OUT': FTYPE_XML,
            'TIME_FORMAT_USER': '%d %b %Y %H:%M:%S %Z',
            'TIME_FORMAT_REPR': '%Y-%m-%d %H:%M:%S',
            'TIMEZONE': pytz.utc,
            'BACKUP_SUFFIX': '~',
        }
        # Initialise fields.
        self.projects = []
        # TODO Devise a more suitable data structure to keep tasks in
        # memory.
        self.tasks = []
        self.wslots = []
        self.groups = []
        # Auxiliary variables.
        self._xml_header_written = False

    def read_config(self, cl_args):
        """ Finds all relevant configuration files, reads them and acts
        accordingly.
        """
        # Find config files.
        # TODO Extend. Include more options where configuration files can be
        # put (some user-specific, some global ones, perhaps some
        # site-specific). Look also in the command line arguments (_cl_args).
        cfg_fname = "wyrdin.cfg"
        if os.path.exists(cfg_fname):
            with open(cfg_fname, encoding="UTF-8") as cfg_file:
                for line in cfg_file:
                    cfg_key, cfg_value = map(str.strip,
                                             line.strip().split('=', 2))
                    # TODO Extend. There can be more various actions to be done
                    # when a value is set in the config file.
                    if cfg_key == 'TIMEZONE':
                        self.config['TIMEZONE'] = pytz.timezone(cfg_value)
                        # TODO Catch UnknownTimeZoneError and raise
                        # a ConfigError.
                    else:
                        self.config[cfg_key] = cfg_value

    def read_projects(self, infname=None):
        """
        TODO: Write docstring.
        """
        if infname is None:
            infname = self.config['PROJECTS_FNAME']
        with open(infname) as infile:
            self.projects = sorted([proj.rstrip('\n') for proj in infile])

    def write_projects(self, outfname=None):
        """Writes the list of projects into a file.

        In the current implementation, simply writes out an alphabetically
        sorted list of all known projects to the file.

        """
        if DEBUG:
            print("Projects:")
            print("---------")
            for project in self.projects:
                pprint(project)
            print("")
        if outfname is None:
            outfname = self.config['PROJECTS_FNAME']
        with open(outfname, 'w') as outfile:
            for project in self.projects:
                outfile.write(project + '\n')

    def read_tasks(self, infname=None, inftype=None):
        """
        Reads in tasks from files listing the user's tasks. Which files these
        are, can be found in `self.config'.

        TODO: Update docstring.

        """
        if infname is None:
            infname = self.config['TASKS_FNAME_IN']
            inftype = self.config['TASKS_FTYPE_IN']
        # This is a primitive implementation for the backend as a CSV.
        if inftype == FTYPE_CSV:
            import csv
            # Read the tasks from the file to the memory.
            with open(infname, newline='') as infile:
                taskreader = csv.reader(infile)
                self.tasks = [task for task in taskreader]
        elif inftype == FTYPE_XML:
            from backend.xml import XmlBackend
            with open(infname, 'rb') as infile:
                self.tasks = XmlBackend.read_tasks(infile)
        elif inftype == FTYPE_PICKLE:
            import pickle
            if not os.path.exists(infname):
                open(infname, 'wb').close()
            with open(infname, 'rb') as infile:
                self.tasks = []
                while True:
                    try:
                        task = pickle.load(infile)
                        self.tasks.append(task)
                    except EOFError:
                        break
        else:
            raise NotImplementedError("Session.read_tasks() is not "
                                      "implemented for this type of files.")

    def write_tasks(self, outfname=None, outftype=None):
        """
        Writes out the current list of tasks and task groupings from memory to
        a file.

        TODO: Update docstring.

        """
        if DEBUG:
            print("Tasks:")
            print("------")
            for task in self.tasks:
                pprint(task)
            print("")
        if outfname is None:
            outfname = self.config['TASKS_FNAME_OUT']
            outftype = self.config['TASKS_FTYPE_OUT']
        if outftype == FTYPE_CSV:
            # FIXME: May have been broken when groups were added.
            import csv
            with open(outfname, newline='') as outfile:
                taskwriter = csv.writer(outfile)
                for task in self.tasks:
                    taskwriter.writerow(task)
                for group in self.groups:
                    groupwriter.writerow(group)
        elif outftype == FTYPE_XML:
            from backend.xml import XmlBackend
            mode = 'r+b' if self._xml_header_written else 'wb'
            with open(outfname, mode) as outfile:
                if self._xml_header_written:
                    # Skip before the last line (assumed to read
                    # "</wyrdinData>").
                    outfile.seek(-len(b'</wyrdinData>\n'), 2)
                else:
                    outfile.seek(0, 2)
                XmlBackend.write_tasks(self.tasks, self.groups,
                                       outfile=outfile,
                                       standalone=not self._xml_header_written)
                if self._xml_header_written:
                    outfile.write(b'</wyrdinData>\n')
                self._xml_header_written = True
        elif outftype == FTYPE_PICKLE:
            import pickle
            with open(outfname, 'wb') as outfile:
                for task in self.tasks:
                    pickle.dump(task, outfile)
                for group in self.groups:
                    pickle.dump(group, outfile)
        else:
            raise NotImplementedError("Session.write_tasks() is not "
                                      "implemented for this type of files.")

    def read_log(self, infname=None, inftype=None):
        """Reads the log of how time was spent."""
        # TODO: Think of when this really has to be done, and when only
        # a subset of the log needs to be read. In the latter case, allow for
        # doing so.
        if infname is None:
            infname = self.config['LOG_FNAME_IN']
            inftype = self.config['LOG_FTYPE_IN']
        if inftype == FTYPE_PICKLE:
            import pickle
            if not os.path.exists(infname):
                open(infname, 'wb').close()
            with open(infname, 'rb') as infile:
                self.wslots = []
                while True:
                    try:
                        worktime = pickle.load(infile)
                        self.wslots.append(worktime)
                    except EOFError:
                        break
        elif inftype == FTYPE_XML:
            from backend.xml import XmlBackend
            with open(infname, 'rb') as infile:
                self.wslots = XmlBackend.read_workslots(infile)
        else:
            raise NotImplementedError("Session.read_log() is not "
                                      "implemented for this type of files.")

    def write_log(self, outfname=None, outftype=None):
        """TODO: Update docstring."""
        if outfname is None:
            outfname = self.config['LOG_FNAME_OUT']
            outftype = self.config['LOG_FTYPE_OUT']
        if outftype == FTYPE_PICKLE:
            import pickle
            with open(outfname, 'wb') as outfile:
                for wtime in self.wslots:
                    pickle.dump(wtime, outfile)
        elif outftype == FTYPE_XML:
            from backend.xml import XmlBackend
            # XXX This assumes that `write_log' was called soon after
            # `write_tasks'.
            mode = 'r+b' if self._xml_header_written else 'wb'
            with open(outfname, mode) as outfile:
                if self._xml_header_written:
                    # Skip before the last line (assumed to read
                    # "</wyrdinData>").
                    outfile.seek(-len(b'</wyrdinData>\n'), 2)
                XmlBackend.write_workslots(self.wslots, outfile, not
                    self._xml_header_written)
                if self._xml_header_written:
                    outfile.write(b'</wyrdinData>\n')
                self._xml_header_written = True
        else:
            raise NotImplementedError("Session.write_log() is not "
                                      "implemented for this type of files.")

    def write_all(self, tasks_ftype=None, tasks_fname=None,
                  log_ftype=None, log_fname=None):
        """Writes out projects, tasks, task groupings, and working slots to
        files as dictated by configuration settings.

        """
        from shutil import copy2, move
        self.write_projects()
        if tasks_ftype is None:
            tasks_ftype = self.config['TASKS_FTYPE_OUT']
        if log_ftype is None:
            log_ftype = self.config['LOG_FTYPE_OUT']
        if tasks_fname is None:
            tasks_fname = self.config['TASKS_FNAME_OUT']
        if log_fname is None:
            log_fname = self.config['LOG_FNAME_OUT']
        # The only special case so far.
        if (tasks_ftype == FTYPE_XML and log_ftype == FTYPE_XML
                and tasks_fname == log_fname):
            from backend.xml import XmlBackend
            # TODO: Write a context manager (with xxx as yyy: zzz) for writing
            #       a file with a backup.
            # TODO: Do this at other places too.
            # TODO: Handle the case the target file does not exist currently.
            bak_fname = tasks_fname + self.config['BACKUP_SUFFIX']
            copy2(tasks_fname, bak_fname)
            try:
                with open(tasks_fname, 'wb') as outfile:
                    XmlBackend.write_all(self.tasks, self.groups, self.wslots,
                                         outfile)
            except Exception as e:
                move(bak_fname, tasks_fname)
                raise e
        else:
            # FIXME: The type of file is not looked at, unless the file name is
            # supplied too. Provide some default filename for the supported
            # file types.
            self.write_log(outftype=log_ftype, outfname=log_fname)
            self.write_tasks(outftype=tasks_ftype, outfname=tasks_fname)

    def find_open_slots(self):
        """Returns work slots that are currently open."""
        return [slot for slot in self.wslots if slot.end is None]

    def remove_project(self, project):
        tasks = filter(lambda task: task.project == project, self.tasks)
        for task in tasks:
            self.remove_task(task)
        self.projects.remove(project)

    def get_task(self, task_id):
        return filter(lambda task: task.id == task_id, self.tasks).__next__()

    def remove_task(self, task):
        slots = filter(lambda slot: slot.task == task, self.wslots)
        for slot in slots:
            self.remove_workslot(slot)
        self.tasks.remove(task)

    def remove_workslot(self, slot):
        self.wslots.remove(slot)


def _init_argparser(arger):
    """
    Initialises the argument parser.
    """
    # Create a pool of subcommands.
    subargers = arger.add_subparsers()
    # Subcommands:
    #-------------

    # help
    arger_help = subargers.add_parser('help', help="Prints out this message.")
    arger_help.set_defaults(func=print_help)

    # begin
    arger_begin = subargers.add_parser('begin',
                                       aliases=['b'],
                                       help="To start working on a task.")
    arger_begin.set_defaults(func=begin)
    arger_begin.add_argument('-a', '--adjust',
                             default=0,
                             metavar='TDELTA',
                             help="Adjust the beginning time by subtracting "
                                  "this much.",
                             type=parse_timedelta)

    # end
    arger_end = subargers.add_parser(
        'end',
        aliases=['e'],
        help="When you have finished/interrupted work on a task.")
    arger_end.set_defaults(func=end)
    arger_end.add_argument('-a', '--adjust',
                           default=0,
                           metavar='MIN',
                           help="Adjust the end time by subtracting this "
                                "much.",
                           type=parse_timedelta)
    arger_end.add_argument('-d', '--done',
                           action='store_true')

    # retro (renamed from fence)
    arger_retro = subargers.add_parser('retro',
                                       aliases=['r'],
                                       help="Retrospective recording of work.")
    arger_retro.add_argument('-d', '--done',
                             action='store_true')
    arger_retro.set_defaults(func=retro)

    # status (merged with state)
    arger_status = subargers.add_parser('status',
                                        aliases=['s', 'st', 'stat', 'slots',
                                                 'log'],
                                        help="Prints out the current status "\
                                             "info.")
    arger_status.set_defaults(func=status)
    parse_tz_interval = lambda intstr: parse_interval(
            intstr,
            tz=session.config['TIMEZONE'])
    arger_status.add_argument('-t', '--time',
                              type=parse_tz_interval,
                              action='append',
                              help="Filter work slots by time.")
    arger_status.add_argument('-a', '--all',
                              action='store_true',
                              help="Include also closed slots.")

    # projects (renamed from topics)
    arger_projects = subargers.add_parser('projects',
                                          aliases=['p', 'proj'],
                                          help="Show info about projects.")
    arger_projects.set_defaults(func=projects)
    arger_projects.add_argument('-a', '--add',
                                dest='subcmd',
                                action='store_const',
                                const='add',
                                help="Add a new project.")
    arger_projects.add_argument('-l', '--list',
                                dest='subcmd',
                                action='store_const',
                                const='list',
                                help="List defined projects.")
    arger_projects.add_argument('-r', '--remove',
                                dest='subcmd',
                                action='store_const',
                                const='remove',
                                help="Remove an existing project.")
    arger_projects.add_argument('-v', '--verbose', action='store_true',
                                help="Be verbose.")

    # tasks (instead of editing the tasks store directly)
    arger_tasks = subargers.add_parser('tasks',
                                       aliases=['t', 'tasks'],
                                       help="Show info about tasks.")
    arger_tasks.set_defaults(func=tasks)
    arger_tasks.add_argument('-a', '--add',
                             dest='subcmd',
                             action='store_const',
                             const='add',
                             help="Add a new task.")
    arger_tasks.add_argument('-m', '--modify',
                             dest='subcmd',
                             action='store_const',
                             const='modify',
                             help="Modify an existing task.")
    arger_tasks.add_argument('-r', '--remove',
                             dest='subcmd',
                             action='store_const',
                             const='remove',
                             help="Remove an existing task.")
    arger_tasks.add_argument('-l', '--list',
                             dest='subcmd',
                             action='store_const',
                             const='list',
                             help="List defined tasks.")
    arger_tasks.add_argument('-v', '--verbose', action='store_true',
                             help="Be verbose.")

    return arger


def _process_args(arger):
    """ Processes the command line arguments.
    """
    arger.parse_args(namespace=_cl_args)
    _cl_args.arger = arger


# Subcommand functions.
def print_help(args):
    args.arger.print_help()
    return 0


def begin(args):
    task = frontend.get_task()
    start = datetime.datetime.now(session.config['TIMEZONE']) + args.adjust
    # TODO Make the Session object take care for accounting related to adding
    # work slots, tasks etc.
    session.wslots.append(WorkSlot(task=task, start=start))
    if task not in session.tasks:
        session.tasks.append(task)
        if ('project' in task.__dict__
                and task.project
                and task.project not in session.projects):
            session.projects.append(task.project)
    return 0


def end(args):
    end = datetime.datetime.now(session.config['TIMEZONE']) + args.adjust
    open_slots = session.find_open_slots()
    if not open_slots:
        print("You have not told me you have been doing something. Use "
              "`begin' or `retro'.")
        return 1
    # If currently working on a single task (once at a time), assume it is that
    # one to be ended.
    if len(open_slots) == 1:
        task = open_slots[0].task
    # If more tasks are currently open, let the user specify which one is to be
    # ended.
    else:
        task = frontend.get_task(map(lambda slot: slot.task, open_slots))
    if args.done:
        task.done = True
    slots_affected = [slot for slot in open_slots if slot.task is task]
    for slot in slots_affected:
        slot.end = end
    print("{num} working slot{s} {have} been closed: {task!s}".format(
        num=len(slots_affected),
        s=("" if len(slots_affected) == 1 else "s"),
        have=("has" if len(slots_affected) == 1 else "have"),
        task=task))
    return 0


def retro(args):
    print("Recording a worktime in retrospect...")
    slot = frontend.get_workslot()
    if args.done:
        slot.task.done = True
    session.wslots.append(slot)


def status(args):
    # Transform selection criteria into test functions.
    if args.time:
        filter_time = lambda slot: \
            all(map(lambda invl: slot.intersects(invl), args.time))
    else:
        filter_time = lambda _: True
    if not args.all:
        filter_open = lambda slot: slot.iscurrent()
    else:
        filter_open = lambda _: True
    # Select work slots matching the selection criteria..
    slots = [slot for slot in session.wslots \
             if filter_time(slot) and filter_open(slot)]

    if not slots:
        # FIXME Update the message.
        print("You don't seem to be working now.")
    else:
        # FIXME Update the message, especially in case when called with --all.
        print("You have been working on the following tasks:")
        now = datetime.datetime.now(session.config['TIMEZONE'])
        task2slot = group_by(slots, "task", single_attr=True)
        for task in task2slot:
            task_slots = task2slot[task]
            # Expected case: only working once on the task in parallel:
            if len(task_slots) == 1:
                end = task_slots[0].end or now
                time_spent = format_timedelta(end - task_slots[0].start)
                try:
                    print("\t{time: >18}: {task}".format(task=task.name,
                                                         time=time_spent))
                except:
                    continue
            else:
                for slot in task_slots:
                    end = slot.end or now
                    time_spent = format_timedelta(end - slot.start)
                    print("M\t{time: >18}: {task}".format(task=task.name,
                                                          time=time_spent))
    return 0


def projects(args):

    # Define subcommand functions.
    def list():
        frontend.list_projects(args.verbose)

    def add():
        print("Adding a project...")
        print("Specify the project name: ")
        project = input("> ")
        while project in session.projects:
            print("Sorry, this project name is already used.  Try again: ")
            project = input("> ")
        session.projects.append(project)
        print("The project '{}' has been added successfully.".format(project))

    def remove():
        print("Removing a project...")
        project = frontend.get_project(False)
        # Remove the project.
        session.remove_project(project)
        print(("The project '{}' and all dependent tasks have been "
              "successfully removed.")\
              .format(project))

    try:
        # Call the subcommand function.
        locals()[args.subcmd]()
    except KeyError:
        raise NotImplementedError(
            'The subcommand `{sub!s}\' is not implemented.'\
            .format(sub=args.subcmd))
    return 0


def tasks(args):

    # Define subcommand functions.
    def list():
        frontend.list_tasks(args.verbose)

    def add():
        print("Adding a task...")
        task = frontend.get_task()
        session.tasks.append(task)
        print("The task '{}' has been added successfully."\
              .format(str(task).lstrip()))

    def modify():
        print("Modifying a task...")
        task = frontend.get_task(session.tasks)
        attr, val = frontend.modify_task(task)
        if attr in Task.slots:
            print("Setting {attr} to {val!s}...".format(attr=attr, val=val))
            task.__setattr__(attr, val)
            print("The task has been succesfully updated:\n  {task!s}"\
                  .format(task=task))

    def remove():
        print("Removing a task...")
        task = frontend.get_task(session.tasks)
        session.remove_task(task)
        print("The task '{}' has been removed successfully.".format(task))

    try:
        # Call the subcommand function.
        locals()[args.subcmd]()
    except KeyError:
        raise NotImplementedError(
            'The subcommand `{sub!s}\' is not implemented.'\
            .format(sub=args.subcmd))
    return 0


# The main program loop.
if __name__ == "__main__":
    if DEBUG:
        from pprint import pprint

    # Read arguments and configuration, initiate the user session.
    arger = argparse.ArgumentParser()
    _init_argparser(arger)
    _process_args(arger)
    session = Session()
    session.read_config(_cl_args)
    # A python gotcha -- the main module gets loaded twice, once as the main
    # module, and second time when imported by other modules. Therefore, any
    # globals that should be visible when imported have to be explicitly
    # assigned here. Solution inspired by
    # http://codebright.wordpress.com/2011/06/15/globals-and-__main__-a-python-gotcha/.
    import wyrdin
    wyrdin.session = session

    # Do imports that depend on an existing session.
    from task import Task
    from util import format_timedelta, group_by
    from worktime import WorkSlot

    # Read data.
    session.read_projects()
    session.read_tasks()
    session.read_log()

    from frontend.cli import Cli as frontend
    # Perform commands.
    # FIXME: As seen, it does not work in a loop yet.
    ret = _cl_args.func(_cl_args)
    if ret == 0:
        print("Done.")

    # Write data on exit.
    session.write_all()
