package solver

import "fmt"

type Request struct {
	IsPartial bool
	Pickup    *Action
	Drop      *Action
	Courier      int
}

func (r *Request) String() string {
	if r.IsPartial {
		return fmt.Sprintf("(c%d).->%d", r.Courier, r.Drop.Node)
	} else {
		return fmt.Sprintf("%d->%d", r.Pickup.Node, r.Drop.Node)
	}
}
