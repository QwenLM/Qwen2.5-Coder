package main

import (
	"os"

	"github.com/symflower/eval-dev-quality/cmd/eval-dev-quality/cmd"
	"github.com/symflower/eval-dev-quality/log"
)

func main() {
	cmd.Execute(log.STDOUT(), os.Args[1:])
}
