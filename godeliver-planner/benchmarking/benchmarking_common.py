from benchmarking.evaluation.metrics.delay_metric import DelayMetric
from benchmarking.evaluation.metrics.deliveries_per_courier import DeliveriesPerCourierMetric
from benchmarking.evaluation.metrics.delivery_en_route_metric import DeliveryEnRouteMetric
from benchmarking.evaluation.metrics.delivery_load_metric import NoPackagesPerPickup
from benchmarking.evaluation.metrics.distance_traveled_metric import DistanceTraveledMetric
from benchmarking.evaluation.metrics.time_spent_metric import TimeSpentMetric
from benchmarking.model.dataset import Dataset
from benchmarking.model.file_instance import FileInstance
from godeliver_planner.model.delivery_event import DeliveryEventType

METRICS = [DelayMetric(DeliveryEventType.drop), DeliveriesPerCourierMetric(),
           DeliveryEnRouteMetric(), NoPackagesPerPickup(), DistanceTraveledMetric(),
           TimeSpentMetric()]

n20_DATASET = Dataset(name='20D', instances=[
    FileInstance(path="foodchain/20_deliveries_00.json", min_num_plans=2, name="00", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_01.json", min_num_plans=2, name="01", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_02.json", min_num_plans=2, name="02", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_03.json", min_num_plans=2, name="03", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_04.json", min_num_plans=2, name="04", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_05.json", min_num_plans=2, name="05", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_06.json", min_num_plans=2, name="06", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_07.json", min_num_plans=2, name="07", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_08.json", min_num_plans=2, name="08", dataset_name="20D"),
    FileInstance(path="foodchain/20_deliveries_09.json", min_num_plans=2, name="09", dataset_name="20D"),
])

n50_DATASET = Dataset(name='50D', instances=[
    FileInstance(path="foodchain/50_deliveries_00.json", min_num_plans=6, name="00", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_01.json", min_num_plans=6, name="01", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_02.json", min_num_plans=6, name="02", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_03.json", min_num_plans=6, name="03", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_04.json", min_num_plans=6, name="04", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_05.json", min_num_plans=6, name="05", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_06.json", min_num_plans=6, name="06", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_07.json", min_num_plans=6, name="07", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_08.json", min_num_plans=6, name="08", dataset_name="50D"),
    FileInstance(path="foodchain/50_deliveries_09.json", min_num_plans=6, name="09", dataset_name="50D"),
])

n100_DATASET = Dataset(name='100D', instances=[
    FileInstance(path="foodchain/100_deliveries_00.json", min_num_plans=11, name="00", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_01.json", min_num_plans=11, name="01", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_02.json", min_num_plans=11, name="02", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_03.json", min_num_plans=11, name="03", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_04.json", min_num_plans=11, name="04", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_05.json", min_num_plans=11, name="05", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_06.json", min_num_plans=11, name="06", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_07.json", min_num_plans=11, name="07", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_08.json", min_num_plans=11, name="08", dataset_name="100D"),
    FileInstance(path="foodchain/100_deliveries_09.json", min_num_plans=11, name="09", dataset_name="100D"),
])

n200_DATASET = Dataset(name='200D', instances=[
    FileInstance(path="foodchain/200_deliveries_00.json", min_num_plans=22, name="00", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_01.json", min_num_plans=22, name="01", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_02.json", min_num_plans=22, name="02", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_03.json", min_num_plans=22, name="03", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_04.json", min_num_plans=22, name="04", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_05.json", min_num_plans=22, name="05", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_06.json", min_num_plans=22, name="06", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_07.json", min_num_plans=22, name="07", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_08.json", min_num_plans=22, name="08", dataset_name="200D"),
    FileInstance(path="foodchain/200_deliveries_09.json", min_num_plans=22, name="09", dataset_name="200D"),
])

n500_DATASET = Dataset(name='500D', instances=[
    FileInstance(path="foodchain/500_deliveries_00.json", min_num_plans=56, name="00", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_01.json", min_num_plans=56, name="01", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_02.json", min_num_plans=56, name="02", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_03.json", min_num_plans=56, name="03", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_04.json", min_num_plans=56, name="04", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_05.json", min_num_plans=56, name="05", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_06.json", min_num_plans=56, name="06", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_07.json", min_num_plans=56, name="07", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_08.json", min_num_plans=56, name="08", dataset_name="500D"),
    FileInstance(path="foodchain/500_deliveries_09.json", min_num_plans=56, name="09", dataset_name="500D"),
])
