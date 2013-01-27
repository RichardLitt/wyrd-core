#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

This module implements the Theme, Goal, Plan, and Task classes, as well as the
general State and Event.

"""

from functools import total_ordering


class Theme(object):
    """
    Theme is a very high-level concept, such as `fun', `career', or `family'.
    It has the capability to generate new goals. We might not want to use it in
    Wyrd In after all, but it might prove useful as a reference point e.g. for
    generating reports. If each goal is assigned to related themes, the user
    can have a report generated that states how much time he/she spent on
    different themes.

    """

    def __init__(self):
        raise NotImplementedError("Theme needs to be implemented yet.")


@total_ordering
class Goal(object):
    """
    Goal is a high-level concept, although less abstract than Theme. It is
    either a State, or an Event. Goals can be positive (desired) or negative
    (states/events to be avoided). This could be specified completely via the
    textual description of the goal, or it might be implemented on the code
    level. Goals are achieved by following (a sequence of) plans. There are
    usually multiple plans that can be chosen to achieve a goal. Goals can
    also involve subgoals, i.e. other objects of this class.

    """

    def __init__(self):
        raise NotImplementedError("Goal needs to be implemented yet.")

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return id(self)


@total_ordering
class Plan(object):
    """
    Plan is a recipe how to achieve a specified target state from a specified
    initial state. Plans are parameterised by various circumstances,
    predominantly by the assignment of roles to real people, but also
    instantiations of salient objects, and subordinate (so-called delta) plans.
    For instance, the plan to buy a new piece of furniture involves a suitable
    instance of a furniture shop and a subordinate plan to get to the shop and
    bring the piece of furniture back home somehow. It might also involve
    a driver if the person him-/herself is not able to drive the thing home. In
    this plan, the initial state specification would include the person having
    enough money, time, and space at home. The final state would be fulfilling
    the goal of having the piece of furniture at home in the simpler case of,
    say, a couch; in a more complex case of a kitchen, for example, it would be
    followed by another plan for building the furniture into the final shape,
    until the goal is reached.

    Plans are composed of tasks (as far as I can see).

    """

    def __init__(self):
        raise NotImplementedError("Plan needs to be implemented yet.")

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return id(self)


@total_ordering
class Task(object):
    """
    Task is an (potentially recurrent) event with an actor, generally one that
    is desired by the user. Every task has the actor specified, be it the local
    user or someone else, even a generic `someone'. Tasks generally also have
    deadlines and belong to a plan, even if the plan should consist of a single
    task. There are all other sorts of attributes of tasks, which are to be
    determined as the implementation proceeds.

    Tasks can have a complex recurrency structure. The implementation should
    account for tasks such as ``Take a pill P each Monday and Thursday after
    breakfast.'' or ``Buy and paint eggs two weeks before Easter except for
    leap years.''

    """
    slots = ('name', 'project', 'done', 'time', 'deadline')

    def __init__(self, name, project):
        self.name = name
        if project:
            self.project = project
        # Empty-string projects are treated as no project.
        else:
            self.project = None
        self.done = False

    def __eq__(self, other):
        return self.name == other.name and self.project == other.project

    def __lt__(self, other):
        return str(self) < str(other)

    def __hash__(self):
        return id(self)

    def __str__(self):
        return "{done} {name} ({proj})".format(
            name=self.name, proj=self.project,
            done=("DONE" if
                  ('done' in self.__dict__ and self.done)
                  else "    "))

    def __repr__(self):
        return "{done} {name} ({proj})".format(
            name=self.name, proj=self.project,
            done=("DONE" if self.done else "    "))


class State(object):
    """
    This class represents a state of the world in the broadest sense.
    """

    def __init__(self):
        raise NotImplementedError("State needs to be implemented yet.")


class Event(object):
    """
    This class represents a one-time event in the real world in the broadest
    sense.

    """

    def __init__(self):
        raise NotImplementedError("Event needs to be implemented yet.")
