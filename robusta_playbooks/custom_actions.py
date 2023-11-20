from robusta.api import *
from typing import List
from robusta.core.reporting.base import (
    Finding,
    FindingSeverity,
    FindingSource,
)
from hikaru.model.rel_1_26 import *


class CheckPodReadyParams(ActionParams):
    prefixes: List[str]  # Define a list of strings for prefixes
    namespace: str


@action
def check_pod_ready_pod_event(event: PodEvent, params: CheckPodReadyParams):
    pod = event.get_pod()
    pod_name = pod.metadata.name

    # Check if the pod's name starts with any of the specified prefixes
    for prefix in params.prefixes:
        if pod_name.startswith(prefix) and pod.metadata.namespace == params.namespace:
            # Get all pods in the namespace
            pod_list: PodList = PodList.listNamespacedPod(pod.metadata.namespace)
            all_pods = pod_list.obj.items  # Access the list of pods

            # Count pods with the prefix that are ready to handle connections
            ready_pods_with_prefix = sum(
                1 for p in all_pods if p.metadata.name.startswith(prefix) and any(
                    cond.type == "Ready" and cond.status == "True" for cond in p.status.conditions)
            )

            if ready_pods_with_prefix == 0:
                event.add_finding(
                    Finding(
                        title=f"No ready pods left with prefix {prefix}",
                        severity=FindingSeverity.HIGH,
                        source=FindingSource.NONE,
                        aggregation_key=f"Custom Event {pod_name}",
                        description=f"No ready pods left with prefix {prefix}"
                    )
                )
            break


@action
def check_pod_ready_kube_event(event: EventChangeEvent, params: CheckPodReadyParams):
    # Get all pods in the namespace
    pod_list: PodList = PodList.listNamespacedPod(params.namespace)
    all_pods = pod_list.obj.items  # Access the list of pods

    # Check if the pod's name starts with any of the specified prefixes
    for prefix in params.prefixes:
        # Count pods with the prefix that are ready to handle connections
        ready_pods_with_prefix = sum(
            1 for p in all_pods if p.metadata.name.startswith(prefix) and any(
                cond.type == "Ready" and cond.status == "True" for cond in p.status.conditions)
        )

        if ready_pods_with_prefix == 0:
            event.add_finding(
                Finding(
                    title=f"No ready pods left with prefix {prefix}",
                    severity=FindingSeverity.HIGH,
                    source=FindingSource.NONE,
                    aggregation_key=f"Custom Event {prefix}",
                    description=f"No ready pods left with prefix {prefix}"
                )
            )