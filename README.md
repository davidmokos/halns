# Master Thesis
A Hybrid Adaptive Large Neighbourhood Search Algorithm for PDPTW

David Mokoš

## Folder Structure
* **thesis** - contains the pdf of the thesis and the source
* **halns** - contains the implementation of HALNS algorithm written in Go language
* **godeliver-planner** - contains the updated architecture of GoDeliver Planner Service

## How to run

There are two ways how to test the algorithm. The first one is easier to setup and tests only the HALNS algorithm written in Go. The other one executes the planner from the *godeliver-planner* project and can be used to benchmark the planners and to visualize the produced solutions.

### Method 1 - Execute HALNS

This method uses already prepared instances in the Go project. Normally, these instances are created on-demand by the *godeliver-planner* project.

* Download and install Go by following the instructions here: https://golang.org/doc/install
* Open the file `halns/solver/halns_test.go` in your favourite IDE (Tested in Jetbrains GoLand)
* Run the `TestHALNS` function to run the HALNS planner with the test instance. You may edit the test according to your needs. By default, it takes the first instance from the 50 request dataset


### Method 2 - Benchmark Planners and Visualize Solutions

This method simulates the production use of the planning. In GoDeliver, the godeliver-planner is executed via a REST API endpoint from the Replan Runner service (see the architecture described in the thesis). Here, we execute the same methods, but with the already prepared data. 

* Download and install Go by following the instructions here: https://golang.org/doc/install
* Compile the Go code to a C library using the following command:
```bash
cd halns
go build -buildmode=c-shared -o ../godeliver-planner/golang_impl.so
```

* Install the requirements for the godeliver-planner project by running the following. I recommend using a virtual environment or conda.
```bash
cd godeliver-planner
pip install -r requirements.txt
pip install -r dev_requirements.txt
```

* Go to the following file:

```bash
cd godeliver-planner/benchmarking/evaluation/benchmark_evaluator.py
```

* Run the `run_benchmarking()` function to execute all planning algorithms against the evaluation dataset. With every produced solution, the visualization of the solution should automatically open as a new browser window. Also, the metrics are automatically pushed to our Firestore database. To properly work with Firestore, you need to put your Firebase private key into `godeliver-planner/config/godeliver-benchmarking-firebase-key.json`. To try our, please contact me.

* To visualize the metrics uploaded to the Firestore database, run the following command from your virtual environment:
```bash
streamlit run benchmarking_app.py
```