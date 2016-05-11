import itertools
import copy

from kafka.client_async import KafkaClient
from kafka.protocol.admin import ListGroupsRequest, DescribeGroupsRequest, \
    ListGroupsResponse, DescribeGroupsResponse

try: # kafka-python 1.1.1
    from kafka.protocol.commit import OffsetFetchRequest, GroupCoordinatorRequest, \
        GroupCoordinatorResponse, OffsetFetchResponse
except ImportError:
    from kafka.protocol.commit import OffsetFetchRequest_v1 as OffsetFetchRequest, GroupCoordinatorRequest, \
        GroupCoordinatorResponse, OffsetFetchResponse as OffsetFetchResponse

from kafka.protocol.group import MemberAssignment
from kafka.protocol.offset import OffsetRequest, OffsetResponse

# For compatibility between kafka-python 1.0.2 and 1.1.1
if isinstance(ListGroupsRequest, list):
    _ListGroupsRequest = ListGroupsRequest[0]
    _ListGroupsResponse = ListGroupsResponse[0]
else:
    _ListGroupsRequest = ListGroupsRequest
    _ListGroupsResponse = ListGroupsResponse

if isinstance(OffsetRequest, list):
    _OffsetRequest = OffsetRequest[0]
    _OffsetResponse = OffsetResponse[0]
else:
    _OffsetRequest = OffsetRequest
    _OffsetResponse = OffsetResponse

if isinstance(OffsetFetchRequest, list):
    _OffsetFetchRequest = OffsetFetchRequest[1]
    _OffsetFetchResponse = OffsetFetchResponse[1]
else:
    _OffsetFetchRequest = OffsetFetchRequest
    _OffsetFetchResponse = OffsetFetchResponse

if isinstance(GroupCoordinatorRequest, list):
    _GroupCoordinatorRequest = GroupCoordinatorRequest[0]
    _GroupCoordinatorResponse = GroupCoordinatorResponse[0]
else:
    _GroupCoordinatorRequest = GroupCoordinatorRequest
    _GroupCoordinatorResponse = GroupCoordinatorResponse

if isinstance(DescribeGroupsRequest, list):
    _DescribeGroupsRequest = DescribeGroupsRequest[0]
    _DescribeGroupsResponse = DescribeGroupsResponse[0]
else:
    _DescribeGroupsRequest = DescribeGroupsRequest
    _DescribeGroupsResponse = DescribeGroupsResponse

class KafkaConsumerLag:

    def __init__(self, bootstrap_servers):

        self.client = KafkaClient(bootstrap_servers=bootstrap_servers)
        self.client.check_version()

    def _send(self, broker_id, request, response_type=None):

        f = self.client.send(broker_id, request)
        response = self.client.poll(future=f)

        if response_type:
            if response and len(response) > 0:
                for r in response:
                    if isinstance(r, response_type):
                        return r
        else:
            if response and len(response) > 0:
                return response[0]

        return None

    def check(self, group_topics=None, discovery=None):
        """
        {
            "<group>": {
                "state": <str>,
                "topics": {
                    "<topic>": {
                        "consumer_lag": <int>,
                        "partitions": {
                            "<partition>": {
                                "offset_first": <int>,
                                "offset_consumed": <int>,
                                "offset_last": <int>,
                                "lag": <int>
                            }
                        }
                    }
                }
            }
        }
        :param persist_groups:
        :return: consumer statistics
        """
        cluster = self.client.cluster
        brokers = cluster.brokers()

        # Consumer group ID -> list(topics)
        if group_topics is None:
            group_topics = {}

            if discovery is None:
                discovery = True
        else:
            group_topics = copy.deepcopy(group_topics)

        # Set of consumer group IDs
        consumer_groups = set(group_topics.iterkeys())

        # Set of all known topics
        topics = set(itertools.chain(*group_topics.itervalues()))

        # Consumer group ID -> coordinating broker
        consumer_coordinator = {}

        # Coordinating broker - > list(consumer group IDs)
        coordinator_consumers = {}

        results = {}

        for consumer_group in group_topics.iterkeys():
            results[consumer_group] = {'state': None, 'topics': {}}

        # Ensure connections to all brokers
        for broker in brokers:
            while not self.client.is_ready(broker.nodeId):
                self.client.ready(broker.nodeId)

        # Collect all active consumer groups
        if discovery:
            for broker in brokers:
                response = self._send(broker.nodeId, _ListGroupsRequest(), _ListGroupsResponse)

                if response:
                    for group in response.groups:
                        consumer_groups.add(group[0])

        # Identify which broker is coordinating each consumer group
        for group in consumer_groups:

            response = self._send(next(iter(brokers)).nodeId, _GroupCoordinatorRequest(group), _GroupCoordinatorResponse)

            if response:
                consumer_coordinator[group] = response.coordinator_id

                if response.coordinator_id not in coordinator_consumers:
                    coordinator_consumers[response.coordinator_id] = []

                coordinator_consumers[response.coordinator_id].append(group)

        # Populate consumer groups into dict
        for group in consumer_groups:
            if group not in group_topics:
                group_topics[group] = []

        # Add groups to results dict
        for group, topic_list in group_topics.iteritems():
            results[group] = {'state': None, 'topics': {}}

        # Identify group information and topics read by each consumer group
        for coordinator, consumers in coordinator_consumers.iteritems():

            response = self._send(coordinator, _DescribeGroupsRequest(consumers), _DescribeGroupsResponse)

            for group in response.groups:

                if group[1] in results:
                    results[group[1]]['state'] = group[2]
                    # TODO Also include member data?

                if discovery:
                    members = group[5]
                    for member in members:
                        try:
                            assignment = MemberAssignment.decode(member[4])
                            if assignment:
                                for partition in assignment.partition_assignment:
                                    topic = partition[0]

                                    # Add topic to topic set
                                    topics.add(topic)

                                    # Add topic to group
                                    group_topics[group[1]].append(topic)
                        except:
                            pass

        # Add topics to groups in results dict
        for group, topic_list in group_topics.iteritems():
            for topic in topic_list:
                results[group]['topics'][topic] = {'consumer_lag': 0, 'partitions': {}}

        # For storing the latest offset for all partitions of all topics
        # topic -> partition -> offset
        start_offsets = {}
        end_offsets = {}

        # Identify all the topic partitions that each broker is leader for
        # and request next new offset for each partition
        for broker, partitions in cluster._broker_partitions.iteritems():

            # topic -> List(partition, time, max_offsets)
            request_partitions = {}

            for tp in partitions:
                if tp.topic in topics:
                    if tp.topic not in request_partitions:
                        request_partitions[tp.topic] = []

                    # Time value '-2' is to get the offset for first available message
                    request_partitions[tp.topic].append((tp.partition, -2, 1))

            # List(topic, List(partition, time, max_offsets))
            topic_partitions = []

            for tp in request_partitions.iteritems():
                topic_partitions.append(tp)

            # Request partition start offsets
            response = self._send(broker, _OffsetRequest(-1, topic_partitions), _OffsetResponse)

            if response:
                for offset in response.topics:
                    topic = offset[0]
                    if topic not in start_offsets:
                        start_offsets[topic] = {}

                    for p in offset[1]:
                        start_offsets[topic][p[0]] = p[2][0]

            for tp in topic_partitions:
                for i, ptm in enumerate(tp[1]):
                    # Time value '-1' is to get the offset for next new message
                    tp[1][i] = (ptm[0], -1, 1)

            # Request partition end offsets
            response = self._send(broker, _OffsetRequest(-1, topic_partitions), _OffsetResponse)

            if response:
                for offset in response.topics:
                    topic = offset[0]
                    if topic not in end_offsets:
                        end_offsets[topic] = {}

                    for p in offset[1]:
                        end_offsets[topic][p[0]] = p[2][0]

        # Populate with offset values
        for group, topics in group_topics.iteritems():

            coordinator = consumer_coordinator[group]

            # topic -> list(partition)
            request_partitions = {}

            for topic in topics:
                results[group]['topics'][topic]['consumer_lag'] = 0
                results[group]['topics'][topic]['partitions'] = {}

                if topic in start_offsets:
                    for p in start_offsets[topic]:
                        results[group]['topics'][topic]['partitions'][p] = {
                            'offset_first': start_offsets[topic][p],
                            'offset_last': end_offsets[topic][p],
                            'offset_consumed': 0,
                            'lag' : 0}

                        if topic not in request_partitions:
                            request_partitions[topic] = []
                        request_partitions[topic].append(p)

            # List(topic -> list(partition))
            topic_partitions = []

            for tp in request_partitions.iteritems():
                topic_partitions.append(tp)

            response = self._send(coordinator, _OffsetFetchRequest(group, topic_partitions), _OffsetFetchResponse)

            if response:
                for offset in response.topics:
                    topic = offset[0]
                    offsets = offset[1]

                    if topic not in results[group]['topics']:
                        continue

                    for p_offset in offsets:
                        partition = p_offset[0]
                        offset_consumed = p_offset[1]
                        p_results = results[group]['topics'][topic]['partitions'][partition]

                        if offset_consumed != -1:
                            p_results['offset_consumed'] = offset_consumed
                            p_results['lag'] = p_results['offset_last'] - offset_consumed
                        else:
                            p_results['offset_consumed'] = 0
                            p_results['lag'] = p_results['offset_last'] - p_results['offset_first']

                        results[group]['topics'][topic]['consumer_lag'] += p_results['lag']

        return results

    def close(self):
        if self.client:
            self.client.close()
