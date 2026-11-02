#pragma once

#include "Command.h"
#include "Repository.h"

// Command to perform a 3-way merge from another branch into the current checked out branch.
class MergeCommand : public Command {
private:
    Repository& repo_;

    // Finds the latest common ancestor commit between two branch tips
    std::string findCommonAncestor(const std::string& commit1, const std::string& commit2);

public:
    // Constructs the merge command bound to the target repository
    explicit MergeCommand(Repository& repo);

    // Executes 3-way merge logic
    void execute(const std::vector<std::string>& args) override;
};
