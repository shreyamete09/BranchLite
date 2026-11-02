#include "BranchCommand.h"
#include "VcsExceptions.h"
#include <iostream>

// Constructs the branch command bound to the target repository
BranchCommand::BranchCommand(Repository& repo)
    : repo_(repo) {}

// Executes branch creation or listing
void BranchCommand::execute(const std::vector<std::string>& args) {
    repo_.requireInit();

    // If no arguments provided: list all branches with asterisk next to current
    if (args.empty()) {
        std::string current = repo_.currentBranch();
        std::vector<std::string> branches = repo_.listBranches();
        for (const auto& branch : branches) {
            if (branch == current) {
                std::cout << "* " << branch << "\n";
            } else {
                std::cout << "  " << branch << "\n";
            }
        }
        return;
    }

    // Branch creation: branchlite branch <name>
    std::string newBranchName = args[0];
    repo_.createBranch(newBranchName);
    std::cout << "Created branch '" << newBranchName << "'\n";
}
