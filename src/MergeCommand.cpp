#include "MergeCommand.h"
#include "StagingArea.h"
#include "FileUtils.h"
#include "Hash.h"
#include "VcsExceptions.h"
#include <iostream>
#include <set>
#include <queue>

// Constructs the merge command bound to the target repository
MergeCommand::MergeCommand(Repository& repo)
    : repo_(repo) {}

// Finds the latest common ancestor commit between two branch tips
std::string MergeCommand::findCommonAncestor(const std::string& commit1, const std::string& commit2) {
    if (commit1.empty() || commit2.empty() || commit1 == "-" || commit2 == "-") {
        return "";
    }

    std::set<std::string> ancestors1;
    std::queue<std::string> q1;
    q1.push(commit1);

    while (!q1.empty()) {
        std::string cur = q1.front();
        q1.pop();
        if (cur.empty() || cur == "-") continue;
        if (ancestors1.find(cur) != ancestors1.end()) continue;
        ancestors1.insert(cur);

        Commit c = repo_.loadCommit(cur);
        if (!c.getParent().empty() && c.getParent() != "-") q1.push(c.getParent());
        if (!c.getParent2().empty() && c.getParent2() != "-") q1.push(c.getParent2());
    }

    std::queue<std::string> q2;
    q2.push(commit2);
    while (!q2.empty()) {
        std::string cur = q2.front();
        q2.pop();
        if (cur.empty() || cur == "-") continue;
        if (ancestors1.find(cur) != ancestors1.end()) {
            return cur; // Found nearest common ancestor
        }
        Commit c = repo_.loadCommit(cur);
        if (!c.getParent().empty() && c.getParent() != "-") q2.push(c.getParent());
        if (!c.getParent2().empty() && c.getParent2() != "-") q2.push(c.getParent2());
    }

    return "";
}

// Executes 3-way merge logic
void MergeCommand::execute(const std::vector<std::string>& args) {
    repo_.requireInit();

    if (args.empty()) {
        throw VcsExceptions::InvalidCommandArgsException("Usage: branchlite merge <branch-name>");
    }

    std::string sourceBranch = args[0];
    std::string targetBranch = repo_.currentBranch();

    if (!repo_.branchExists(sourceBranch)) {
        throw VcsExceptions::VcsException("fatal: branch '" + sourceBranch + "' does not exist.");
    }

    if (sourceBranch == targetBranch) {
        throw VcsExceptions::VcsException("Cannot merge a branch into itself.");
    }

    std::string currentCommitId = repo_.headCommitId();
    std::string sourceCommitId = repo_.branchCommitId(sourceBranch);

    if (sourceCommitId.empty() || sourceCommitId == "-") {
        std::cout << "Already up to date. (Source branch has no commits)\n";
        return;
    }

    if (currentCommitId.empty() || currentCommitId == "-") {
        // Fast-forward to source branch commit directly
        repo_.updateBranchTip(sourceCommitId);
        std::cout << "Fast-forward merge to " << sourceBranch << "\n";
        return;
    }

    if (currentCommitId == sourceCommitId) {
        std::cout << "Already up to date.\n";
        return;
    }

    std::string baseCommitId = findCommonAncestor(currentCommitId, sourceCommitId);

    // If source is already an ancestor of current, nothing to do
    if (baseCommitId == sourceCommitId) {
        std::cout << "Already up to date.\n";
        return;
    }

    // Load file manifests for 3-way merge
    std::map<std::string, std::string> baseFiles;
    if (!baseCommitId.empty() && baseCommitId != "-") {
        baseFiles = repo_.loadCommit(baseCommitId).getFiles();
    }
    std::map<std::string, std::string> currentFiles = repo_.loadCommit(currentCommitId).getFiles();
    std::map<std::string, std::string> sourceFiles = repo_.loadCommit(sourceCommitId).getFiles();

    // Collect all filenames involved across all three snapshots
    std::set<std::string> allFiles;
    for (const auto& [f, _] : baseFiles) allFiles.insert(f);
    for (const auto& [f, _] : currentFiles) allFiles.insert(f);
    for (const auto& [f, _] : sourceFiles) allFiles.insert(f);

    std::map<std::string, std::string> mergedFiles;

    for (const auto& fileName : allFiles) {
        std::string baseHash = baseFiles.count(fileName) ? baseFiles[fileName] : "";
        std::string curHash = currentFiles.count(fileName) ? currentFiles[fileName] : "";
        std::string srcHash = sourceFiles.count(fileName) ? sourceFiles[fileName] : "";

        if (curHash == srcHash) {
            // Both unchanged or both made the exact same change
            if (!curHash.empty()) {
                mergedFiles[fileName] = curHash;
            }
        } else if (curHash == baseHash) {
            // Current didn't change it, source did (or deleted it)
            if (!srcHash.empty()) {
                mergedFiles[fileName] = srcHash;
            }
        } else if (srcHash == baseHash) {
            // Source didn't change it, current did (or deleted it)
            if (!curHash.empty()) {
                mergedFiles[fileName] = curHash;
            }
        } else {
            // Both changed differently: take source version or combine
            mergedFiles[fileName] = srcHash;
        }
    }

    // Materialize merged files into working directory
    for (const auto& [fileName, hash] : mergedFiles) {
        std::string content = repo_.readBlob(hash);
        std::filesystem::path filePath = repo_.getRootDir() / fileName;
        if (filePath.has_parent_path()) {
            std::filesystem::create_directories(filePath.parent_path());
        }
        FileUtils::writeFile(filePath, content);
    }

    // Create merge commit with TWO parents
    std::string timestamp = FileUtils::currentTimestamp();
    std::string message = "Merge branch '" + sourceBranch + "' into " + targetBranch;
    Commit mergeCommit("", currentCommitId, timestamp, message, mergedFiles, sourceCommitId);
    std::string commitId = Hash::fnv1a(mergeCommit.serialize());
    mergeCommit.setId(commitId);

    repo_.saveCommit(mergeCommit);
    repo_.updateBranchTip(commitId);

    // Clear staging area
    StagingArea stagingArea;
    stagingArea.clear();
    stagingArea.save(repo_.getIndexPath());

    std::string shortHash = commitId.length() >= 7 ? commitId.substr(0, 7) : commitId;
    std::cout << "[" << targetBranch << " " << shortHash << "] " << message << "\n";
}
