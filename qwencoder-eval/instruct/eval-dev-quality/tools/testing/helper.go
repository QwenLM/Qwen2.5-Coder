package toolstesting

import "testing"

// NewMockToolNamed returns a new mocked tool with ID and binary path already configured.
func NewMockToolNamed(t *testing.T, name string) *MockTool {
	mock := NewMockTool(t)
	mock.On("ID").Return(name).Maybe()
	mock.On("BinaryPath").Return(name).Maybe()

	return mock
}
