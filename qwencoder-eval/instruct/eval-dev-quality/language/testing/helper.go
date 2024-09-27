package languagetesting

import "testing"

// NewMockLanguageNamed returns a new named mocked language.
func NewMockLanguageNamed(t *testing.T, id string) *MockLanguage {
	m := NewMockLanguage(t)
	m.On("ID").Return(id).Maybe()

	return m
}
