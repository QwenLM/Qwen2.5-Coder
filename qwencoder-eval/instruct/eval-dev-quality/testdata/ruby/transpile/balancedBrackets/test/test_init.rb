# Set up coverage.
require "simplecov"
SimpleCov.start do
  add_filter "/test/" # Exclude files in test folder.
end
require "simplecov_json_formatter"
SimpleCov.formatter = SimpleCov::Formatter::JSONFormatter

# Set up minitest.
require "minitest/autorun"
