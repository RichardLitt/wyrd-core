#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is mostly PEP8-compliant. See
# http://www.python.org/dev/peps/pep-0008/.
# pylint: disable=E126
# pymode:lint_ignore=E126
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

"""
from lxml import etree
from datetime import datetime, timedelta
import pytz

from grouping import SoeGrouping, AndGroup, OrGroup, ListGroup
from task import Task
from wyrdin import session


# TODO: Inherit from IBackend (to be implemented).
class XmlBackend(object):
    parser = etree.XMLParser(remove_blank_text=True)

    @classmethod
    def _timedelta_repr(cls, td):
        # TODO: Be more human-friendly.
        return '{d} d, {s} s'.format(d=td.days, s=td.seconds)

    @classmethod
    def _timedelta_fromrepr(cls, td_repr):
        parts = td_repr.split()
        return timedelta(days=int(parts[0]), seconds=int(parts[2]))

    @classmethod
    def _create_task_e(cls, task):
        """Creates an XML element for an object of the type Task."""
        task_e = etree.Element("task",
                               id=str(task.id),
                               done=str(int(task.done)))
        if 'project' in task.__dict__ and task.project is not None:
            task_e.set('project', task.project)
        if 'time' in task.__dict__:
            task_e.set('time', cls._timedelta_repr(task.time))
        if 'deadline' in task.__dict__:
            task_e.set('deadline', datetime.strftime(
                task.deadline, session.config['TIME_FORMAT_REPR']))
            if task.deadline.tzinfo:
                task_e.set('deadline_tz', task.deadline.tzname())
        if 'prerequisites' in task.__dict__ and task.prerequisites:
            task_e.set('prerequisites',
                       ', '.join(map(lambda prereq: prereq.short_repr(),
                                     task.prerequisites)))
             # 'enables': {'type': list, 'editable': True},
        task_e.text = task.name
        return task_e

    @classmethod
    def _create_group_e(cls, group, seen=None):
        """Creates an XML element for an object of the type SoeGrouping.

        Keyword arguments:
            - group: the SoeGrouping object
            - seen: a set of group objects that have been seen during the
                    traversal (only for internal purposes)

        """
        if seen is None:
            seen = set()
        seen.add(group)

        group_e = etree.Element("group",
                                id=str(group.short_repr()),
                                type=type(group).name)
        for member in group.elems:
            if isinstance(member, Task):
                task_e = etree.SubElement(group_e, "task")
                task_e.set('id', str(member.id))
            else:
                assert isinstance(member, SoeGrouping)
                assert type(member) != SoeGrouping
                # If this group was seen previously, do not go into it again.
                # Else, add it to the set of seen groups and do recur.
                if member not in seen:
                    member_e = XmlBackend._create_group_e(member, seen=seen)
                    group_e.append(member_e)
                else:
                    member_e = etree.SubElement(group_e, "group")
                    member_e.set('id', str(member.short_repr()))
                    member_e.set('type', type(member).name)
        return group_e

    @classmethod
    def write_tasks(cls, tasks, groups, outfile, standalone=True):
        """
        DEPRECATED!!! In case standalone == False, puts <groups> below <tasks>.

        Writes out a list of tasks in the XML format to the open file
        `outfile'.

        Keyword arguments:
            - session: the global object for the user session
            - tasks: an iterable of objects of the type Task
            - groups: an iterable of objects of the type SoeGrouping
            - outfile: a file open for writing, to which the tasks should be
                       written
            - standalone: whether a complete XML content should be written to
                          the file, including the XML header

        """
        if standalone:
            top_e = wyrdin_e = etree.Element('wyrdinData')
            tasks_e = etree.SubElement(wyrdin_e, 'tasks')
        else:
            top_e = tasks_e = etree.Element('tasks')
        for task in tasks:
            tasks_e.append(cls._create_task_e(task))
        for group in groups:
            top_e.append(cls._create_group_e(group))
        outfile.write(etree.tostring(top_e,
                                     encoding='UTF-8',
                                     pretty_print=True,
                                     xml_declaration=standalone))

    @classmethod
    def read_tasks(cls, infile):
        tasks = []
        in_tasks = False
        in_groups = False
        for event, elem in etree.iterparse(infile, events=('start', 'end')):
            # Stop reading as soon as the </tasks> tag is encountered.
            if in_tasks:
                if elem.tag == "groups":
                    in_groups = not in_groups
                elif elem.tag == "tasks":
                    break
            # Check whether we have reached the <tasks> element yet.
            else:
                if elem.tag == "tasks" and event == "start":
                    in_tasks = True
                continue
            # Skip the subtree describing groupings.
            if in_groups:
                continue
            # Otherwise, parse each <task> element in accordance to the way it
            # was output.
            if elem.tag == "task" and event == "end":
                attrs = elem.attrib
                # XXX When project of a task becomes something more than just
                # a string, the code will probably break on the following line.
                if 'project' in attrs:
                    project = attrs['project']
                else:
                    project = ''
                task = Task(name=elem.text,
                            project=project,
                            id=int(attrs['id']))
                if 'done' in attrs:
                    task.done = bool(int(attrs['done']))
                if 'time' in attrs:
                    task.time = cls._timedelta_fromrepr(attrs['time'])
                if 'deadline' in attrs:
                    task.deadline = datetime.strptime(
                        attrs['deadline'],
                        session.config['TIME_FORMAT_REPR'])
                    if 'deadline_tz' in attrs:
                        task.deadline = task.deadline.replace(
                            tzinfo=pytz.timezone(attrs['deadline_tz']))
                tasks.append(task)
        return tasks

    _typestr2cls = {'and': AndGroup,
                    'or': OrGroup,
                    'list': ListGroup}

    # TODO: It might be advantageous to switch to parsing the XML once into
    # a tree and reading all from the tree afterwards...
    @classmethod
    def read_groups(cls, infile, tasks):
        """Reads SoeGroupings from an XML file.

        Keyword arguments:
            - tasks: a mapping of known task IDs to the corresponding task
                     objects
            - infile: an open XML file to read the groupings from

        """
        groups = []  # the list of groups to be returned
        groups_map = {}  # short_repr -> group
        groups_branch = []  # branch of nested groups currently open
        in_groups = False
        for event, elem in etree.iterparse(infile, events=('start', 'end')):
            # Stop reading as soon as the </groups> tag is encountered.
            if in_groups:
                if elem.tag == "groups":
                    break
            # Check whether we have reached the <groups> element yet.
            else:
                if elem.tag == "groups" and event == "start":
                    in_groups = True
                continue
            # Parse each <group> element according to the way it was
            # output.
            if elem.tag == "group":
                if event == "start":
                    # Open a new group.
                    grp_type = elem.get('type')
                    grp_repr = elem.get('id')
                    if grp_repr in groups_map:
                        cur_group = groups_map[grp_repr]
                    else:
                        cur_group = XmlBackend._typestr2cls[grp_type](
                            short_repr=grp_repr)
                        groups_map[grp_repr] = cur_group
                    # Put the group to its place.
                    if groups_branch:
                        groups_branch[-1].elems.append(cur_group)
                    groups_branch.append(cur_group)
                # If event == "end",
                else:
                    # Close the current group.
                    if len(groups_branch) == 1:
                        groups.append(groups_branch[0])
                    groups_branch.pop()
            else:
                assert elem.tag == "task"
                if event == "start":
                    task = tasks[int(elem.get('id'))]
                    groups_branch[-1].elems.append(task)
        return groups

    @classmethod
    def _create_slot_e(cls, slot):
        """Creates an XML element for an object of the type WorkSlot."""
        slot_e = etree.Element('workslot',
                               id=str(slot.id),
                               task=str(slot.task.id))
        if slot.start is not None:
            slot_e.set('start', datetime.strftime(
                slot.start, session.config['TIME_FORMAT_REPR']))
        if slot.end is not None:
            slot_e.set('end', datetime.strftime(
                slot.end, session.config['TIME_FORMAT_REPR']))
        return slot_e

    @classmethod
    def write_workslots(cls, slots, outfile, standalone=True):
        if standalone:
            top_e = wyrdin_e = etree.Element('wyrdinData')
            slots_e = etree.SubElement(wyrdin_e, 'workslots')
        else:
            top_e = slots_e = etree.Element('workslots')
        for slot in slots:
            slots_e.append(cls._create_slot_e(slot))
        outfile.write(etree.tostring(top_e,
                                     encoding='UTF-8',
                                     pretty_print=True,
                                     xml_declaration=standalone))

    @classmethod
    def read_workslots(cls, infile):
        from worktime import WorkSlot
        slots = []
        for _, elem in etree.iterparse(infile):
            # Stop reading as soon as the </workslots> tag is encountered.
            if elem.tag == "workslots":
                break
            # Otherwise, parse each <workslot> element in accordance to the way
            # it was output.
            elif elem.tag == "workslot":
                attrs = elem.attrib
                id_ = int(attrs['id'])
                task_id = int(attrs['task'])
                task = session.get_task(task_id)
                start = (datetime.strptime(
                            attrs['start'],
                            session.config['TIME_FORMAT_REPR'])
                         if 'start' in attrs else None)
                end = (datetime.strptime(
                            attrs['end'],
                            session.config['TIME_FORMAT_REPR'])
                       if 'end' in attrs else None)
                slot = WorkSlot(task=task, start=start, end=end, id=id_)
                slots.append(slot)
        return slots

    # XXX This name is not the best possible. `all' still does not include
    # projects, just tasks and work slots.
    @classmethod
    def write_all(cls, tasks, groups, slots, outfile):
        """Writes out a list of tasks and work slots in the XML format to the
        open file `outfile'.

        Keyword arguments:
            - session: the global object for the user session
            - tasks: an iterable of objects of the type Task
            - groups: an iterable of objects of the type SoeGrouping
            - slots: an iterable of objects of the type WorkSlot
            - outfile: a file open for writing, to which the tasks should be
                       written

        """
        wyrdin_e = etree.Element('wyrdinData')
        tasks_e = etree.SubElement(wyrdin_e, 'tasks')
        slots_e = etree.SubElement(wyrdin_e, 'workslots')
        for task in tasks:
            tasks_e.append(cls._create_task_e(task))
        groups_e = etree.SubElement(tasks_e, 'groups')
        for group in groups:
            groups_e.append(cls._create_group_e(group))
        for slot in slots:
            slots_e.append(cls._create_slot_e(slot))
        outfile.write(etree.tostring(wyrdin_e,
                                     encoding='UTF-8',
                                     pretty_print=True,
                                     xml_declaration=True))
