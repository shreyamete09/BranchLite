#include "Commit.h"
#include <sstream>
#include <stdexcept>
#include <utility>

// Initialize static member variable
int Commit::commitObjectCount_ = 0;

// Default constructor
Commit::Commit()
    : id_(""), parent_("-"), parent2_(""), timestamp_(""), message_("") {
    ++commitObjectCount_;
}

// Parameterized constructor initializing all commit attributes
Commit::Commit(std::string id, std::string parent, std::string timestamp,
               std::string message, std::map<std::string, std::string> files,
               std::string parent2)
    : id_(std::move(id)),
      parent_(std::move(parent)),
      parent2_(std::move(parent2)),
      timestamp_(std::move(timestamp)),
      message_(std::move(message)),
      files_(std::move(files)) {
    ++commitObjectCount_;
}

// Copy constructor demonstrating deep copy semantics
Commit::Commit(const Commit& other)
    : id_(other.id_),
      parent_(other.parent_),
      parent2_(other.parent2_),
      timestamp_(other.timestamp_),
      message_(other.message_),
      files_(other.files_) {
    ++commitObjectCount_;
}

// Destructor decrementing static instance count
Commit::~Commit() {
    --commitObjectCount_;
}

// Static member function to retrieve count of active Commit objects
int Commit::getCommitObjectCount() {
    return commitObjectCount_;
}

// Returns the unique 16-character commit hash identifier
const std::string& Commit::getId() const {
    return this->id_; // demonstrating explicit 'this' pointer usage
}

// Sets the unique commit hash identifier
void Commit::setId(const std::string& id) {
    this->id_ = id;
}

// Returns the parent commit identifier (or "-" if initial commit)
const std::string& Commit::getParent() const {
    return parent_;
}

// Returns the second parent commit identifier (for merge commits)
const std::string& Commit::getParent2() const {
    return parent2_;
}

// Sets the second parent commit identifier
void Commit::setParent2(const std::string& parent2) {
    this->parent2_ = parent2;
}

// Checks if this commit is a merge commit
bool Commit::isMerge() const {
    return !parent2_.empty() && parent2_ != "-";
}

// Returns the creation timestamp of the commit
const std::string& Commit::getTimestamp() const {
    return timestamp_;
}

// Returns the commit message describing the snapshot changes
const std::string& Commit::getMessage() const {
    return message_;
}

// Returns the map of tracked files and their corresponding blob hashes
const std::map<std::string, std::string>& Commit::getFiles() const {
    return files_;
}

// Serializes the commit object into the standardized text format
std::string Commit::serialize() const {
    std::ostringstream oss;
    oss << "parent " << (parent_.empty() ? "-" : parent_) << "\n";
    if (!parent2_.empty() && parent2_ != "-") {
        oss << "parent2 " << parent2_ << "\n";
    }
    oss << "time " << timestamp_ << "\n";
    oss << "message " << message_ << "\n";
    oss << "files\n";
    for (const auto& [filename, hash] : files_) {
        oss << hash << " " << filename << "\n";
    }
    return oss.str();
}

// Deserializes a standardized text representation into a Commit object
Commit Commit::deserialize(const std::string& id, const std::string& content) {
    std::istringstream stream(content);
    std::string line;

    std::string parent = "-";
    std::string parent2 = "";
    std::string timestamp;
    std::string message;
    std::map<std::string, std::string> files;

    bool inFilesSection = false;

    while (std::getline(stream, line)) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        if (inFilesSection) {
            if (line.empty()) {
                continue;
            }
            const auto spacePos = line.find(' ');
            if (spacePos != std::string::npos) {
                std::string fileHash = line.substr(0, spacePos);
                std::string fileName = line.substr(spacePos + 1);
                files[fileName] = fileHash;
            }
            continue;
        }

        if (line.rfind("parent ", 0) == 0) {
            parent = line.substr(7);
        } else if (line.rfind("parent2 ", 0) == 0) {
            parent2 = line.substr(8);
        } else if (line.rfind("time ", 0) == 0) {
            timestamp = line.substr(5);
        } else if (line.rfind("message ", 0) == 0) {
            message = line.substr(8);
        } else if (line == "files") {
            inFilesSection = true;
        }
    }

    return Commit(id, parent, timestamp, message, files, parent2);
}

// Operator Overloading: Equality operator (Binary operator)
bool Commit::operator==(const Commit& other) const {
    return this->id_ == other.id_;
}

// Operator Overloading: Inequality operator (Binary operator)
bool Commit::operator!=(const Commit& other) const {
    return !(*this == other);
}

// Stream Insertion Operator overloading (Unit 5 requirement)
std::ostream& operator<<(std::ostream& os, const Commit& commit) {
    os << "commit " << commit.id_;
    if (commit.isMerge()) {
        std::string p1 = commit.parent_.length() >= 7 ? commit.parent_.substr(0, 7) : commit.parent_;
        std::string p2 = commit.parent2_.length() >= 7 ? commit.parent2_.substr(0, 7) : commit.parent2_;
        os << " (Merge: " << p1 << " " << p2 << ")";
    }
    os << "\nDate:   " << commit.timestamp_ << "\n\n"
       << "    " << commit.message_ << "\n";
    return os;
}

// Stream Extraction Operator overloading (Unit 5 requirement)
std::istream& operator>>(std::istream& is, Commit& commit) {
    std::string line;
    std::string content;
    while (std::getline(is, line)) {
        content += line + "\n";
    }
    commit = Commit::deserialize(commit.getId(), content);
    return is;
}
