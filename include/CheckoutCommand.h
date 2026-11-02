#pragma once

#include "Command.h"
#include "Repository.h"

// Command to switch between branches and restore the working tree to the target commit snapshot.
class CheckoutCommand : public Command {
private:
    Repository& repo_;

public:
    // Constructs the checkout command bound to the target repository
    explicit CheckoutCommand(Repository& repo);

    // Executes switching to a target branch
    void execute(const std::vector<std::string>& args) override;
};
