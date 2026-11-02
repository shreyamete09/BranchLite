#include "CommitCommand.h"
#include "StagingArea.h"
#include "FileUtils.h"
#include "Hash.h"
#include "VcsExceptions.h"
#include <iostream>

// Constructs the commit command bound to the target repository
CommitCommand::CommitCommand(Repository& repo)
    : repo_(repo) {}

// Executes the creation of a new commit with staged changes
void CommitCommand::execute(const std::vector<std::string>& args) {
    repo_.requireInit();

    if (args.size() < 2 || args[0] != "-m") {
        throw VcsExceptions::InvalidCommandArgsException("Usage: branchlite commit -m \"<message>\"");
    }

    std::string message = args[1];
    if (FileUtils::trim(message).empty()) {
        throw VcsExceptions::InvalidCommandArgsException("Aborting commit due to empty commit message.");
    }

    StagingArea stagingArea;
    stagingArea.load(repo_.getIndexPath());

    if (stagingArea.empty()) {
        throw VcsExceptions::EmptyStagingAreaException();
    }

    std::string parentId = repo_.headCommitId();
    std::map<std::string, std::string> commitFiles;

    if (!parentId.empty() && parentId != "-") {
        Commit parentCommit = repo_.loadCommit(parentId);
        commitFiles = parentCommit.getFiles();
    }

    // Overlay staged files on top of parent commit files
    for (const auto& [filepath, hash] : stagingArea.entries()) {
        commitFiles[filepath] = hash;
    }

    std::string timestamp = FileUtils::currentTimestamp();
    std::string parentField = (parentId.empty() || parentId == "-") ? "-" : parentId;

    Commit newCommit("", parentField, timestamp, message, commitFiles);
    std::string commitId = Hash::fnv1a(newCommit.serialize());
    newCommit.setId(commitId);

    repo_.saveCommit(newCommit);
    repo_.updateBranchTip(commitId);

    stagingArea.clear();
    stagingArea.save(repo_.getIndexPath());

    std::string shortHash = commitId.length() >= 7 ? commitId.substr(0, 7) : commitId;
    std::cout << "[" << repo_.currentBranch() << " " << shortHash << "] " << message << "\n";
}
