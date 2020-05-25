import math
import time
import socket
import threading
from datetime import datetime
import queue


# This is a port of Akka's Phi-accrual failure detector.


class HeartbeatHistory:
    """Stores the sample window"""
    def __init__(self, max_sample_size):
        self.max_sample_size = max_sample_size
        self.intervals = queue.Queue()
        self.interval_sum = 0
        self.squared_interval_sum = 0

    def mean(self):
        return self.interval_sum / self.intervals.qsize()

    def variance(self):
        return self.squared_interval_sum / self.intervals.qsize() - self.mean() ** 2

    def std_deviation(self):
        return math.sqrt(self.variance())

    def add(self, interval):
        if self.intervals.qsize() >= self.max_sample_size:
            # Need to drop oldest sample
            head = self.intervals.get()
            self.interval_sum -= head
            self.squared_interval_sum -= head ** 2

        self.intervals.put(interval)
        self.interval_sum += interval
        self.squared_interval_sum += interval ** 2



class PhiAccrualFailureDetector:
    """
    Implementation of 'The Phi Accrual Failure Detector' by Hayashibara et al. as defined in their paper:
    [https://pdfs.semanticscholar.org/11ae/4c0c0d0c36dc177c1fff5eb84fa49aa3e1a8.pdf]

    The suspicion level of failure is given by a value called φ (phi).
    The basic idea of the φ failure detector is to express the value of φ on a scale that
    is dynamically adjusted to reflect current network conditions. A configurable
    threshold is used to decide if φ is considered to be a failure.

    The value of φ is calculated as: φ = -log10(1 - F(timeSinceLastHeartbeat)
    where F is the cumulative distribution function of a normal distribution with mean
    and standard deviation estimated from historical heartbeat inter-arrival times.

    Parameters:
    * threshold: A low threshold is prone to generate many wrong suspicions but ensures a quick detection in the event
      of a real crash. Conversely, a high threshold generates fewer mistakes but needs more time to detect
      actual crashes

    * maxSampleSize:  Number of samples to use for calculation of mean and standard deviation of
      inter-arrival times.

    * minStdDeviationMillis:  Minimum standard deviation to use for the normal distribution used when calculating phi.
      Too low standard deviation might result in too much sensitivity for sudden, but normal, deviations
      in heartbeat inter arrival times.

    * acceptableHeartbeatPauseMillis: Duration corresponding to number of potentially lost/delayed
      heartbeats that will be accepted before considering it to be an anomaly.
      This margin is important to be able to survive sudden, occasional, pauses in heartbeat
      arrivals, due to for example garbage collect or network drop.

    * firstHeartbeatEstimateMillis: Bootstrap the stats with heartbeats that corresponds to
      to this duration, with a with rather high standard deviation (since environment is unknown
      in the beginning)
    """
    def __init__(self,
                 threshold=8,
                 max_sample_size=200,
                 min_std_deviation_millis=200,
                 acceptable_heartbeat_pause_millis=0,
                 first_heartbeat_estimate_millis=1000):
        self.threshold = threshold
        self.min_stddev_millis = min_std_deviation_millis
        self.acceptable_heartbeat_pause_millis = acceptable_heartbeat_pause_millis
        self.max_sample_size = max_sample_size
        self.first_hb = first_heartbeat_estimate_millis
        # self.last_timestamp = datetime.now()
        self.reinit()

    def reinit(self):
        self.heatbeat_history = HeartbeatHistory(self.max_sample_size)
        stddev_millis = self.first_heartbeat_estimate_millis / 4
        self.heatbeat_history.add(
            self.first_heartbeat_estimate_millis - stddev_millis)
        self.heatbeat_history.add(
            self.first_heartbeat_estimate_millis + stddev_millis)


    def ensure_valid_stddev(self, stddev_millis):
        return max(stddev_millis, self.min_stddev_millis)

    def phi(self, timestamp):
        if self.last_timestamp is None:
            return 0

        timediff_millis = (timestamp - self.last_timestamp).total_seconds() * 1000
        mean_millis = self.heatbeat_history.mean() + self.acceptable_heartbeat_pause_millis
        stddev_millis = self.ensure_valid_stddev(self.heatbeat_history.std_deviation())
        # print(mean_millis, stddev_millis)

        # print("timediff: {}, mean: {}, stddev: {}".format(timediff_millis, mean_millis, stddev_millis))
        y = (timediff_millis - mean_millis) / stddev_millis
        e = math.exp(-y * (1.5976 + 0.070566 * y * y))
        # print("e: {}".format(e))
        if timediff_millis > mean_millis:
            return -math.log10(e / (1 + e))
        else:
            return -math.log10(1 - 1 / (1 + e))

    def is_available(self, time):
        return self.phi(time) < self.threshold

    def heartbeat(self, timestamp):
        last_timestamp = self.last_timestamp
        self.last_timestamp = timestamp
        if last_timestamp is not None:
            if self.is_available():
                self.heatbeat_history.add(
                    (timestamp - last_timestamp).total_seconds() * 1000)


class DetectorManager:
    """Manages all failure detectors"""
    def __init__(self, broadcast_address="255.255.255.255"):
        self.detectors = {}
        self.server = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Enable broadcasting mode
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        listenfd = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        listenfd.bind(("", 37021))

        def listen_fn():
            while True:
                data, addr = listenfd.recvfrom(1024)
                if addr[0] in self.detectors:
                    self.detectors[addr[0]].heartbeat(datetime.now())

        def server_fn():
            while True:
                time.sleep(1)
                print(self.check_status())
                self.server.sendto(b"", (broadcast_address, 37020))

        threading.Thread(target=listen_fn).start()
        threading.Thread(target=server_fn).start()

    def add_node(self, ip):
        detector = PhiAccrualFailureDetector()
        self.detectors[ip] = detector

    def heartbeat(self, ip):
        self.detectors[ip].heartbeat(datetime.now())

    def check_status(self):
        res = {}
        for ip in self.detectors:
            res[ip] = self.detectors[ip].is_available(datetime.now())

        return res
