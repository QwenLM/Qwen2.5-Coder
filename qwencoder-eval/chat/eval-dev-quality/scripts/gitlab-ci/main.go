package main

import (
	"os"
	"strings"

	"github.com/zimmski/osutil"

	"github.com/symflower/eval-dev-quality/tools"
)

func main() {
	f, err := os.OpenFile(os.Getenv("GITHUB_ENV"), os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0600)
	if err != nil {
		panic(err)
	}
	defer func() {
		if err := f.Close(); err != nil {
			panic(err)
		}
	}()

	installPath, err := tools.InstallPathDefault()
	if err != nil {
		panic(err)
	}
	if _, err = f.WriteString(osutil.EnvironmentPathIdentifier + "=" + strings.Join([]string{installPath, os.Getenv(osutil.EnvironmentPathIdentifier)}, string(os.PathListSeparator))); err != nil {
		panic(err)
	}
}
