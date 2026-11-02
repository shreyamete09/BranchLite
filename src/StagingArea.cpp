#include "StagingArea.h"
#include "FileUtils.h"
#include <fstream>
#include <sstream>

// Loads staged file entries from the repository index file
void StagingArea::load(const std::filesystem::path& indexPath) {
    entries_.clear();
    if (!std::filesystem::exists(indexPath)) {
        return;
    }

    std::ifstream file(indexPath);
    if (!file.is_open()) {
        return;
    }

    std::string line;
    while (std::getline(file, line)) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
        if (line.empty()) {
            continue;
        }

        const auto spacePos = line.find(' ');
        if (spacePos != std::string::npos) {
            std::string hash = line.substr(0, spacePos);
            std::string filepath = line.substr(spacePos + 1);
            entries_[filepath] = hash;
        }
    }
}

// Saves the currently staged file entries to the repository index file
void StagingArea::save(const std::filesystem::path& indexPath) const {
    std::ostringstream oss;
    for (const auto& [filepath, hash] : entries_) {
        oss << hash << " " << filepath << "\n";
    }
    FileUtils::writeFile(indexPath, oss.str());
}

// Adds or updates a staged file with its corresponding content hash
void StagingArea::add(const std::string& filepath, const std::string& hash) {
    entries_[filepath] = hash;
}

// Clears all entries from the staging area
void StagingArea::clear() {
    entries_.clear();
}

// Checks whether the staging area has no staged entries
bool StagingArea::empty() const {
    return entries_.empty();
}

// Returns count of staged entries
size_t StagingArea::count() const {
    return entries_.size();
}

// Returns a read-only reference to the staged entries map
const std::map<std::string, std::string>& StagingArea::entries() const {
    return entries_;
}

// Operator Overloading: Subscript operator for array-like lookup of staged hash
std::string StagingArea::operator[](const std::string& filename) const {
    auto it = entries_.find(filename);
    if (it != entries_.end()) {
        return it->second;
    }
    return "";
}

// Stream Insertion Operator overloading (Unit 5 requirement)
std::ostream& operator<<(std::ostream& os, const StagingArea& stage) {
    for (const auto& [file, hash] : stage.entries_) {
        os << hash << " " << file << "\n";
    }
    return os;
}
