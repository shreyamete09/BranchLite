# BranchLite VCS 🚀
> **A Lightweight, Object-Oriented Version Control System & Interactive Developer Studio**

![C++17](https://img.shields.io/badge/Language-C%2B%2B17-blue.svg?logo=c%2B%2B&logoColor=white)
![Build](https://img.shields.io/badge/Build-MinGW%20%2F%20GCC-success.svg?logo=gnu&logoColor=white)
![GUI](https://img.shields.io/badge/Web%20GUI-Python%203%20%2B%20TailwindCSS-orange.svg?logo=python&logoColor=white)
![Design Pattern](https://img.shields.io/badge/Architecture-Command%20Pattern-purple.svg)
![Status](https://img.shields.io/badge/Status-Completed%20%26%20Verified-brightgreen.svg)

---

## 📌 1. Project Overview

**BranchLite** is a custom distributed version control system (VCS) designed from the ground up in modern **C++17** to demonstrate core **Object-Oriented Programming (OOP)** principles. Modeled after the architectural fundamentals of Git, BranchLite tracks changes to source files across a directed acyclic graph (DAG) of snapshots.

Instead of relying on third-party version control libraries, BranchLite implements its own:
- **Content-Addressable Object Storage** using 64-bit FNV-1a hashing.
- **Staging Index Management** for atomic change preparation.
- **Branch Pointer System & HEAD Reference Resolution**.
- **Full 3-Way Merge Engine** with common ancestor resolution and conflict marker generation.
- **Interactive Dark-Themed Web Studio GUI** running locally on a Python HTTP bridge for visual demonstration.

This project was built as an academic capstone for a second-semester **Object-Oriented Programming (OOP) Course Project**.

---

## 🏛️ 2. System Architecture

BranchLite is organized into two primary layers:

1. **C++ Core Engine (`branchlite.exe`)**: A high-performance, command-line interface utilizing strict object-oriented modularity. It maintains all disk databases inside a local `.branchlite/` directory.
2. **Developer Studio Web GUI (`gui/`)**: A modern single-page dashboard serving real-time visual commit graphs, interactive staging tables, desktop file uploading, and simulated terminal execution.

```
       +-------------------------------------------------------------+
       |               Developer Studio (Web Browser)                |
       |       Tailwind CSS + SVG Directed Graph + JS Event Loop     |
       +------------------------------+------------------------------+
                                      | HTTP REST APIs (Port 5000)
       +------------------------------v------------------------------+
       |               Python GUI Server (gui/server.py)             |
       |     Endpoints: /api/status, /api/execute, /api/upload       |
       +------------------------------+------------------------------+
                                      | Subprocess Invocation (CLI)
       +------------------------------v------------------------------+
       |                  BranchLite C++17 Engine                     |
       |                   (branchlite.exe)                          |
       +------------------------------+------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                            |                            |
         v                            v                            v
+------------------+         +------------------+         +------------------+
| Objects Storage  |         |  Commits Storage |         | Branches & HEAD  |
| .branchlite/     |         |  .branchlite/    |         | .branchlite/     |
| objects/<hash>   |         |  commits/<hash>  |         | branches/<name>  |
+------------------+         +------------------+         +------------------+
```

---

## ✨ 3. Core Features (Implemented & Verified)

All listed features are implemented in the C++ source code and fully accessible through both the CLI and Web Dashboard:

| Command | Feature Description | Underlying Mechanism |
| :--- | :--- | :--- |
| `init` | Initializes a new repository | Creates `.branchlite/` with `objects/`, `commits/`, `branches/`, and sets `HEAD` to `main`. |
| `add <file>` | Stages file content | Computes 64-bit FNV-1a hash, writes immutable blob to `objects/`, and records entry into `index`. |
| `commit -m <msg>` | Records a snapshot | Bundles staged files, records author date, sets parent commit hash, updates current branch tip, and clears index. |
| `log` | Displays commit timeline | Traverses the commit graph from `HEAD` backward, rendering commit hashes, parents, dates, and messages. |
| `branch [<name>]` | Lists or creates branches | Lists existing branches highlighting the active branch (`* main`), or creates a new pointer at current `HEAD`. |
| `checkout <branch>` | Switches branches | Updates `HEAD` pointer and reconstructs working directory files to match the destination commit snapshot. |
| `merge <branch>` | Performs 3-Way Merge | Uses Breadth-First Search (BFS) to find the Lowest Common Ancestor (LCA); executes fast-forward merges or 3-way merges with conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>>`). |
| `reset` | Safe rollback / undo | Moves the current branch pointer back to the immediate parent commit while keeping working directory files intact. |

---

## 🧩 4. Object-Oriented Programming (OOP) Concepts Demonstrated

BranchLite was intentionally engineered to serve as a comprehensive exhibition of academic OOP principles:

### 1. Classes, Objects, and Encapsulation
- **Data Hiding**: Core classes ([`Repository`](include/Repository.h), [`Commit`](include/Commit.h), [`StagingArea`](include/StagingArea.h)) encapsulate internal state using `private:` and `protected:` access specifiers.
- **Integrity**: Disk operations, raw path manipulators, and hashing routines are safeguarded behind controlled public accessors and mutators.

### 2. Constructors, Destructors & Static Members
- **Constructor Overloading**: [`Commit`](include/Commit.h) implements default constructors, parameterized constructors with default arguments, and explicit copy constructors.
- **Resource Management**: Classes define destructors (`~Commit()`, virtual `~Command() = default;`) ensuring proper lifecycle management.
- **Static Attributes and Methods**: [`Commit`](include/Commit.h) maintains a `static int commitObjectCount_` and `static int getCommitObjectCount()` to track live instance allocations.
- **Explicit `this` Pointer**: Member functions explicitly utilize `this->id_` to disambiguate member variables from parameters.

### 3. Inheritance and Abstract Base Classes
- **Base Command Interface**: [`Command`](include/Command.h) declares an abstract class containing a pure virtual function:
  ```cpp
  virtual void execute(const std::vector<std::string>& args) = 0;
  ```
- **Hierarchical Inheritance**: Eight specialized command classes (`InitCommand`, `AddCommand`, `CommitCommand`, `LogCommand`, `BranchCommand`, `CheckoutCommand`, `MergeCommand`, `ResetCommand`) inherit publicly from `Command`.

### 4. Polymorphism and Dynamic Binding
- **Command Pattern & Dynamic Dispatch**: The CLI dispatcher in [`src/main.cpp`](src/main.cpp) maps string inputs to `std::unique_ptr<Command>`. Commands are executed via base class pointers (`Command* cmdPtr = it->second.get(); cmdPtr->execute(args);`), achieving dynamic run-time polymorphism.

### 5. Operator Overloading
- **Binary Relational Operators**: [`Commit`](include/Commit.h) overloads `operator==` and `operator!=` to compare commit identifiers.
- **Subscript Operator (`operator[]`)**: Both [`StagingArea`](include/StagingArea.h) and [`ObjectRegistry`](include/Templates.h) overload `operator[]` to support clean array/dictionary-like lookups.
- **Stream I/O Operators (`<<` and `>>`)**: Overloaded `operator<<` (insertion) and `operator>>` (extraction) on [`Commit`](include/Commit.h) and [`StagingArea`](include/StagingArea.h) allow idiomatic stream serialization:
  ```cpp
  friend std::ostream& operator<<(std::ostream& os, const Commit& commit);
  friend std::istream& operator>>(std::istream& is, Commit& commit);
  ```

### 6. Friend Functions & Friend Classes
- **Friend Class**: [`Commit`](include/Commit.h) and [`StagingArea`](include/StagingArea.h) grant `friend class Repository;` privilege, enabling clean database persistence without polluting public interfaces.
- **Friend Functions**: Stream operators and diagnostic functions (such as `inspectRepositoryInternals`) are granted friend access.

### 7. Exception Handling & Custom Hierarchy
- **Custom Exceptions**: [`VcsExceptions.h`](include/VcsExceptions.h) implements a standard-compliant exception hierarchy derived from `std::exception`:
  - `VcsException` (Base)
    - `RepositoryNotInitializedException`
    - `RepositoryAlreadyExistsException`
    - `FileNotFoundVcsException`
    - `EmptyStagingAreaException`
    - `InvalidCommandArgsException`
- **Multi-Level Catch Blocks**: `src/main.cpp` demonstrates ordered exception interception (specific custom exceptions $\rightarrow$ generic `VcsException` $\rightarrow$ `std::exception` $\rightarrow$ `catch (...)` ellipsis handler).

### 8. Templates & Generic Programming
- **Class Template**: [`ObjectRegistry<T, MaxDisplay>`](include/Templates.h) demonstrates parameterized types with non-type template parameters (`size_t MaxDisplay = 100`).
- **Function Template & Specialization**: [`formatSummary<T>`](include/Templates.h) demonstrates generic summarization with explicit template specialization for `std::string`.

---

## 📁 5. Project Directory Structure

```
OOPS CP/
│
├── include/                     # C++ Header Files (Class declarations & templates)
│   ├── AddCommand.h             # Staging command declaration
│   ├── BranchCommand.h          # Branch listing and creation
│   ├── CheckoutCommand.h        # Branch switching and working tree restoration
│   ├── Command.h                # Abstract Base Command class (Command Pattern)
│   ├── Commit.h                 # Commit entity (Constructors, operators, friend class)
│   ├── CommitCommand.h          # Snapshot creation command
│   ├── FileUtils.h              # File system helper utilities
│   ├── Hash.h                   # 64-bit FNV-1a hashing function
│   ├── InitCommand.h            # Repository initialization
│   ├── LogCommand.h             # Commit DAG traversal
│   ├── MergeCommand.h           # 3-Way merge and LCA algorithm
│   ├── Repository.h             # Repository disk architecture and operations
│   ├── ResetCommand.h           # Undo / branch pointer reset
│   ├── StagingArea.h            # Staging index (operator[], friend class)
│   ├── Templates.h              # Generic class and function templates
│   └── VcsExceptions.h          # Custom exception inheritance hierarchy
│
├── src/                         # C++ Source Files (Implementations)
│   ├── AddCommand.cpp
│   ├── BranchCommand.cpp
│   ├── CheckoutCommand.cpp
│   ├── Commit.cpp
│   ├── CommitCommand.cpp
│   ├── FileUtils.cpp
│   ├── Hash.cpp
│   ├── InitCommand.cpp
│   ├── LogCommand.cpp
│   ├── main.cpp                 # CLI Entry point & polymorphic command dispatcher
│   ├── MergeCommand.cpp
│   ├── Repository.cpp
│   ├── ResetCommand.cpp
│   └── StagingArea.cpp
│
├── gui/                         # Developer Studio Frontend & Bridge
│   ├── index.html               # Responsive dark-theme dashboard (Tailwind CSS)
│   └── server.py                # Python 3 HTTP bridge server (REST endpoints)
│
├── .vscode/                     # Visual Studio Code build configuration
│   ├── c_cpp_properties.json
│   └── tasks.json               # Automated build & GUI launch tasks
│
├── ARCHITECTURE.png             # Architecture and design diagram
├── branchlite.exe               # Compiled C++ executable
├── .gitignore                   # Git ignore specifications
└── README.md                    # Project documentation
```

---

## 🛠️ 6. Technologies Used

- **Core Programming Language**: C++17 (Standard Library, `<filesystem>`, STL maps, vectors, queues, sets).
- **Compiler**: GCC / MinGW (`g++` supporting C++17).
- **GUI Server**: Python 3 standard library (`http.server`, `subprocess`, `json`, `pathlib`).
- **Web Frontend**: HTML5, Modern Vanilla JavaScript, Tailwind CSS (via CDN), Google Fonts (*Inter*, *JetBrains Mono*).
- **Operating System Compatibility**: Windows 10 / 11, Linux, macOS.

---

## 🚀 7. Setup & Execution Instructions

### Prerequisites
1. **C++ Compiler**: MinGW-w64 / GCC with C++17 support.
2. **Python**: Python 3.8+ (for running the optional Developer Studio Web GUI).

---

### Step 1: Compiling the C++ Core
You can compile the executable from the project root using `g++`:

```powershell
g++ -std=c++17 -static -Iinclude src/*.cpp -o branchlite.exe
```

*(If you are using VS Code, simply press `Ctrl + Shift + B` to trigger the preconfigured build task).*

---

### Step 2: Running via the Command-Line Interface (CLI)

Verify the build by requesting the command manual:
```powershell
.\branchlite.exe --help
```

#### Example CLI Workflow Session:
```powershell
# 1. Initialize repository
.\branchlite.exe init

# 2. Stage a file
.\branchlite.exe add sample.txt

# 3. Commit staged changes
.\branchlite.exe commit -m "Initial commit with sample.txt"

# 4. View commit history
.\branchlite.exe log

# 5. Create and switch to a feature branch
.\branchlite.exe branch feature-ui
.\branchlite.exe checkout feature-ui

# 6. Make changes, stage and commit on feature branch
.\branchlite.exe add new_file.txt
.\branchlite.exe commit -m "Added new file on feature branch"

# 7. Switch back to main and merge
.\branchlite.exe checkout main
.\branchlite.exe merge feature-ui
```

---

### Step 3: Launching the Web Developer Studio

To launch the graphical dashboard:

```powershell
python gui/server.py
```

Then open your browser and navigate to:
```
http://localhost:5000
```

#### Dashboard Features:
- **Left Panel (Git Operations)**: Execute `Init`, `Stage`, `Commit`, `Branch`, `Checkout`, `Merge`, and `Reset` with button clicks.
- **Center Panel (Commit Graph)**: Real-time visual DAG timeline displaying commit nodes, parents, authors, and timestamps.
- **Right Panel (File Manager & Staging Area)**: Drag-and-drop file upload from your desktop, inspect staged files, and view workspace contents.
- **Footer**: Integrated simulated terminal reflecting `stdout` and `stderr` from the C++ binary.
- **Reset Button**: One-click "Delete All & Reset Fresh" button to quickly reset state for live classroom demonstrations.

---

## 📊 8. Project Status

| Milestone | Status | Details |
| :--- | :---: | :--- |
| **Object Model Architecture** | ✅ Completed | Clean object-oriented design and design pattern implementation |
| **Storage Engine & Hashing** | ✅ Completed | FNV-1a content hashing and `.branchlite` database integrity |
| **Core VCS Commands** | ✅ Completed | `init`, `add`, `commit`, `log`, `branch`, `checkout`, `merge`, `reset` |
| **3-Way Merge & Conflict Handling** | ✅ Completed | BFS lowest common ancestor and conflict resolution |
| **Web GUI & Bridge** | ✅ Completed | Responsive dark-theme dashboard connected to backend CLI |
| **Test Verification** | ✅ Completed | Verified on Windows PowerShell and modern web browsers |

---

## 👥 Contributors & Academic Context

- **Course**: Object-Oriented Programming (Semester 2)
- **Project Type**: Course Project / Capstone
- **Primary Focus**: Practical application of C++ OOP paradigms, Data Structures (DAG / BFS), and System Design.
