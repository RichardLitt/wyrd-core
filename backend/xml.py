#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

"""
try:
  from lxml import etree
  print("running with lxml.etree")
except ImportError:
  try:
    # Python 2.5
    import xml.etree.cElementTree as etree
    print("running with cElementTree on Python 2.5+")
  except ImportError:
    try:
      # Python 2.5
      import xml.etree.ElementTree as etree
      print("running with ElementTree on Python 2.5+")
    except ImportError:
      try:
        # normal cElementTree install
        import cElementTree as etree
        print("running with cElementTree")
      except ImportError:
        try:
          # normal ElementTree install
          import elementtree.ElementTree as etree
          print("running with ElementTree")
        except ImportError:
          print("Failed to import ElementTree from any known place")

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
    def _read_time(cls, attrs, attr, default_tz=None):
        """Reads time data from XML element's attributes.

        Assumes `attrs' specify `attr'.

        Keyword arguments:
            attrs -- attributes of the XML element
            attr -- name of the attribute in question
            default_tz -- the default timezone object to use when none was
                          specified (optional)

        """
        dt = datetime.strptime(attrs[attr], session.config['TIME_FORMAT_REPR'])
        tz_attr = '{}_tz'.format(attr)
        if tz_attr in attrs:
            dt = dt.replace(tzinfo=pytz.timezone(attrs[tz_attr]))
        else:
            dt = dt.replace(tzinfo=default_tz or pytz.utc)
        return dt

    @classmethod
    def _write_time(cls, elem, dt, name, default_tz=None):
        """Records time data into XML element's attributes.

        Keyword arguments:
            elem -- the XML element to record the data for
            dt -- the datetime data to record
            name -- name for the XML attribute
            default_tz -- default timezone object if a default timezone is
                          defined

        """
        if dt is not None:
            elem.set(name,
                     datetime.strftime(dt, session.config['TIME_FORMAT_REPR']))
            # FIXME: If dt.tzinfo == default_tz, do nothing. (But default_tz
            # has to be handled yet.)
            if dt.tzinfo and (default_tz is None or dt.tzinfo != default_tz):
                elem.set('{}_tz'.format(name), dt.tzname())

    @classmethod
    def _create_task_e(cls, task, default_tz=None):
        """Creates an XML element for an object of the type Task."""
        task_e = etree.Element("task",
                               id=str(task.id),
                               done=str(int(task.done)))
        if hasattr(task, 'project') and task.project is not None:
            task_e.set('project', task.project)
        if hasattr(task, 'time'):
            task_e.set('time', cls._timedelta_repr(task.time))
        if hasattr(task, 'deadline'):
            cls._write_time(task_e, task.deadline, 'deadline',
                            default_tz=default_tz)
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

        group_e = etree.Element("group",
                                id=str(group.short_repr()),
                                type=type(group).__name__)
        for member in group.members:
            if isinstance(member, Task):
                task_e = etree.SubElement(group_e, "task")
                task_e.set('id', member.id)
            else:
                assert isinstance(member, SoeGrouping)
                assert type(member) != SoeGrouping
                member_e = etree.SubElement(group_e, "group")
                member_e.set(id=str(member.short_repr()))
                member_e.set(type=type(member).__name__)
                # If this group was seen previously, do not go into it again.
                # Else, add it to the set of seen groups and do recur.
                if member not in seen:
                    seen.add(member)
                    member_e = XmlBackend._create_group_e(member, seen=seen)
                    group_e.append(member_e)
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
        default_tz = pytz.utc
        for event, elem in etree.iterparse(infile, events=('start', 'end')):
            if event == 'start':
                if elem.tag == 'defaults':
                    in_defaults = True
            else:
                # Stop reading as soon as the </tasks> tag is encountered.
                if elem.tag == "tasks":
                    break
                elif elem.tag == 'defaults':
                    in_defaults = False
                # Otherwise, parse each <task> element in accordance to the way
                # it was output.
                elif elem.tag == "task":
                    attrs = elem.attrib
                    # XXX When project of a task becomes something more than
                    # just a string, the code will probably break on the
                    # following line.
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
                        task.deadline = cls._read_time(attrs, 'deadline',
                                                       default_tz=default_tz)
                    tasks.append(task)
                elif elem.tag == 'timezone' and in_defaults:
                    default_tz = pytz.timezone(elem.text)
        return tasks

    _typestr2cls = {'and': AndGroup,
                    'or': OrGroup,
                    'list': ListGroup}

    # TODO: It might be advantageous to switch to parsing the XML once into
    # a tree and reading all from the tree afterwards...
    @classmethod
    def read_groups(cls, tasks, infile):
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
                else:
                    continue
            # Parse each <group> element in accordance to the way it was
            # output.
            if elem.tag == "group":
                if event == "start":
                    # Open a new group.
                    grp_type = elem.get('type')
                    cur_group = XmlBackend._typestr2cls(grp_type)()
                    # Remember the group by its short_repr.
                    cur_repr = cur_group.short_repr()
                    if cur_repr in groups_map:
                        cur_group = groups_map[cur_repr]
                    else:
                        groups_map[cur_repr] = cur_group
                    # Put the group to its place.
                    if groups_branch:
                        groups_branch[-1].elems.append(cur_group)
                    groups_branch.append(cur_group)
                # If event == "end",
                else:
                    # Close the current group.
                    if len(groups_branch) == 1:
                        groups.append(groups_branch[0])
            else:
                assert elem.tag == "task"
                if event == "start":
                    task = tasks[elem.get('id')]
                    groups_branch[-1].append(task)
        return groups

    @classmethod
    def _create_slot_e(cls, slot, default_tz=None):
        """Creates an XML element for an object of the type WorkSlot."""
        slot_e = etree.Element('workslot',
                               id=str(slot.id),
                               task=str(slot.task.id))
        cls._write_time(slot_e, slot.start, 'start', default_tz=default_tz)
        cls._write_time(slot_e, slot.end, 'end', default_tz=default_tz)
        return slot_e

    @classmethod
    def write_workslots(cls, slots, outfile, standalone=True):
        try:
            default_tz = session.config['TIMEZONE']
        except KeyError:
            default_tz = None
        if standalone:
            top_e = wyrdin_e = etree.Element('wyrdinData')
            if default_tz is not None:
                defaults_e = etree.SubElement(top_e, 'defaults')
                etree.SubElement(defaults_e, 'timezone').text = str(default_tz)
            slots_e = etree.SubElement(wyrdin_e, 'workslots')
        else:
            top_e = slots_e = etree.Element('workslots')
        for slot in slots:
            slots_e.append(cls._create_slot_e(slot, default_tz))
        outfile.write(etree.tostring(top_e,
                                     encoding='UTF-8',
                                     pretty_print=True,
                                     xml_declaration=standalone))

    @classmethod
    def read_workslots(cls, infile):
        from worktime import WorkSlot
        default_tz = None
        slots = []
        in_defaults = False
        for event, elem in etree.iterparse(infile, events=('start', 'end')):
            if event == 'start':
                if elem.tag == 'defaults':
                    in_defaults = True
            else:
                # Stop reading as soon as the </workslots> tag is encountered.
                if elem.tag == "workslots":
                    break
                elif elem.tag == 'defaults':
                    in_defaults = False
                # Otherwise, parse each <workslot> element in accordance to the
                # way it was output.
                elif elem.tag == "workslot":
                    attrs = elem.attrib
                    id_ = int(attrs['id'])
                    task_id = int(attrs['task'])
                    task = session.get_task(task_id)
                    if 'start' in attrs:
                        start = cls._read_time(attrs, 'start',
                                               default_tz=default_tz)
                    else:
                        start = None
                    if 'end' in attrs:
                        end = cls._read_time(attrs, 'end',
                                             default_tz=default_tz)
                    else:
                        end = None
                    slot = WorkSlot(task=task, start=start, end=end, id=id_)
                    slots.append(slot)
                elif elem.tag == 'timezone' and in_defaults:
                    default_tz = pytz.timezone(elem.text)
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
        try:
            default_tz = session.config['TIMEZONE']
        except KeyError:
            default_tz = None
        wyrdin_e = etree.Element('wyrdinData')
        if default_tz is not None:
            defaults_e = etree.SubElement(wyrdin_e, 'defaults')
            etree.SubElement(defaults_e, 'timezone').text = str(default_tz)
        tasks_e = etree.SubElement(wyrdin_e, 'tasks')
        slots_e = etree.SubElement(wyrdin_e, 'workslots')
        for task in tasks:
            tasks_e.append(cls._create_task_e(task, default_tz=default_tz))
        for group in groups:
            tasks_e.append(cls._create_group_e(group))
        for slot in slots:
            slots_e.append(cls._create_slot_e(slot, default_tz))
        outfile.write(etree.tostring(wyrdin_e,
                                     encoding='UTF-8',
                                     pretty_print=True,
                                     xml_declaration=True))
