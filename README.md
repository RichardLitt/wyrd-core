wyrd-core
=========

This version adds features of json internet data handler to backend. It's based on Python3.1 branch which is the core part of the program

## Installation

Nothing is needed to install the program, just pulling it from the repo.
However, it has a few prerequisites in order to run:

* python 3
* python modules:
	* pytz (http://pytz.sourceforge.net/)
	* lxml (http://lxml.de)
	* (argparse; this one should be part of the python distribution)
	* standard python json module library


## Files

<dl>
<dt>deadline.py</dt>
    <dd>
		Not used yet. This module should define the <tt>Deadline</tt> class.
    </dd>
<dt>grouping.py</dt>
    <dd>
		Defines groupings of SOEs (<tt>StateOrEvent</tt>s). They are used as
		prerequisites of tasks, and can be used to capture structure of more
		complex tasks or plans.
    </dd>
<dt>person.py</dt>
    <dd>
		Not used yet. This module will handle users' identities.
    </dd>
<dt>scheduler.py</dt>
    <dd>
		Not used yet. This module will take care of scheduling tasks into the
		time available.
    </dd>
<dt>task.py</dt>
    <dd>
		Defines <tt>State</tt>, <tt>Event</tt>, <tt>Task</tt>, and a few other
		concepts. Especially the <tt>Task</tt> class is used heavily in the
		program as of now.
		</dd>
<dt>util.py</dt>
    <dd>
		Utility functions.
    </dd>
<dt>worktime.py</dt>
    <dd>
		Implements classes related to time and work slots, namely
		<tt>Interval</tt> and <tt>WorkSlot</tt>.
    </dd>
<dt>wyrdin.py</dt>
    <dd>
		The main module of the program. Defines the user session using
		<tt>Session</tt> (the class) and <tt>session</tt> (a global variable),
		and handles parsing the command line.
    </dd>
<dt>backend/generic.py</dt>
    <dd>
		Defines <tt>DBObject</tt> as an object with a unique ID assigned. All
		serializable classes that hold user's data should extend
		<tt>DBObject</tt>.
    </dd>
<dt>backend/xml.py</dt>
    <dd>
		Handles writing user's data to XML files and reading the data back from
		those files.
    </dd>
<dt>frontend/cli.py</dt>
    <dd>
		Implements the command-line user interface.
    </dd>
<dt>nlp/parsers.py</dt>
    <dd>
		Provides methods for parsing objects used in the program from strings.
    </dd>
</dl>
