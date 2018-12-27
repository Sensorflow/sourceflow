from applauncher.kernel import Environments, Kernel
# import remote_event_bundle
# import redis_bundle
import source_flow_bundle
import apscheduler_bundle

bundle_list = [
    # redis_bundle.RedisBundle(),
    # remote_event_bundle.RemoteEventBundle(),
    apscheduler_bundle.APSchedulerBundle(),
    source_flow_bundle.SourceFlowBundle()
]

with Kernel(Environments.DEVELOPMENT, bundle_list) as kernel:
   kernel.wait()