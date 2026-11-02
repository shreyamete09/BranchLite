#pragma once

#include <string>
#include <map>
#include <filesystem>
#include <iostream>

// Forward declaration
class Repository;

// Manages the staging area (index) where staged changes are tracked before committing.
class StagingArea {
private:
    std::map<std::string, std::string> entries_; // filename -> blob hash

public:
    // Default constructor
    StagingArea() = default;

    // Loads staged file entries from the repository index file
    void load(const std::filesystem::path& indexPath);

    // Saves the currently staged file entries to the repository index file
    void save(const std::filesystem::path& indexPath) const;

    // Adds or updates a staged file with its corresponding content hash
    void add(const std::string& filepath, const std::string& hash);

    // Clears all entries from the staging area
    void clear();

    // Checks whether the staging area has no staged entries
    bool empty() const;

    // Returns count of staged entries
    size_t count() const;

    // Returns a read-only reference to the staged entries map
    const std::map<std::string, std::string>& entries() const;

    // Operator Overloading: Subscript operator for array-like lookup of staged hash
    std::string operator[](const std::string& filename) const;

    // Stream Insertion Operator overloading (Unit 5 requirement)
    friend std::ostream& operator<<(std::ostream& os, const StagingArea& stage);

    // Friend class declaration
    friend class Repository;
};
