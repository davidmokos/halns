package solver

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"testing"
)

func dummyInstance(name string) *VRPInstance {
	file, _ := ioutil.ReadFile("../instances/" + name + ".json")
	vrpInstanceInterface := VRPInstanceInterface{}
	if err := json.Unmarshal(file, &vrpInstanceInterface); err != nil {
		return nil
	}
	instance := CreateInstance(vrpInstanceInterface)
	globalInstance = instance
	return instance
}

func saveSolution(solution *Solution, name string) {
		vrpSolutionJson, err := json.Marshal(solution.ToSolutionInterface())
		if err != nil {
			fmt.Println(err.Error())
			return
		}
		err = ioutil.WriteFile("../solutions/" + name + ".json", vrpSolutionJson, 0644)
		if err != nil {
			fmt.Println(err.Error())
		}
}

func ExamplePlanIterator() {
	instance := dummyInstance("medium")
	solution := DummySolution()

	it := NewPlanIterator(
		solution.Plans[0],
		instance,
		0,
		&PlanInsertion{
			request: solution.Plans[1].Actions[0].Request,
			pickIdx: 0,
			dropIdx: 3,
		},
	)

	actions := make([]*Action, 0)
	for it.HasNext() {
		a := it.Next()
		actions = append(actions, a)
	}

	fmt.Printf("%s", actions)
	// Output: [0 5 4 18 19 6 20 8 22 10 24 12 26 14 28 16 30 2]
}

func TestHALNS(t *testing.T) {
	data := fmt.Sprintf("50_deliveries_%02d", 0)
	instance := dummyInstance(data)
	instance.TimeLimit = 180
	planner := HALNS{}
	solution, err := planner.Solve(instance)
	if err != nil {
		fmt.Println(err)
		return
	}
	fmt.Println(solution)
}
