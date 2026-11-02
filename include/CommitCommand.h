#pragma once

#include "Command.h"
#include "Repository.h"

// Command to record staged changes as a new commit snapshot.
class CommitCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the commit command bound to the target repository.
    explicit CommitCommand(Repository& repo);

    // Executes the creation of a new commit with staged changes.
    void execute(const std::vector<std::string>& args) override;
};
