#include "Repository.h"
#include "FileUtils.h"
#include "Hash.h"
#include "VcsExceptions.h"
#include <utility>
#include <iostream>
#include <algorithm>

// Discovers the repository root by walking up from the working directory
std::filesystem::path Repository::findRepositoryRoot() {
    std::filesystem::path current = std::filesystem::current_path();
    while (true) {
        if (std::filesystem::exists(current / ".branchlite")) {
            return current;
        }
        if (!current.has_parent_path() || current.parent_path() == current) {
            break;
        }
        current = current.parent_path();
    }
    return std::filesystem::current_path();
}

// Constructs a Repository instance associated with a root directory
Repository::Repository(std::filesystem::path rootDir)
    : rootDir_(std::move(rootDir)) {}

// Returns the root directory path of the repository
const std::filesystem::path& Repository::getRootDir() const {
    return rootDir_;
}

// Returns the path to the '.branchlite' metadata directory
std::filesystem::path Repository::getBranchLiteDir() const {
    return rootDir_ / ".branchlite";
}

// Returns the path to the 'objects' storage directory
std::filesystem::path Repository::getObjectsDir() const {
    return getBranchLiteDir() / "objects";
}

// Returns the path to the 'commits' storage directory
std::filesystem::path Repository::getCommitsDir() const {
    return getBranchLiteDir() / "commits";
}

// Returns the path to the 'branches' directory
std::filesystem::path Repository::getBranchesDir() const {
    return getBranchLiteDir() / "branches";
}

// Returns the path to the HEAD reference file
std::filesystem::path Repository::getHeadPath() const {
    return getBranchLiteDir() / "HEAD";
}

// Returns the path to the staging index file
std::filesystem::path Repository::getIndexPath() const {
    return getBranchLiteDir() / "index";
}

// Initializes a new BranchLite repository structure on disk
void Repository::init() {
    if (std::filesystem::exists(getBranchLiteDir())) {
        throw VcsExceptions::RepositoryAlreadyExistsException();
    }

    std::filesystem::create_directories(getObjectsDir());
    std::filesystem::create_directories(getCommitsDir());
    std::filesystem::create_directories(getBranchesDir());

    // HEAD points to the default branch "main" (no newline)
    FileUtils::writeFile(getHeadPath(), "main");

    // Initialize the default branch file (empty because no commits yet)
    FileUtils::writeFile(getBranchesDir() / "main", "");

    // Initialize an empty staging index file
    FileUtils::writeFile(getIndexPath(), "");
}

// Verifies that the current directory is inside an initialized repository and self-heals critical files
void Repository::requireInit() const {
    if (!std::filesystem::exists(getBranchLiteDir()) || !std::filesystem::is_directory(getBranchLiteDir())) {
        throw VcsExceptions::RepositoryNotInitializedException();
    }
    // Self-healing: ensure essential internal structure exists if partially missing
    if (!std::filesystem::exists(getHeadPath())) {
        FileUtils::writeFile(getHeadPath(), "main");
    }
    if (!std::filesystem::exists(getBranchesDir())) {
        std::filesystem::create_directories(getBranchesDir());
    }
    if (!std::filesystem::exists(getBranchesDir() / "main")) {
        FileUtils::writeFile(getBranchesDir() / "main", "");
    }
    if (!std::filesystem::exists(getIndexPath())) {
        FileUtils::writeFile(getIndexPath(), "");
    }
}

// Returns the name of the currently checked out branch from HEAD
std::string Repository::currentBranch() const {
    requireInit();
    if (!std::filesystem::exists(getHeadPath())) {
        FileUtils::writeFile(getHeadPath(), "main");
        return "main";
    }
    std::string branch = FileUtils::trim(FileUtils::readFile(getHeadPath()));
    return branch.empty() ? "main" : branch;
}

// Sets the currently checked out branch name in HEAD
void Repository::setHeadBranch(const std::string& branchName) {
    requireInit();
    FileUtils::writeFile(getHeadPath(), branchName);
}

// Returns the latest commit ID of the current branch (or empty string if none)
std::string Repository::headCommitId() const {
    requireInit();
    return branchCommitId(currentBranch());
}

// Returns the latest commit ID of a specific branch
std::string Repository::branchCommitId(const std::string& branchName) const {
    requireInit();
    std::filesystem::path branchFile = getBranchesDir() / branchName;
    if (!std::filesystem::exists(branchFile)) {
        return "";
    }
    return FileUtils::trim(FileUtils::readFile(branchFile));
}

// Updates a branch reference to point to a new commit ID (defaults to current branch)
void Repository::updateBranchTip(const std::string& commitId, const std::string& branchName) {
    requireInit();
    std::string targetBranch = branchName.empty() ? currentBranch() : branchName;
    FileUtils::writeFile(getBranchesDir() / targetBranch, commitId.empty() ? "" : (commitId + "\n"));
}

// Creates a new branch pointing to the current HEAD commit
void Repository::createBranch(const std::string& branchName) {
    requireInit();
    if (branchExists(branchName)) {
        throw VcsExceptions::VcsException("fatal: A branch named '" + branchName + "' already exists.");
    }
    std::string currentTip = headCommitId();
    updateBranchTip(currentTip, branchName);
}

// Checks if a branch with the given name exists
bool Repository::branchExists(const std::string& branchName) const {
    requireInit();
    return std::filesystem::exists(getBranchesDir() / branchName);
}

// Lists all branches in the repository
std::vector<std::string> Repository::listBranches() const {
    requireInit();
    std::vector<std::string> branches;
    for (const auto& entry : std::filesystem::directory_iterator(getBranchesDir())) {
        if (entry.is_regular_file()) {
            branches.push_back(entry.path().filename().string());
        }
    }
    std::sort(branches.begin(), branches.end());
    return branches;
}

// Stores content as an immutable content-addressed blob in objects/ and returns its hash
std::string Repository::storeBlob(const std::string& content) {
    requireInit();
    std::string hash = Hash::fnv1a(content);
    std::filesystem::path blobPath = getObjectsDir() / hash;
    if (!std::filesystem::exists(blobPath)) {
        FileUtils::writeFile(blobPath, content);
    }
    return hash;
}

// Reads content of an immutable blob from objects/ given its hash
std::string Repository::readBlob(const std::string& hash) const {
    requireInit();
    std::filesystem::path blobPath = getObjectsDir() / hash;
    if (!std::filesystem::exists(blobPath)) {
        throw VcsExceptions::VcsException("fatal: unable to read blob object " + hash);
    }
    return FileUtils::readFile(blobPath);
}

// Saves a commit object to the commits/ directory
void Repository::saveCommit(const Commit& commit) {
    requireInit();
    std::filesystem::path commitPath = getCommitsDir() / commit.getId();
    FileUtils::writeFile(commitPath, commit.serialize());
}

// Loads and deserializes a commit object from disk given its commit ID
Commit Repository::loadCommit(const std::string& commitId) const {
    requireInit();
    std::filesystem::path commitPath = getCommitsDir() / commitId;
    if (!std::filesystem::exists(commitPath)) {
        throw VcsExceptions::VcsException("fatal: commit not found: " + commitId);
    }
    std::string content = FileUtils::readFile(commitPath);
    return Commit::deserialize(commitId, content);
}

// Friend function demonstrating access to private Repository members
void inspectRepositoryInternals(const Repository& repo) {
    std::cout << "[Friend Function]: Repository root path is " << repo.rootDir_.string() << "\n";
}
