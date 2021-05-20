from datetime import datetime
from math import ceil
from typing import List, Optional

import plotly.figure_factory as ff
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from benchmarking.evaluation.metrics.distance_traveled_metric import DistanceTraveledMetric
from godeliver_planner.helper.timestamp_helper import TimestampHelper
from benchmarking.evaluation.metrics.delay_metric import DelayMetric
from benchmarking.evaluation.metrics.deliveries_per_courier import DeliveriesPerCourierMetric
from benchmarking.evaluation.metrics.delivery_en_route_metric import DeliveryEnRouteMetric
from benchmarking.evaluation.metrics.delivery_load_metric import NoPackagesPerPickup
from godeliver_planner.model.delivery import Delivery
from godeliver_planner.model.delivery_event import DeliveryEvent, DeliveryEventType
from godeliver_planner.model.plan import Plan
from godeliver_planner.model.timeblock import TimeBlock


class PlanVisualisation:
    metrics = [DelayMetric(DeliveryEventType.drop),
               DeliveryEnRouteMetric(),
               # DeliveriesPerCourierMetric(),
               NoPackagesPerPickup(),
               DistanceTraveledMetric(),
               ]

    @staticmethod
    def update_y_coord(y):
        y = list(y)
        for i in range(int(ceil(len(y) / 5))):
            idx = i * 5
            row = int(round(y[idx]))
            if row % 3 == 1:
                y[idx] = y[idx] - 0.1
                y[idx + 1] = y[idx + 1] - 0.1
                y[idx + 2] = y[idx + 2] + 0.1
                y[idx + 3] = y[idx + 3] + 0.1
            elif row % 3 == 2:
                y[idx] = y[idx] - 0.4
                y[idx + 1] = y[idx + 1] - 0.4
            else:
                y[idx + 2] = y[idx + 2] + 0.4
                y[idx + 3] = y[idx + 3] + 0.4

        return y

    @staticmethod
    def timestamp_to_str(times_stamp: int) -> str:
        loc_dt = datetime.fromtimestamp(times_stamp)

        return loc_dt.strftime('%Y-%m-%d %H:%M')

    @staticmethod
    def evalute_delivery_position_for_vis(time_block: TimeBlock, arrival: DeliveryEvent):
        start = time_block.from_time if time_block is not None else int(TimestampHelper.current_timestamp())
        finish = time_block.get_to_time() if time_block is not None else int(TimestampHelper.current_timestamp())
        is_on_time = time_block is None or \
                     (arrival is not None and not
                     (arrival.event_time.to_time < start or arrival.event_time.from_time > finish))

        state = 'Ontime' if is_on_time else 'Delayed'
        return {
            'Start': PlanVisualisation.timestamp_to_str(start),
            'Finish': PlanVisualisation.timestamp_to_str(finish),
            'Resource': state
        }

    @staticmethod
    def prepare_delivery_for_vis(delivery: Delivery, pickup_event: Optional[DeliveryEvent],
                                 drop_event: Optional[DeliveryEvent], order: int, driver_id: str):
        order_id_short = delivery.id[:6]

        data = [
            dict(Task=f"Delivery-{order_id_short}-pickup", **PlanVisualisation.evalute_delivery_position_for_vis(
                delivery.pickup_time, pickup_event)),

            dict(Task=f"Delivery-{order_id_short}-drop", **PlanVisualisation.evalute_delivery_position_for_vis(
                delivery.delivery_time, drop_event))
        ]

        annots = []
        if delivery.pickup_time is not None:
            annots.append(dict(x=PlanVisualisation.timestamp_to_str(
                int(delivery.pickup_time.from_time + (
                        delivery.pickup_time.get_to_time() - delivery.pickup_time.from_time) / 2)),
                y=(order - 1) * 3 - 1.2, text="Pickup Window", showarrow=False, font=dict(color='white')))

        annots.append(
            dict(x=PlanVisualisation.timestamp_to_str(
                int(delivery.delivery_time.from_time + (
                        delivery.delivery_time.get_to_time() - delivery.delivery_time.from_time) / 2)),
                 y=(order - 1) * 3 - 2.8, text="Drop Window", showarrow=False, font=dict(color='White'))
        )

        if drop_event is not None and pickup_event is not None:
            pickup_time = pickup_event.event_time.to_time
            data.insert(1,
                        dict(Task=f"Delivery-{order_id_short}-in-progress",
                             Start=PlanVisualisation.timestamp_to_str(pickup_event.event_time.from_time),
                             Finish=PlanVisualisation.timestamp_to_str(pickup_event.event_time.to_time),
                             Resource='Waiting'))

            data.insert(2,
                        dict(Task=f"Delivery-{order_id_short}-in-progress",
                             Start=PlanVisualisation.timestamp_to_str(pickup_event.event_time.to_time),
                             Finish=PlanVisualisation.timestamp_to_str(drop_event.event_time.from_time),
                             Resource='Progress'))

            data.insert(3,
                        dict(Task=f"Delivery-{order_id_short}-in-progress",
                             Start=PlanVisualisation.timestamp_to_str(drop_event.event_time.from_time),
                             Finish=PlanVisualisation.timestamp_to_str(drop_event.event_time.to_time),
                             Resource='Waiting'))

            annots.insert(1,
                          dict(x=PlanVisualisation.timestamp_to_str(
                              int(pickup_time + (drop_event.event_time.from_time - pickup_time) / 2)),
                              y=(order - 1) * 3 - 2, text=f"🚗 {driver_id}", showarrow=False,
                              font=dict(color='White')))

        return data, annots

    @staticmethod
    def time_block_to_range(time_block: TimeBlock):
        fr = time_block.from_time
        to = time_block.to_time

    @staticmethod
    def prepare_data_vis(deliveries: List[Delivery], plans: List[Plan]):
        data = []
        annot = []

        delivery_id_to_delivery = {delivery.id: delivery for delivery in deliveries}
        all_deliveries = set(map(lambda x: x.id, deliveries))

        start_idx = 0

        for idx, plan in enumerate(plans):
            delivery_to_pickup_events = {}
            delivery_to_drop_events = {}

            delivery_orders_plan = []

            driver_id = plan.assigned_courier_id
            if driver_id is None:
                driver_id = f"#{idx}"

            for delivery_event in plan.delivery_events:
                if delivery_event.type == DeliveryEventType.pickup:
                    for delivery_order_id in delivery_event.delivery_order_ids:
                        delivery_to_pickup_events[delivery_order_id] = delivery_event

                elif delivery_event.type == DeliveryEventType.drop:
                    for delivery_order_id in delivery_event.delivery_order_ids:
                        delivery_to_drop_events[delivery_order_id] = delivery_event
                        delivery_orders_plan.append(delivery_order_id)

            for delivery_order_id in plan.delivery_order_ids:
                if delivery_order_id not in delivery_to_pickup_events:
                    delivery_to_pickup_events[delivery_order_id] = None

            for idx, delivery_order_id in enumerate(delivery_orders_plan):
                delivery = delivery_id_to_delivery[delivery_order_id]
                pickup_event = delivery_to_pickup_events[delivery_order_id]
                drop_event = delivery_to_drop_events[delivery_order_id]
                order = len(deliveries) - start_idx - idx + 1

                c_data, c_annot = PlanVisualisation.prepare_delivery_for_vis(
                    delivery, pickup_event, drop_event, order, driver_id
                )

                data.extend(c_data)
                annot.extend(c_annot)

            start_idx = start_idx + len(delivery_orders_plan)

            all_deliveries = all_deliveries - set(delivery_orders_plan)

        for idx, delivery_order_id in enumerate(all_deliveries):
            delivery = delivery_id_to_delivery[delivery_order_id]
            order = len(deliveries) - start_idx - idx + 1

            c_data, c_annot = PlanVisualisation.prepare_delivery_for_vis(
                delivery, None, None, order, "unassigned"
            )

            data.extend(c_data)
            annot.extend(c_annot)

        return data, annot

    @staticmethod
    def _plot_metric(deliveries: List[Delivery], plans: List[Plan], fig):
        for idx, metric in enumerate(PlanVisualisation.metrics):
            result = metric.compute(deliveries=deliveries, plans=plans)

            x_base = round(0.1 + idx * 0.2, 2)
            print(x_base)

            unit = metric.get_unit()

            y_step = 0.62 / len(deliveries)

            fig.add_annotation(text=f"<b>{metric.get_name()}</b>",
                               xref="paper", yref="paper", font=dict(size=20),
                               xanchor='left',
                               x=x_base, y=1 + 3.5 * y_step, showarrow=False, align='left')
            fig.add_annotation(text=f"Min:          {result.min:.2f} {unit}",
                               xanchor='left', xref="paper", yref="paper", font=dict(size=16),
                               x=x_base + 0.01, y=1 + 2.5 * y_step, showarrow=False, align='left')
            fig.add_annotation(text=f"Max:         {result.max:.2f} {unit}",
                               xanchor='left', xref="paper", yref="paper", font=dict(size=16),
                               x=x_base + 0.01, y=1 + 2.0 * y_step, showarrow=False, align='left')
            fig.add_annotation(text=f"Average:   {result.average:.2f} {unit}",
                               xref="paper", yref="paper", font=dict(size=16),
                               xanchor='left', x=x_base + 0.01, y=1 + 1.5 * y_step, showarrow=False, align='left')
            fig.add_annotation(text=f"Total:        {result.total:.2f} {unit}",
                               xanchor='left', xref="paper", yref="paper", font=dict(size=16),
                               x=x_base + 0.01, y=1 + 1 * y_step, showarrow=False, align='left')

    @staticmethod
    def visualise_orders(deliveries: List[Delivery], plans: List[Plan]):
        data, annots = PlanVisualisation.prepare_data_vis(deliveries, plans)

        colors = {
            'Ontime': '#688E26',
            'Delayed': '#A10702',
            'Progress': "#313638",
            'Waiting': "#7c7878"
        }

        gant_height = max(60 * len(deliveries), 800)
        total_height = gant_height + 800

        fig = make_subplots(rows=2, cols=1,   specs=[[{"type": "xy"}], [{"type": "mapbox"}]],
                            vertical_spacing=0.05, row_heights=[gant_height / total_height, 1 - (gant_height/total_height)],
                            row_titles=['Deliveries in Plan ', "Map of the plans"])

        fig_sec = ff.create_gantt(data, colors=colors, index_col='Resource', group_tasks=True,
                                  title='Deliveries in Plan')

        for i in range(4):
            if fig_sec['data'][i]['fill'] is None:
                break
            fig_sec['data'][i]['y'] = PlanVisualisation.update_y_coord(fig_sec['data'][i]['y'])

        for g in fig_sec['data']:
            fig.add_trace(g, row=1, col=1)

        fig.update_yaxes(ticktext=fig_sec.layout.yaxis.ticktext, row=1, col=1)
        fig.update_yaxes(tickvals=fig_sec.layout.yaxis.tickvals, row=1, col=1)

        fig['layout']['yaxis']['autorange'] = True
        fig['layout']['annotations'] = annots
        fig['layout']['height'] = total_height
        fig.update_layout(margin=dict(l=150, r=50, b=100, t=200, pad=4))

        PlanVisualisation._plot_metric(deliveries, plans, fig)
        PlanVisualisation.plot_map(plans, fig)

        fig.show()

    @staticmethod
    def plot_map(plans: List[Plan], fig):

        for idx, plan in enumerate(plans):
            lat = list(map(lambda x: x.location.latitude, plan.delivery_events))
            lon = list(map(lambda x: x.location.longitude, plan.delivery_events))

            driver_id = plan.assigned_courier_id
            if driver_id is None:
                driver_id = f"#{idx}"

            fig.add_trace(go.Scattermapbox(
                name=f"🚗 {driver_id}",
                mode="markers+lines+text",
                text=[f"{idx}. {event}" for idx, event in enumerate(plan.delivery_events)],
                lon=lon,
                lat=lat,
                marker={'size': 10}), row=2, col=1)

        fig.update_layout(
            mapbox={
                'center': {'lon': 14.45, 'lat': 50.1},
                'style': "stamen-terrain",
                'zoom': 12})
