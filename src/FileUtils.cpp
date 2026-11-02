#include "FileUtils.h"
#include "VcsExceptions.h"
#include <fstream>
#include <sstream>
#include <chrono>
#include <ctime>
#include <iomanip>

namespace FileUtils {

// Reads and returns the entire contents of a file as a string
std::string readFile(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::in | std::ios::binary);
    if (!file.is_open()) {
        throw VcsExceptions::FileNotFoundVcsException(path.string());
    }
    return std::string((std::istreambuf_iterator<char>(file)),
                        std::istreambuf_iterator<char>());
}

// Writes a string content into the target file, overwriting existing content
void writeFile(const std::filesystem::path& path, const std::string& content) {
    std::ofstream file(path, std::ios::out | std::ios::binary);
    if (!file.is_open()) {
        throw VcsExceptions::VcsException("Cannot write to file: " + path.string());
    }
    file << content;
}

// Trims leading and trailing whitespace and newline characters from a string
std::string trim(const std::string& str) {
    const std::string whitespace = " \t\r\n";
    const auto start = str.find_first_not_of(whitespace);
    if (start == std::string::npos) {
        return "";
    }
    const auto end = str.find_last_not_of(whitespace);
    return str.substr(start, end - start + 1);
}

// Returns the current system timestamp in 'YYYY-MM-DD HH:MM:SS' format
std::string currentTimestamp() {
    auto now = std::chrono::system_clock::now();
    std::time_t tt = std::chrono::system_clock::to_time_t(now);
    std::tm tm{};
#if defined(_WIN32)
    localtime_s(&tm, &tt);
#else
    localtime_r(&tt, &tm);
#endif
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

} // namespace FileUtils
