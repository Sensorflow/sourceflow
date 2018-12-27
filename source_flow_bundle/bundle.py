import logging
from applauncher.kernel import KernelReadyEvent, ConfigurationReadyEvent, Configuration
# from remote_event_bundle import RemoteEvent
import inject
# import netifaces as ni
from .sinkflow import SinkflowClient
from apscheduler_bundle import Scheduler
from datetime import datetime, timedelta
import time
from beaglebone import enable_usb, enable_network

# class NetworkUpEvent(RemoteEvent):
#     event_name = "network_up"
#
#     def __init__(self, network_interface):
#         self.network_interface = network_interface
#
#
# class NetworkDownEvent(RemoteEvent):
#     event_name = "network_down"
#
#     def __init__(self, network_interface):
#         self.network_interface = network_interface


class SourceFlowBundle(object):

    def __init__(self):
        self.logger = logging.getLogger("source-flow")
        self.config_mapping = {
            "sourceflow": {
                "api_key": None,
                "sleep_hour": None,
                "wake_hour": None,
                "read_interval": 10
            }
        }

        self.injection_bindings = {}

        self.event_listeners = [
            # (NetworkDownEvent, self.network_down),
            # (NetworkUpEvent, self.network_up),
            (ConfigurationReadyEvent, self.config_ready),
            (KernelReadyEvent, self.kernel_ready)
        ]

    # def enable_network(self, enabled):
    #     pass

    def read_sensors(self):
        self.logger.info("Reading sensors")
        sc = inject.instance(SinkflowClient)
        from random import randint
        sc.sink({"cosa": randint(1, 55)})

    def sleep(self):
        enable_network(False)
        enable_usb(False)

    def wake_up(self, retry=True):
        sc = inject.instance(SinkflowClient)
        enable_usb(True)
        enable_network(True)
        attempts = 0
        sc_available = sc.available()
        while not sc_available and attempts < 5:
            self.logger.info("Internet not available, waiting...")
            time.sleep(10)
            sc_available = sc.available()

        if not sc_available:
            self.logger.warning("Cannot connect to internet, shutting down modem")
            enable_network(False)
            enable_usb(False)
            # Try again in 5 minutes
            if retry:
                scheduler = inject.instance(Scheduler)
                scheduler.add_job(self.wake_up, 'date', run_date=datetime.now() + timedelta(minutes=5), args=[False])
        else:
            self.logger.info("Service ready, dumping data...")
            sc.dump()
            self.logger.info("Data dumped")

    @inject.params(scheduler=Scheduler)
    @inject.params(configuration=Configuration)
    def kernel_ready(self, event, scheduler, configuration):
        sleep_hour = configuration.sourceflow.sleep_hour
        wake_hour = configuration.sourceflow.wake_hour
        read_interval = configuration.sourceflow.read_interval

        scheduler.add_job(self.read_sensors, 'interval', seconds=read_interval, next_run_time=datetime.now() + timedelta(seconds=2))
        scheduler.add_job(self.sleep, "cron", hour=sleep_hour)  # Disable internet every day at 17
        scheduler.add_job(self.wake_up, "cron", hour=wake_hour)  # Enable internet and dump data every day at 16

    def config_ready(self, event):
        self.injection_bindings[SinkflowClient] = SinkflowClient(api_key=event.configuration.sourceflow.api_key, secure=False)

    # def network_down(self, event):
    #     print("Network down " + event.network_interface)
    #
    # @inject.params(sc=SinkflowClient)
    # def network_up(self, event, sc):
    #     self.logger.info("Network up " + event.network_interface)
    #
    #     if event.network_interface in ni.interfaces():
    #         ip = ni.ifaddresses(event.network_interface)[ni.AF_INET][0]['addr']
    #         self.logger.info("Network ip " + ip)
    #         while not sc.available():
    #             self.logger.info("Internet not available, waiting...")
    #             time.sleep(5)
    #
    #         self.logger.info("Service ready, dumping data...")
    #         sc.dump()
    #         self.logger.info("Data dumped")
    #
    #     else:
    #         self.logger.warning("Unknown network interface: " + str(event.network_interface))