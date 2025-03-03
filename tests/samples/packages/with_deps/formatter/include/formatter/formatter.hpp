#pragma once
#include <string>

namespace formatter {

/**
 * Simple string formatter that replaces {} placeholders with arguments.
 * Example: format("Hello, {}!", "World") -> "Hello, World!"
 */
std::string format(const std::string& fmt, const std::string& arg1);

/**
 * Overload for two arguments.
 * Example: format("Hello, {}! The year is {}.", "World", 2024)
 */
std::string format(const std::string& fmt, const std::string& arg1, const std::string& arg2);

} // namespace formatter 