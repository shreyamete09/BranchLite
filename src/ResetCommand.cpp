#include "ResetCommand.h"
#include "VcsExceptions.h"
#include <iostream>

// Constructs the reset command bound to the target repository
ResetCommand::ResetCommand(Repository& repo)
    : repo_(repo) {}

// Executes the undo/reset operation
void ResetCommand::execute(const std::vector<std::string>& /*args*/) {
    repo_.requireInit();

    std::string currentCommitId = repo_.headCommitId();
    if (currentCommitId.empty() || currentCommitId == "-") {
        throw VcsExceptions::VcsException("fatal: cannot reset: no commits exist on current branch.");
    }

    Commit currentCommit = repo_.loadCommit(currentCommitId);
    std::string parentId = currentCommit.getParent();

    if (parentId == "-") {
        // Resetting the initial commit: branch becomes empty
        repo_.updateBranchTip("");
        std::cout << "Reset branch '" << repo_.currentBranch() << "' back before initial commit.\n";
    } else {
        // Move branch tip to parent commit
        repo_.updateBranchTip(parentId);
        std::string shortParent = parentId.length() >= 7 ? parentId.substr(0, 7) : parentId;
        std::cout << "Reset branch '" << repo_.currentBranch() << "' to commit " << shortParent << " (parent commit).\n";
    }
    std::cout << "Working directory files were kept intact.\n";
}
