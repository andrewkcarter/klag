.. image:: https://img.shields.io/github/license/andrewkcarter/klag.svg?maxAge=2592000
  :target: https://github.com/andrewkcarter/klag/blob/master/LICENSE
.. image:: https://img.shields.io/pypi/dw/klag.svg?maxAge=2592000
  :target: https://pypi.python.org/pypi/klag

klag
====

A command line interface for inspecting Kafka consumer group offsets
which are stored on the brokers (Kafka 0.8.2+).

Features
--------

-  Discover and display all active or specific consumer groups and
   topics.
-  View offsets for partition start and end, consumer offsets, and the
   remaining messages.
-  Output in several formats (human, json, discrete json records for
   indexing/monitoring).
-  Built in polling at a specified interval.

Installation
------------

::

    pip install klag

or

::

    python setup.py install

Examples
--------

::

    usage: klag [-h] [-b LIST] [-g JSON] [--groups-file FILE] [-d] [-c] [-p]
                [-s N] [-o FILE] [-f FORMAT] [--log-level LEVEL] [--version]

    Kafka 0.8.2+ consumer monitoring.

    optional arguments:
      -h, --help            show this help message and exit
      -b LIST, --brokers LIST
                            Comma separated list of Kafka brokers
      -g JSON, --groups JSON
                            Consumer groups and list of topics for each group to
                            check (even if dead). JSON structured as
                            '{"<group_id>":["<topic>"]}'
      --groups-file FILE    JSON file containing consumer groups and list of
                            topics for each group to check (even if dead). JSON
                            structured as '{"<group_id>":["<topic>"]}'
      -d, --discover        Include all active consumer groups and topics in
                            output
      -c, --cache           Consumer groups that go dead (all consumers
                            disconnect) will continue to be checked. Used with
                            '-s'
      -p, --partitions      Include partition metrics in output
      -s N, --seconds N     Repeat check every N seconds
      -o FILE, --output-file FILE
                            Write output to a file
      -f FORMAT, --format FORMAT
                            Write output using the specified format structure
                            {default,json,json-pretty,json-discrete}
      --log-level LEVEL     Set the application logging level
      --version             show program's version number and exit

To see all consumer groups that are connected and their topics, just run
the ``klag`` command. It will attempt to connect to a Kafka broker at
``localhost:9092`` as a default.

::

    $ klag

If your broker is not local, specify the ``--brokers`` flag.

::

    $ klag -b <remote-broker>
    Group     Topic                                                        Remaining
    ================================================================================
    my-group                                                                [STABLE]
              topic-1                                                             21
              topic-2                                                             15

To see data about the consumption of individual topic partitions, add
the ``--partitions`` flag.

::

    $ klag -p
    Group     Topic     Partition       Earliest    Consumed      Latest   Remaining
    ================================================================================
    my-group                                                                [STABLE]
              topic-1                                                             21
                        0                  52152      460290      460298           8
                        1                  52538      460963      460968           5
                        2                  52291      460805      460813           8
              topic-2                                                             15
                        0                      0      187180      187182           2
                        1                      0      187979      187984           5
                        2                      0      187026      187034           8

To focus on specific consumer groups and topics, use the ``--groups``
parameter.

::

    $ klag -g '{"my-group":["topic-2"]}'
    Group     Topic                                                        Remaining
    ================================================================================
    my-group                                                                [STABLE]
              topic-2                                                             15

To output the information in a more machine readable format, use the
``--format`` parameter. This is ideal for producing records for a
monitoring system.

::

    $ klag -g '{"my-group":["topic-2"]}' -f json-discrete
    {"consumer_lag": 15, "group": "my-group", "topic": "topic-2", "state": "Stable"}

To run ``klag`` continuously you may specify the ``--seconds``
parameter, which will print the consumer data at the specified interval.
Running continuously in conjunction with the ``--discover`` flag will
add consumer groups when they connect, and remove them when they
disconnect. If you wish to keep monitoring the topics for consumer
groups that have disconnected, enable caching with the ``--cache`` flag.