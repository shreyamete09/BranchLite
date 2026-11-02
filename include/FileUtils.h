#pragma once

#include <string>
#include <filesystem>

namespace FileUtils {

// Reads and returns the entire contents of a file as a string.
std::string readFile(const std::filesystem::path& path);

// Writes a string content into the target file, overwriting existing content.
void writeFile(const std::filesystem::path& path, const std::string& content);

// Trims leading and trailing whitespace and newline characters from a string.
std::string trim(const std::string& str);

// Returns the current system timestamp in 'YYYY-MM-DD HH:MM:SS' format.
std::string currentTimestamp();

} // namespace FileUtils
