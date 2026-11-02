#pragma once

#include <string>
#include <vector>
#include <filesystem>
#include "Commit.h"
#include "StagingArea.h"

// Encapsulates the BranchLite repository structure, disk storage, and state.
class Repository {
private:
    std::filesystem::path rootDir_;

public:
    // Discovers the repository root by walking up from the working directory
    static std::filesystem::path findRepositoryRoot();

    // Constructs a Repository instance associated with a root directory
    explicit Repository(std::filesystem::path rootDir = findRepositoryRoot());

    // Returns the root directory path of the repository
    const std::filesystem::path& getRootDir() const;

    // Returns the path to the '.branchlite' metadata directory
    std::filesystem::path getBranchLiteDir() const;

    // Returns the path to the 'objects' storage directory
    std::filesystem::path getObjectsDir() const;

    // Returns the path to the 'commits' storage directory
    std::filesystem::path getCommitsDir() const;

    // Returns the path to the 'branches' directory
    std::filesystem::path getBranchesDir() const;

    // Returns the path to the HEAD reference file
    std::filesystem::path getHeadPath() const;

    // Returns the path to the staging index file
    std::filesystem::path getIndexPath() const;

    // Initializes a new BranchLite repository structure on disk
    void init();

    // Verifies that the current directory is inside an initialized repository
    void requireInit() const;

    // Returns the name of the currently checked out branch from HEAD
    std::string currentBranch() const;

    // Sets the currently checked out branch name in HEAD
    void setHeadBranch(const std::string& branchName);

    // Returns the latest commit ID of the current branch (or empty string if none)
    std::string headCommitId() const;

    // Returns the latest commit ID of a specific branch
    std::string branchCommitId(const std::string& branchName) const;

    // Updates a branch reference to point to a new commit ID (defaults to current branch)
    void updateBranchTip(const std::string& commitId, const std::string& branchName = "");

    // Creates a new branch pointing to the current HEAD commit
    void createBranch(const std::string& branchName);

    // Checks if a branch with the given name exists
    bool branchExists(const std::string& branchName) const;

    // Lists all branches in the repository
    std::vector<std::string> listBranches() const;

    // Stores content as an immutable content-addressed blob in objects/ and returns its hash
    std::string storeBlob(const std::string& content);

    // Reads content of an immutable blob from objects/ given its hash
    std::string readBlob(const std::string& hash) const;

    // Saves a commit object to the commits/ directory
    void saveCommit(const Commit& commit);

    // Loads and deserializes a commit object from disk given its commit ID
    Commit loadCommit(const std::string& commitId) const;

    // Friend function demonstrating access to private Repository internals
    friend void inspectRepositoryInternals(const Repository& repo);
};

// Standalone friend function accessing private repo members
void inspectRepositoryInternals(const Repository& repo);
