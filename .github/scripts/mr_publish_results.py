# Send model regression test.csv results to Segment and Datadog
# with a summary of all test.csv results.
# Also write them into a report file.
import copy
import datetime
import json
import os
from typing import Any, Dict, List, Tuple

import analytics
from datadog_api_client.v1 import ApiClient, Configuration
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.model.metrics_payload import MetricsPayload
from datadog_api_client.v1.model.point import Point
from datadog_api_client.v1.model.series import Series

DD_ENV = "rasa-regression-tests"
DD_SERVICE = "rasa"
METRIC_RUNTIME_PREFIX = "rasa.perf.benchmark."
METRIC_ML_PREFIX = "rasa.perf.ml."
CONFIG_REPOSITORY = "training-data"

task_mapping = {
    "intent_report.json": "intent_classification",
    "CRFEntityExtractor_report.json": "entity_prediction",
    "DIETClassifier_report.json": "entity_prediction",
    "response_selection_report.json": "response_selection",
    "story_report.json": "story_prediction",
}

task_mapping_segment = {
    "intent_report.json": "Intent Classification",
    "CRFEntityExtractor_report.json": "Entity Prediction",
    "DIETClassifier_report.json": "Entity Prediction",
    "response_selection_report.json": "Response Selection",
    "story_report.json": "Story Prediction",
}


def transform_to_seconds(duration: str) -> float:
    """Transform string (with hours, minutes, and seconds) to seconds.

    Args:
        duration: Examples: '1m27s', '1m27.3s', '27s', '1h27s', '1h1m27s'

    Raises:
        Exception: If the input is not supported.

    Returns:
        Duration converted in seconds.
    """
    h_split = duration.split("h")
    if len(h_split) == 1:
        rest = h_split[0]
        hours = 0
    else:
        hours = int(h_split[0])
        rest = h_split[1]
    m_split = rest.split("m")
    if len(m_split) == 2:
        minutes = int(m_split[0])
        seconds = float(m_split[1].rstrip("s"))
    elif len(m_split) == 1:
        minutes = 0
        seconds = float(m_split[0].rstrip("s"))
    else:
        raise Exception(f"Unsupported duration: {duration}")
    overall_seconds = hours * 60 * 60 + minutes * 60 + seconds
    return overall_seconds


def prepare_runtime_metrics() -> Dict[str, float]:
    return {
        "test_run_time": os.environ["TEST_RUN_TIME"],
        "train_run_time": os.environ["TRAIN_RUN_TIME"],
        "total_run_time": os.environ["TOTAL_RUN_TIME"],
    }


def prepare_ml_metric(result: Dict[str, Any]) -> Dict[str, float]:
    """Converts a nested result dict into a list of metrics.

    Args:
        result: Example
            {'accuracy': 1.0,
             'weighted avg': {
                'precision': 1.0, 'recall': 1.0, 'f1-score': 1.0, 'support': 28
             }
            }

    Returns:
        Dict of metric name and metric value
    """
    metrics_ml = {}
    result = copy.deepcopy(result)
    result.pop("file_name", None)
    task = result.pop("task", None)

    for metric_name, metric_value in result.items():
        if isinstance(metric_value, float):
            metric_full_name = f"{task}.{metric_name}"
            metrics_ml[metric_full_name] = float(metric_value)
        elif isinstance(metric_value, dict):
            for mname, mval in metric_value.items():
                metric_full_name = f"{task}.{metric_name}.{mname}"
                metrics_ml[metric_full_name] = float(mval)
        else:
            raise Exception(
                f"metric_value {metric_value} has",
                f"unexpected type {type(metric_value)}",
            )
    return metrics_ml


def prepare_ml_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    metrics_ml = {}
    for result in results:
        new_metrics_ml = prepare_ml_metric(result)
        metrics_ml.update(new_metrics_ml)

    return metrics_ml


def prepare_tags() -> List[str]:
    tags = {
        "env": DD_ENV,
        "service": DD_SERVICE,
        "accelerator_type": os.environ["ACCELERATOR_TYPE"],
        "dataset": os.environ["DATASET_NAME"],
        "config": os.environ["CONFIG"],
        "dataset_commit": os.environ["DATASET_COMMIT"],
        "branch": os.environ["BRANCH"],
        "github_sha": os.environ["GITHUB_SHA"],
        "pr_id": os.environ["PR_ID"],
        "pr_url": os.environ["PR_URL"],
        "dataset_repository_branch": os.environ["DATASET_REPOSITORY_BRANCH"],
        "external_dataset_repository": os.environ["IS_EXTERNAL"],
        "config_repository": CONFIG_REPOSITORY,
        "config_repository_branch": os.environ["DATASET_REPOSITORY_BRANCH"],
        "workflow": os.environ["GITHUB_WORKFLOW"],
        "github_run_id": os.environ["GITHUB_RUN_ID"],
        "github_event": os.environ["GITHUB_EVENT_NAME"],
        "type": os.environ["TYPE"],
    }
    tags_list = [f"{k}:{v}" for k, v in tags.items()]
    return tags_list


def send_to_datadog(results: List[Dict[str, Any]]) -> None:
    """Sends metrics to datadog."""
    # Prepare
    tags_list = prepare_tags()
    timestamp = datetime.datetime.now().timestamp()
    series = []

    # Send metrics about runtime
    metrics_runtime = prepare_runtime_metrics()
    for metric_name, metric_value in metrics_runtime.items():
        overall_seconds = transform_to_seconds(metric_value)
        series.append(
            Series(
                metric=f"{METRIC_RUNTIME_PREFIX}{metric_name}.gauge",
                type="gauge",
                points=[Point([timestamp, overall_seconds])],
                tags=tags_list,
            )
        )

    # Send metrics about ML model performance
    metrics_ml = prepare_ml_metrics(results)
    for metric_name, metric_value in metrics_ml.items():
        series.append(
            Series(
                metric=f"{METRIC_ML_PREFIX}{metric_name}.gauge",
                type="gauge",
                points=[Point([timestamp, float(metric_value)])],
                tags=tags_list,
            )
        )

    body = MetricsPayload(series=series)
    with ApiClient(Configuration()) as api_client:
        api_instance = MetricsApi(api_client)
        response = api_instance.submit_metrics(body=body)
        if response.get("status") != "ok":
            print(response)


def _send_to_segment(context: Dict[str, Any]) -> None:
    (
        is_external,
        dataset_repository_branch,
    ) = _get_is_external_and_dataset_repository_branch()

    jobID = os.environ["GITHUB_RUN_ID"]

    analytics.identify(
        jobID, {"name": "model-regression-tests", "created_at": datetime.datetime.now()}
    )

    analytics.track(
        jobID,
        "results",
        {
            "dataset": os.environ["DATASET_NAME"],
            "dataset_repository_branch": dataset_repository_branch,
            "external_dataset_repository": is_external,
            "config_repository": CONFIG_REPOSITORY,
            "config_repository_branch": os.environ["DATASET_REPOSITORY_BRANCH"],
            "dataset_commit": os.environ["DATASET_COMMIT"],
            "workflow": os.environ["GITHUB_WORKFLOW"],
            "config": os.environ["CONFIG"],
            "pr_url": os.environ["PR_URL"],
            "accelerator_type": os.environ["ACCELERATOR_TYPE"],
            "test_run_time": os.environ["TEST_RUN_TIME"],
            "train_run_time": os.environ["TRAIN_RUN_TIME"],
            "total_run_time": os.environ["TOTAL_RUN_TIME"],
            "github_run_id": os.environ["GITHUB_RUN_ID"],
            "github_sha": os.environ["GITHUB_SHA"],
            "github_event": os.environ["GITHUB_EVENT_NAME"],
            "type": os.environ["TYPE"],
            **context,
        },
    )


def _get_is_external_and_dataset_repository_branch() -> Tuple[bool, str]:
    is_external = os.environ["IS_EXTERNAL"]
    dataset_repository_branch = os.environ["DATASET_REPOSITORY_BRANCH"]
    if is_external.lower() in ("yes", "true", "t", "1"):
        is_external_flag = True
        dataset_repository_branch = os.environ["EXTERNAL_DATASET_REPOSITORY_BRANCH"]
    else:
        is_external_flag = False
    return is_external_flag, dataset_repository_branch


def read_results(file: str) -> Dict[str, Any]:
    with open(file) as json_file:
        data = json.load(json_file)

        keys = [
            "accuracy",
            "weighted avg",
            "macro avg",
            "micro avg",
            "conversation_accuracy",
        ]
        result = {key: data[key] for key in keys if key in data}

    return result


def _push_results(file_name: str, file: str) -> None:
    result = get_result(file_name, file)
    result["task"] = task_mapping_segment[file_name]
    _send_to_segment(result)


def get_result(file_name: str, file: str) -> Dict[str, Any]:
    result = read_results(file)
    result["file_name"] = file_name
    result["task"] = task_mapping[file_name]
    return result


def send_all_to_datadog() -> None:
    results = []
    for dirpath, dirnames, files in os.walk(os.environ["RESULT_DIR"]):
        for f in files:
            if any(f.endswith(valid_name) for valid_name in task_mapping.keys()):
                result = get_result(f, os.path.join(dirpath, f))
                results.append(result)
    send_to_datadog(results)


def generate_json(file: str, task: str, data: dict) -> dict:
    (
        is_external,
        dataset_repository_branch,
    ) = _get_is_external_and_dataset_repository_branch()
    config = os.environ["CONFIG"]
    dataset = os.environ["DATASET"]

    if dataset not in data:
        data = {dataset: {config: {}}, **data}
    elif config not in data[dataset]:
        data[dataset] = {config: {}, **data[dataset]}

    data[dataset][config] = {
        "external_dataset_repository": is_external,
        "dataset_repository_branch": dataset_repository_branch,
        "config_repository": CONFIG_REPOSITORY,
        "config_repository_branch": os.environ["DATASET_REPOSITORY_BRANCH"],
        "dataset_commit": os.environ["DATASET_COMMIT"],
        "accelerator_type": os.environ["ACCELERATOR_TYPE"],
        "test_run_time": os.environ["TEST_RUN_TIME"],
        "train_run_time": os.environ["TRAIN_RUN_TIME"],
        "total_run_time": os.environ["TOTAL_RUN_TIME"],
        "type": os.environ["TYPE"],
        **data[dataset][config],
    }

    data[dataset][config][task] = {**read_results(file)}

    return data


def send_all_results_to_segment() -> None:
    analytics.write_key = os.environ["SEGMENT_TOKEN"]
    for dirpath, dirnames, files in os.walk(os.environ["RESULT_DIR"]):
        for f in files:
            if any(
                f.endswith(valid_name) for valid_name in task_mapping_segment.keys()
            ):
                _push_results(f, os.path.join(dirpath, f))
    analytics.flush()


def create_report_file() -> None:
    data = {}
    for dirpath, dirnames, files in os.walk(os.environ["RESULT_DIR"]):
        for f in files:
            if f not in task_mapping.keys():
                continue

            data = generate_json(os.path.join(dirpath, f), task_mapping[f], data)

    with open(os.environ["SUMMARY_FILE"], "w") as f:
        json.dump(data, f, sort_keys=True, indent=2)


if __name__ == "__main__":
    send_all_to_datadog()
    send_all_results_to_segment()
    create_report_file()
