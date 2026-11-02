#include "CheckoutCommand.h"
#include "StagingArea.h"
#include "FileUtils.h"
#include "VcsExceptions.h"
#include <iostream>

// Constructs the checkout command bound to the target repository
CheckoutCommand::CheckoutCommand(Repository& repo)
    : repo_(repo) {}

// Executes switching to a target branch
void CheckoutCommand::execute(const std::vector<std::string>& args) {
    repo_.requireInit();

    if (args.empty()) {
        throw VcsExceptions::InvalidCommandArgsException("Usage: branchlite checkout <branch-name>");
    }

    std::string targetBranch = args[0];
    if (!repo_.branchExists(targetBranch)) {
        throw VcsExceptions::VcsException("fatal: branch '" + targetBranch + "' not found.");
    }

    std::string currentBranch = repo_.currentBranch();
    if (currentBranch == targetBranch) {
        std::cout << "Already on '" << targetBranch << "'\n";
        return;
    }

    // Determine target commit
    std::string targetCommitId = repo_.branchCommitId(targetBranch);
    std::string currentCommitId = repo_.headCommitId();

    std::map<std::string, std::string> currentFiles;
    if (!currentCommitId.empty() && currentCommitId != "-") {
        Commit curCommit = repo_.loadCommit(currentCommitId);
        currentFiles = curCommit.getFiles();
    }

    std::map<std::string, std::string> targetFiles;
    if (!targetCommitId.empty() && targetCommitId != "-") {
        Commit tgtCommit = repo_.loadCommit(targetCommitId);
        targetFiles = tgtCommit.getFiles();
    }

    // Delete files that exist in current commit but not in target commit
    for (const auto& [fileName, hash] : currentFiles) {
        if (targetFiles.find(fileName) == targetFiles.end()) {
            std::filesystem::path filePath = repo_.getRootDir() / fileName;
            if (std::filesystem::exists(filePath)) {
                std::filesystem::remove(filePath);
            }
        }
    }

    // Overwrite/write files from target commit into working directory
    for (const auto& [fileName, hash] : targetFiles) {
        std::string content = repo_.readBlob(hash);
        std::filesystem::path filePath = repo_.getRootDir() / fileName;
        if (filePath.has_parent_path()) {
            std::filesystem::create_directories(filePath.parent_path());
        }
        FileUtils::writeFile(filePath, content);
    }

    // Clear staging area upon checkout
    StagingArea stagingArea;
    stagingArea.clear();
    stagingArea.save(repo_.getIndexPath());

    // Switch HEAD to target branch
    repo_.setHeadBranch(targetBranch);
    std::cout << "Switched to branch '" << targetBranch << "'\n";
}
