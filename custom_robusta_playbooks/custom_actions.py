from robusta.api import *
from typing import List
from robusta.core.reporting.base import (
    Finding,
    FindingSeverity,
    FindingSource,
)
from hikaru.model.rel_1_26 import *
from kubernetes import client, config


class CheckHpaLimitParams(ActionParams):
    hpa_names: List[str]  # Names of HPAs to monitor
    namespace: str  # Namespace where HPAs are located


class CheckPodReadyParams(ActionParams):
    prefixes: List[str]  # Define a list of strings for prefixes
    namespace: str


@action
def check_pod_ready(event: ExecutionBaseEvent, params: CheckPodReadyParams):
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


@action
def check_hpa_limits(event: ExecutionBaseEvent, params: CheckHpaLimitParams):
    config.load_incluster_config()
    v1 = client.AutoscalingV1Api()

    for hpa_name in params.hpa_names:
        hpa = v1.read_namespaced_horizontal_pod_autoscaler(hpa_name, params.namespace)
        current_replicas = hpa.status.current_replicas
        max_replicas = hpa.spec.max_replicas

        # Check if current replicas are equal to max replicas
        if current_replicas >= max_replicas:
            event.add_finding(
                Finding(
                    title=f"HPA Limit Reached for {hpa_name}",
                    severity=FindingSeverity.HIGH,
                    source=FindingSource.NONE,
                    aggregation_key=f"Hpa limit reached {hpa_name}",
                    description=f"The HPA {hpa_name} in namespace {params.namespace} has reached its maximum limit of {max_replicas} replicas."
                )
            )
