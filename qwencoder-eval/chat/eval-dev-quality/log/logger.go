package log

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"maps"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"sync"
	"time"

	pkgerrors "github.com/pkg/errors"
	"github.com/zimmski/osutil/bytesutil"
)

// AttributeKey defines a key for attributes handed to the structural logger.
type AttributeKey string

const (
	AttributeKeyArtifact   AttributeKey = "Artifact"
	AttributeKeyLanguage                = "Language"
	AttributeKeyModel                   = "Model"
	AttributeKeyRepository              = "Repository"
	AttributeKeyResultPath              = "ResultPath"
	AttributeKeyRun                     = "Run"
	AttributeKeyTask                    = "Task"
)

// Attribute returns a logging attribute.
func Attribute(key AttributeKey, value any) (attribute slog.Attr) {
	return slog.Any(string(key), value)
}

// Flags defines how log messages should be printed.
type Flags int

const (
	FlagMessageOnly = 0
	FlagDate        = 1 << iota
	FlagTime
	FlagStandard = FlagDate | FlagTime
)

var (
	// openLogFiles holds the files that were opened by some logger.
	openLogFiles      []*os.File
	openLogFilesMutex sync.Mutex
)

func addOpenLogFile(file *os.File) {
	openLogFilesMutex.Lock()
	defer openLogFilesMutex.Unlock()

	openLogFiles = append(openLogFiles, file)
}

// CloseOpenLogFiles closes the files that were opened by some logger.
func CloseOpenLogFiles() {
	openLogFilesMutex.Lock()
	defer openLogFilesMutex.Unlock()

	for _, logFile := range openLogFiles {
		logFile.Close()
	}

	openLogFiles = nil
}

// Logger holds a logger to log to.
type Logger struct {
	*slog.Logger
}

// newLoggerWithWriter instantiate a logger with a writer.
func newLoggerWithWriter(writer io.Writer, flags Flags) *Logger {
	handler := newSpawningHandler(writer, flags)
	handler.logFileSpawners = defaultLogFileSpawners

	return &Logger{
		Logger: slog.New(handler),
	}
}

// SetFlags sets the flags defining how log messages should be printed.
func (l *Logger) SetFlags(flags Flags) {
	if spawningHandler, ok := l.Handler().(*spawningHandler); ok {
		spawningHandler.flags = flags
	} else {
		l.Error("Could not set flags of handler")
	}
}

// With returns a Logger that includes the given attributes in each output operation.
func (l *Logger) With(key AttributeKey, value any) *Logger {
	return &Logger{
		Logger: l.Logger.With(string(key), value),
	}
}

// Print logs the given message at the "info" level.
func (l *Logger) Print(message string) {
	l.Logger.Info(message)
}

// Printf logs the given message at the "info" level.
func (l *Logger) Printf(format string, args ...any) {
	l.Logger.Info(fmt.Sprintf(format, args...))
}

// PrintWith logs the given message at the "info" level.
func (l *Logger) PrintWith(message string, args ...any) {
	l.Logger.Info(message, args...)
}

// Panicf is equivalent to "Printf" followed by a panic.
func (l *Logger) Panicf(format string, args ...any) {
	message := fmt.Sprintf(format, args...)
	l.Logger.Info(message)

	panic(message)
}

// Panic is equivalent to "Print" followed by a panic.
func (l *Logger) Panic(message string) {
	l.Logger.Info(message)

	panic(message)
}

// Fatal is equivalent to "Print" followed by a "os.Exit(1)".
func (l *Logger) Fatal(v ...any) {
	l.Logger.Info(fmt.Sprint(v...))

	os.Exit(1)
}

// Writer returns a writer for writing to the logging output destination.
func (l *Logger) Writer() (writer io.Writer) {
	return &handlerWriter{
		handler: l.Handler(),
	}
}

// Buffer returns a logger that writes to a buffer.
func Buffer() (buffer *bytesutil.SynchronizedBuffer, logger *Logger) {
	buffer = new(bytesutil.SynchronizedBuffer)
	logger = newLoggerWithWriter(buffer, FlagStandard)

	return buffer, logger
}

// File returns a logger that writes to a file.
func File(path string) (logger *Logger, loggerClose func(), err error) {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return nil, nil, pkgerrors.WithStack(err)
	}

	file, err := os.OpenFile(path, os.O_APPEND|os.O_RDWR|os.O_CREATE, 0644)
	if err != nil {
		return nil, nil, pkgerrors.WithStack(err)
	}
	loggerClose = func() {
		if err := file.Close(); err != nil {
			panic(err)
		}
	}

	logger = newLoggerWithWriter(file, FlagStandard)

	return logger, loggerClose, nil
}

// STDOUT returns a logger that writes to STDOUT.
func STDOUT() (logger *Logger) {
	return newLoggerWithWriter(os.Stdout, FlagStandard)
}

// newLogWriter returns a logger that writes to a file and to the parent logger at the same time.
func newLogWriter(parent io.Writer, filePath string) (writer io.Writer, err error) {
	file, err := openLogFile(filePath)
	if err != nil {
		return nil, err
	}
	addOpenLogFile(file)

	writer = io.MultiWriter(parent, file)

	return writer, nil
}

// openLogFile opens the given file and creates it if necessary.
func openLogFile(filePath string) (file *os.File, err error) {
	if err := os.MkdirAll(filepath.Dir(filePath), 0755); err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	file, err = os.OpenFile(filePath, os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	if err != nil {
		return nil, pkgerrors.WithStack(err)
	}

	return file, nil
}

// spawningHandler is a structural logging handler which spawns a new log file if one of the given log file spawners triggers.
type spawningHandler struct {
	// writer holds the writer to write the output.
	writer io.Writer

	// attributes holds the attributes handed to the logger.
	attributes map[AttributeKey]string

	// logFileSpawners holds the spawners responsible for spawning a new log file.
	logFileSpawners []logFileSpawner

	// flags holds the flags deciding which fields are logged.
	flags Flags
}

// newSpawningHandler returns a new spawning handler.
func newSpawningHandler(writer io.Writer, flags Flags) *spawningHandler {
	return &spawningHandler{
		writer: writer,

		attributes: map[AttributeKey]string{},

		flags: flags,
	}
}

// Clone returns a copy of the object.
func (h *spawningHandler) Clone() (clone *spawningHandler) {
	return &spawningHandler{
		writer: h.writer,

		attributes: maps.Clone(h.attributes),

		logFileSpawners: slices.Clone(h.logFileSpawners),

		flags: h.flags,
	}
}

var _ slog.Handler = (*spawningHandler)(nil)

// Enabled reports whether the handler handles records at the given level.
func (h *spawningHandler) Enabled(ctx context.Context, level slog.Level) bool {
	return true
}

// Handle handles the Record.
func (h *spawningHandler) Handle(ctx context.Context, record slog.Record) (err error) {
	writer := h.writer
	attributes := maps.Clone(h.attributes)
	record.Attrs(func(attribute slog.Attr) bool {
		attributes[AttributeKey(attribute.Key)] = attribute.Value.String()

		return true
	})
	for _, spawner := range artifactLogFileSpawners {
		if !spawner.NeedsSpawn(attributes) {
			continue
		}

		logFilePath := spawner.FilePath(attributes)
		writer, err = newLogWriter(writer, logFilePath)
		if err != nil {
			return err
		}
	}

	if h.flags&FlagDate != 0 {
		fmt.Fprint(writer, record.Time.Format("2006/01/02"))
		fmt.Fprint(writer, " ")
	}
	if h.flags&FlagTime != 0 {
		fmt.Fprint(writer, record.Time.Format("15:04:05"))
		fmt.Fprint(writer, " ")
	}

	fmt.Fprintln(writer, record.Message)

	return nil
}

// WithAttrs returns a new Handler whose attributes consist of both the receiver's attributes and the arguments.
// The Handler owns the slice: it may retain, modify or discard it.
func (h *spawningHandler) WithAttrs(attributes []slog.Attr) slog.Handler {
	// Collect attributes.
	for _, attribute := range attributes {
		h.attributes[AttributeKey(attribute.Key)] = attribute.Value.String()
	}

	newHandler := h.Clone()

	// Check if we need to spawn a new log file.
	for i, spawner := range h.logFileSpawners {
		if !spawner.NeedsSpawn(h.attributes) {
			continue
		}

		logFilePath := spawner.FilePath(h.attributes)
		writer, err := newLogWriter(h.writer, logFilePath)
		if err != nil {
			fmt.Fprintf(h.writer, "ERROR: cannot create new handler: %s\n", err.Error())

			continue
		}

		logMessage := fmt.Sprintf("Spawning new log file at %s", logFilePath)
		h.Handle(context.Background(), slog.NewRecord(time.Now(), slog.LevelInfo, logMessage, 0))

		newHandler.writer = writer
		newHandler.logFileSpawners = slices.Delete(newHandler.logFileSpawners, i, i+1) // The currently triggered log file spawner must not be part of the new handler as it would trigger again and again.

		return newHandler
	}

	return newHandler
}

// WithGroup returns a new Handler with the given group appended to the receiver's existing groups.
func (h *spawningHandler) WithGroup(string) slog.Handler {
	return h
}

// handlerWriter is an io.Writer that calls a Handler.
type handlerWriter struct {
	handler slog.Handler
}

var _ io.Writer = (*handlerWriter)(nil)

// Write writes the given bytes to the underlying data stream.
func (w *handlerWriter) Write(buffer []byte) (int, error) {
	// Remove final newline.
	originalLength := len(buffer) // Report that the entire buf was written.
	if len(buffer) > 0 && buffer[len(buffer)-1] == '\n' {
		buffer = buffer[:len(buffer)-1]
	}

	var pc uintptr
	record := slog.NewRecord(time.Now(), slog.LevelInfo, string(buffer), pc)

	return originalLength, w.handler.Handle(context.Background(), record)
}

var defaultLogFileSpawners = []logFileSpawner{
	logFileSpawner{
		NeededAttributes: []AttributeKey{
			AttributeKeyResultPath,
		},
		FilePath: func(attributes map[AttributeKey]string) string {
			return filepath.Join(attributes[AttributeKeyResultPath], "evaluation.log")
		},
	},
	logFileSpawner{
		NeededAttributes: []AttributeKey{
			AttributeKeyResultPath,

			AttributeKeyLanguage,
			AttributeKeyModel,
			AttributeKeyRepository,
			AttributeKeyTask,
		},
		FilePath: func(attributes map[AttributeKey]string) string {
			resultPath := attributes[AttributeKeyResultPath]
			modelID := attributes[AttributeKeyModel]
			languageID := attributes[AttributeKeyLanguage]
			repositoryName := attributes[AttributeKeyRepository]
			taskIdentifier := attributes[AttributeKeyTask]

			return filepath.Join(resultPath, taskIdentifier, CleanModelNameForFileSystem(modelID), languageID, repositoryName, "evaluation.log")
		},
	},
}

var artifactLogFileSpawners = []logFileSpawner{
	logFileSpawner{
		NeededAttributes: []AttributeKey{
			AttributeKeyResultPath,

			AttributeKeyArtifact,
			AttributeKeyLanguage,
			AttributeKeyModel,
			AttributeKeyRepository,
			AttributeKeyRun,
			AttributeKeyTask,
		},
		FilePath: func(attributes map[AttributeKey]string) string {
			resultPath := attributes[AttributeKeyResultPath]
			modelID := attributes[AttributeKeyModel]
			languageID := attributes[AttributeKeyLanguage]
			repositoryName := attributes[AttributeKeyRepository]
			taskIdentifier := attributes[AttributeKeyTask]
			run := attributes[AttributeKeyRun]
			artifact := attributes[AttributeKeyArtifact]

			return filepath.Join(resultPath, taskIdentifier, CleanModelNameForFileSystem(modelID), languageID, repositoryName, fmt.Sprintf("%s-%s.log", artifact, run))
		},
	},
}

// logFileSpawner defines when a new log file is spawned.
type logFileSpawner struct {
	// NeededAttributes holds the list of attributes that need to be set in order to spawn a new log file.
	NeededAttributes []AttributeKey
	// FilePath is called if all needed attributes are set and returns the file path for the new log file.
	FilePath func(attributes map[AttributeKey]string) string
}

// NeedsSpawn returns if a new log file has to be spawned.
func (s logFileSpawner) NeedsSpawn(attributes map[AttributeKey]string) bool {
	for _, attributeKey := range s.NeededAttributes {
		if value := attributes[attributeKey]; value == "" {
			return false
		}
	}

	return true
}

var cleanModelNameForFileSystemReplacer = strings.NewReplacer(
	"/", "_",
	"\\", "_",
	":", "_",
)

// CleanModelNameForFileSystem cleans a model name to be useable for directory and file names on the file system.
func CleanModelNameForFileSystem(modelName string) (modelNameCleaned string) {
	return cleanModelNameForFileSystemReplacer.Replace(modelName)
}
