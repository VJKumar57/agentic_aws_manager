from typing import Optional, Dict, Any, List
from .aws_auth import get_client

def list_metrics(namespace: Optional[str] = None, metric_name: Optional[str] = None, dimensions: Optional[List[Dict[str, str]]] = None, profile: Optional[str] = None, region_name: Optional[str] = None) -> List[Dict[str, Any]]:
    client = get_client('cloudwatch', profile=profile, region_name=region_name)
    paginator = client.get_paginator('list_metrics')
    kwargs = {}
    if namespace:
        kwargs['Namespace'] = namespace
    if metric_name:
        kwargs['MetricName'] = metric_name
    if dimensions:
        kwargs['Dimensions'] = dimensions
    metrics = []
    for page in paginator.paginate(**kwargs):
        metrics.extend(page.get('Metrics', []))
    return metrics

def get_metric_statistics(namespace: str, metric_name: str, dimensions: List[Dict[str, str]], start_time, end_time, period: int = 60, statistics: Optional[List[str]] = None, profile: Optional[str] = None, region_name: Optional[str] = None) -> Dict[str, Any]:
    client = get_client('cloudwatch', profile=profile, region_name=region_name)
    stats = statistics or ['Average', 'Sum', 'SampleCount']
    resp = client.get_metric_statistics(Namespace=namespace, MetricName=metric_name, Dimensions=dimensions, StartTime=start_time, EndTime=end_time, Period=period, Statistics=stats)
    return resp

def get_metric_data(metric_data_queries: List[Dict[str, Any]], start_time, end_time, profile: Optional[str] = None, region_name: Optional[str] = None) -> Dict[str, Any]:
    client = get_client('cloudwatch', profile=profile, region_name=region_name)
    resp = client.get_metric_data(MetricDataQueries=metric_data_queries, StartTime=start_time, EndTime=end_time)
    return resp
