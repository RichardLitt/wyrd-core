#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

"""
from collections import Mapping

from nlp.parsers import parse_timedelta, parse_datetime, get_parser
from task import Task
from worktime import WorkSlot
from wyrdin import session


# TODO: Inherit from IFrontend (to be implemented) once alternatives are
# programmed.
class Cli(object):
    """ Basic command-line user interface. """

    @staticmethod
    def get_task(selection=None, ask_details=True):
        """ Asks the user for a task from a given selection or a new one.

        Keyword arguments:
        session -- the user session object
        selection -- a selection of tasks to choose from (default: anything)
        ask_details -- whether to ask the user for details, such as deadline
                       and estimated time

        """
        # Check that the selection is satisfiable.
        if selection is not None and not selection:
            raise ValueError("Cannot ask for a task from an empty selection.")

        task = None
        print("What is the task? ")
        if selection is not None:
            restricted = True
        else:
            selection = session.tasks
            restricted = False

        str2task = dict()
        int2task = dict()
        for task_index, a_task in enumerate(selection):
            # FIXME Distinguish between different tasks with the same string
            # representation.
            task_str = str(a_task)
            str2task[task_str] = a_task
            int2task[str(task_index)] = a_task
        if restricted:
            Cli.choosefrom(int2task)

        shown_selection = False
        taskname = input("> ")
        while not taskname or taskname == "?":
            if restricted:
                Cli.choosefrom(int2task)
            else:
                if selection:
                    shown_selection = True
                    Cli.choosefrom(int2task,
                                   msg="You can choose from the existing "
                                       "tasks:")
                else:
                    print("There are currently no tasks defined.")
            taskname = input("> ")
        # Should the task be one of existing Task tasks,
        if restricted:
            # Find the Task task.
            while taskname not in str2task and taskname not in int2task:
                if not taskname or taskname == "?":
                    Cli.choosefrom(int2task)
                else:
                    print("Sorry, this task was not on the menu. Try again.")
                taskname = input("> ")
            if taskname in int2task:
                task = int2task[taskname]
            else:
                task = str2task[taskname]
        # If we are asking for a new task,
        else:
            if shown_selection:
                if taskname in int2task:
                    task = int2task[taskname]
                elif taskname in str2task:
                    task = str2task[taskname]
            if task is None:
                # Create a new task, asking for optional details.
                matching_tasks = None
                if selection:
                    matching_tasks = [task for task in selection
                                      if task.name == taskname]
                if matching_tasks:
                    if len(matching_tasks) > 1:
                        print("There are multiple tasks of that name.  "
                              "I am going to choose the first one.")
                        # FIXME Let the user choose.
                    task = matching_tasks[0]
                else:
                    project = Cli.get_project(
                        prompt="What project does it belong to?")
                    task = Task(taskname, project)
                    if ask_details:
                        print("Estimated time?")
                        time = input("> ").strip()
                        print("Deadline?")
                        deadline = input("> ").strip()
                        if time:
                            task.time = parse_timedelta(time)
                        if deadline:
                            task.deadline = parse_datetime(
                                deadline, tz=session.config['TIMEZONE'])
        return task

    @staticmethod
    def choosefrom(selection, msg="Choose from the following list:"):
        print(msg)
        # Find what indexing to use for the selection.
        numbered_map = None
        if isinstance(selection, Mapping):
            try:
                sorted_keys = sorted(selection, key=int)
            except ValueError:
                try:
                    sorted_keys = sorted(selection)
                except KeyError:
                    numbered_map = selection
        else:
            numbered_map = enumerate(selection)
        if numbered_map is None:
            numbered_map = ((key, selection[key]) for key in sorted_keys)
        # Print the selection.
        for index, item in numbered_map:
            print ("    {idx: >4} {item!s}".format(idx=index, item=item))
        print("")

    @staticmethod
    def get_project(accept_empty=True, prompt=None):
        """Solicits a project name from the user.

        Keyword arguments:
        session -- the user session object
        accept_empty -- whether to accept an empty (nonexistent) project
                        (default: True)
        prompt -- the string to display to the user as a prompt
                  (default: "Which project?")

        """
        # TODO: Here should be some form of tab-completion.
        if prompt is None:
            prompt = "Which project?"
        print(prompt)
        project = input("> ").strip()

        msg_choose_ex = "You can choose from the existing projects."
        msg_choose_emp = ("You can also use an empty string, meaning no "
                          "project.")
        while ((project or not accept_empty)
               and project not in session.projects):
            if project != "?":
                if not project and not accept_empty:
                    print("You have to select one of the defined projects.")
                else:
                    print("You have not told me about this project yet.")
                    wish = input("Do you wish to create it as a new project? "
                                 "([y]/n) ").strip()
                    if not wish.startswith('n'):
                        session.projects.append(project)
                        break
            Cli.choosefrom(session.projects,
                           msg=(msg_choose_ex +
                                (("\n" + msg_choose_emp) if accept_empty
                                 else "")))
            # Cli.list_projects(session)
            project = input("> ").strip()
            # Try to interpret the input as a project index into the selection
            # list.
            try:
                proj_idx = int(project)
                try:
                    return session.projects[proj_idx]
                except IndexError:
                    pass
            except ValueError:
                pass
            # If it wasn't a project index that the user supplied, take it as
            # a string (i.e., do nothing).
        return project

    @staticmethod
    def get_workslot():
        task = Cli.get_task(ask_details=False)
        start = Cli.get_datetime("What was the start time?")
        end = Cli.get_datetime("What was the end time?",
                               (lambda end: end >= start))
        return WorkSlot(task=task, start=start, end=end)

    @staticmethod
    def get_datetime(prompt, validate=None):
        print(prompt)
        in_dt = None
        while in_dt is None:
            in_str = input("> ").strip()
            try:
                in_dt = parse_datetime(in_str, tz=session.config['TIMEZONE'])
            except ValueError as error:
                print("Error: {err!s}".format(err=error))
        return in_dt

    @staticmethod
    def modify_task(task):
        print("What do you want to change?")
        attr = None
        while attr is None:
            for attr in filter(lambda slot: Task.slots[slot]['editable'],
                               Task.slots):
                try:
                    val = task.__getattribute__(attr)
                except AttributeError:
                    val = None
                print ("    {attr: >13}".format(attr=attr) +
                       ('  ("{val!s}")'.format(val=val)
                           if val is not None else ''))
            instr = input("> ").strip()
            if instr in Task.slots:
                attr = instr
                break
            else:
                matching = [slot for slot in Task.slots
                            if (slot.startswith(instr)
                                and Task.slots[slot]['editable'])]
                if len(matching) == 1:
                    attr = matching[0]
                else:
                    attr = None
                    print("Sorry, could not unambiguously set the attribute "
                          "to the value specified. Please, try again.")
        print("Enter the new value.")
        value = None
        attr_type = Task.slots[attr]['type']
        parser = get_parser(attr_type)
        try:
            orig_val = task.__getattribute__(attr)
        except AttributeError:
            orig_val = None
        while value is None:
            value = input("> ")
            # Check the type of the value.
            try:
                value = parser(value, orig_val=orig_val)
            except:
                value = None
        return attr, value

    @staticmethod
    def list_projects(verbose=False):
        # TODO Implement verbosity.
        print("List of current projects:")
        for project in sorted(session.projects):
            print("    {}".format(project))
        print("")

    @staticmethod
    def list_tasks(verbose=False):
        # TODO Say when the tasks were worked on.
        print("List of current tasks:")
        if verbose:
            # Remove name, id from slots.
            slots = [slot for slot in Task.slots if slot not in ('id', 'name')]
            for task in sorted(session.tasks):
                print("    {}".format(task.name))
                for attr in slots:
                    try:
                        val = task.__getattribute__(attr)
                    except AttributeError:
                        continue
                    print("      {attr: >13}: {val!s}"\
                          .format(attr=attr, val=val))
                print("")
        else:
            for task in sorted(session.tasks):
                print("    {}".format(task))
        print("")
