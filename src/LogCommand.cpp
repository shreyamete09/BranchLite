#include "LogCommand.h"
#include <iostream>

// Constructs the log command bound to the target repository
LogCommand::LogCommand(Repository& repo)
    : repo_(repo) {}

// Executes traversing and displaying commits newest-first
void LogCommand::execute(const std::vector<std::string>& /*args*/) {
    repo_.requireInit();

    std::string currentId = repo_.headCommitId();
    if (currentId.empty()) {
        std::cout << "No commits yet on branch " << repo_.currentBranch() << "\n";
        return;
    }

    while (!currentId.empty() && currentId != "-") {
        Commit commit = repo_.loadCommit(currentId);
        // Using stream insertion operator (Unit 5 requirement)
        std::cout << commit << "\n";
        currentId = commit.getParent();
    }
}
