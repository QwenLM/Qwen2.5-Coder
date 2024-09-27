package openaiapi

import (
	"context"
	"fmt"

	pkgerrors "github.com/pkg/errors"
	"github.com/sashabaranov/go-openai"
)

// QueryOpenAIModel queries an OpenAI API model.
func QueryOpenAIAPIModel(ctx context.Context, client *openai.Client, modelIdentifier string, promptText string) (response string, err error) {
	apiResponse, err := client.CreateChatCompletion(
		ctx,
		openai.ChatCompletionRequest{
			Model: modelIdentifier,
			Messages: []openai.ChatCompletionMessage{
				{
					Role:    openai.ChatMessageRoleUser,
					Content: promptText,
				},
			},
		},
	)
	if err != nil {
		return "", pkgerrors.WithStack(err)
	} else if len(apiResponse.Choices) == 0 {
		return "", pkgerrors.WithStack(fmt.Errorf("empty LLM %q response: %+v", modelIdentifier, apiResponse))
	}

	return apiResponse.Choices[0].Message.Content, nil
}
