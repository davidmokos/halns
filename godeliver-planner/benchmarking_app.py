import os

import streamlit as st
import pandas as pd

from benchmarking.benchmarking_common import METRICS
from benchmarking.database.firebase_manager import FirebaseManager
from benchmarking.evaluation.metrics.delivery_en_route_metric import DeliveryEnRouteMetric


def load_data() -> pd.DataFrame:
    firebase_key = os.environ.get('FIREBASE_CONFIG',
                                  os.path.join('config', 'godeliver-benchmarking-firebase-key.json'))

    manager = FirebaseManager(firebase_key)

    stream = manager.database.collection(u'planner').stream(timeout=5)

    dicts = list(map(lambda x: x.to_dict(), stream))

    data = pd.DataFrame.from_records(dicts)
    return data


def get_metric_table(metric: str, data: pd.DataFrame):
    metric_data = data.loc[data['metric_name'] == metric]
    index = ['dataset_name']
    if split_instance:
        index.append('instance_name')
    table = metric_data.pivot_table(values=metric_selected, index=index, columns='model_name')

    return table


data = load_data()

split_instance = st.sidebar.checkbox("Instances split")
metric_selected = st.sidebar.radio("Metric to display", options=['metric_average', 'metric_min',
                                                                 'metric_max', 'metric_total'])

for metric in METRICS:
    st.title(metric.get_name() + " (" + metric.get_unit() + ")")
    st.table(get_metric_table(metric.get_id(), data))



