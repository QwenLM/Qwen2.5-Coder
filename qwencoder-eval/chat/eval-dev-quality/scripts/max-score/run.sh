#!/bin/bash

# Usage: script.sh <evaluation-directory>

echo "WRITE TESTS"
echo "java:"
find $1 -path "*/write-tests/*/java/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
echo "ruby:"
find $1 -path "*/write-tests/*/ruby/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
echo "golang:"
find $1 -path "*/write-tests/*/golang/*/*/evaluation.log" | xargs go run scripts/max-score/main.go

echo "TRANSPILE"
echo "java:"
find $1 -path "*/transpile/*/java/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
echo "ruby:"
find $1 -path "*/transpile/*/ruby/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
echo "golang:"
find $1 -path "*/transpile/*/golang/*/*/evaluation.log" | xargs go run scripts/max-score/main.go

echo "CODE REPAIR"
echo "java:"
find $1 -path "*/code-repair/*/java/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
echo "ruby:"
find $1 -path "*/code-repair/*/ruby/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
echo "golang:"
find $1 -path "*/code-repair/*/golang/*/*/evaluation.log" | xargs go run scripts/max-score/main.go
