#include <iostream>
#include <memory>
#include <map>
#include <vector>
#include <string>
#include <stdexcept>
#include "Repository.h"
#include "InitCommand.h"
#include "AddCommand.h"
#include "CommitCommand.h"
#include "LogCommand.h"
#include "BranchCommand.h"
#include "CheckoutCommand.h"
#include "MergeCommand.h"
#include "ResetCommand.h"
#include "VcsExceptions.h"
#include "Templates.h"

// Prints the usage instructions and supported commands
inline void printHelp() {
    std::cout << "Usage: branchlite <command> [<args>]\n\n"
              << "Available commands:\n"
              << "   init       Create an empty BranchLite repository\n"
              << "   add        Add file contents to the staging area\n"
              << "   commit     Record changes to the repository\n"
              << "   log        Show commit logs\n"
              << "   branch     List or create branches\n"
              << "   checkout   Switch branches and restore working tree\n"
              << "   merge      Perform a three-way merge from another branch\n"
              << "   reset      Move branch pointer back to previous commit (keep files)\n";
}

// Application entry point that registers and dispatches CLI commands.
// Demonstrates: Command-line arguments, Exception handling with multiple catch blocks,
// Pointers to base class, Dynamic dispatch, Template usage, and Operator overloading.
int main(int argc, char* argv[]) {
    // Check command-line arguments (Unit 5 requirement)
    if (argc < 2) {
        printHelp();
        return 1;
    }

    std::string commandName = argv[1];
    if (commandName == "--help" || commandName == "-h") {
        printHelp();
        return 0;
    }

    try {
        Repository repo;

        // Command dispatcher map demonstrating polymorphism and unique_ptr ownership
        std::map<std::string, std::unique_ptr<Command>> commands;
        commands["init"] = std::make_unique<InitCommand>(repo);
        commands["add"] = std::make_unique<AddCommand>(repo);
        commands["commit"] = std::make_unique<CommitCommand>(repo);
        commands["log"] = std::make_unique<LogCommand>(repo);
        commands["branch"] = std::make_unique<BranchCommand>(repo);
        commands["checkout"] = std::make_unique<CheckoutCommand>(repo);
        commands["merge"] = std::make_unique<MergeCommand>(repo);
        commands["reset"] = std::make_unique<ResetCommand>(repo);

        auto it = commands.find(commandName);
        if (it == commands.end()) {
            std::cerr << "branchlite: '" << commandName << "' is not a branchlite command. See 'branchlite --help'.\n";
            return 1;
        }

        std::vector<std::string> args;
        for (int i = 2; i < argc; ++i) {
            args.emplace_back(argv[i]);
        }

        // Polymorphic invocation via Base Class pointer (Command*)
        Command* cmdPtr = it->second.get();
        cmdPtr->execute(args);

    } catch (const VcsExceptions::RepositoryNotInitializedException& ex) {
        // Multiple catch block: Specific custom exception (Unit 4 requirement)
        std::cerr << "Repository Error: " << ex.what() << "\n";
        return 1;
    } catch (const VcsExceptions::EmptyStagingAreaException& ex) {
        // Multiple catch block: Empty staging exception
        std::cerr << "Staging Error: " << ex.what() << "\n";
        return 1;
    } catch (const VcsExceptions::VcsException& ex) {
        // Catching base of custom exception hierarchy (Unit 4: Exception and Inheritance)
        std::cerr << "BranchLite Error: " << ex.what() << "\n";
        return 1;
    } catch (const std::exception& ex) {
        // Catch-all standard exceptions
        std::cerr << "Standard Exception: " << ex.what() << "\n";
        return 1;
    } catch (...) {
        // Catch-all block for unknown exceptions (Unit 4 requirement)
        std::cerr << "Unknown catastrophic error occurred.\n";
        return 1;
    }

    return 0;
}
