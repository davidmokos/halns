package solver

import (
	"fmt"
)

type ActionType int8

const (
	Pickup ActionType = 0
	Drop   ActionType = 1
	Start  ActionType = 2
	End    ActionType = 3
)

type Action struct {
	TimeWindowList *TimeWindowList
	Node           int
	Type           ActionType
	ServiceTime    int
	Request        *Request
	Demand         int
}

func (a *Action) String() string {
	return fmt.Sprintf("%d", a.Node)
}

func (a *Action) GetNode() int {
	return a.Node
}

func (a *Action) Other() *Action {
	if a.Type == Pickup {
		return a.Request.Drop
	} else if a.Type == Drop && !a.Request.IsPartial {
		return a.Request.Pickup
	}
	return nil
}
