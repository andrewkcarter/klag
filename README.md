# klag
A command line interface for inspecting Kafka consumer group offsets which are stored on the brokers (Kafka 0.8.2+).

## Features
- Discover and display all active or specific consumer groups and topics.
- View offsets for partition start and end, consumer offsets, and the remaining messages.
- Output in several formats (human, json, discrete json records for indexing/monitoring).
- Built in polling at a specified interval.

## Installation

```
python setup.py install
```

## Examples

```
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
```

To see all consumer groups that are connected and their topics, just run the `klag` command. It will attempt to connect to a Kafka broker at `localhost:9092` as a default. 
```
$ klag
```

If your broker is not local, specify the `-b` flag.
```
$ klag -b <remote-broker>
```

