#pragma once

#include "Command.h"
#include "Repository.h"

// Command to display the commit history of the current branch.
class LogCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the log command bound to the target repository.
    explicit LogCommand(Repository& repo);

    // Executes traversing and displaying commits newest-first.
    void execute(const std::vector<std::string>& args) override;
};
