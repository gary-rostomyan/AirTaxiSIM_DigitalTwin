## Initializing Submodules

> **Note:** Octomap Server is currently **NOT** a submodule. Because its repository contains multiple modules, and we only need the Octomap Server module.

When you clone this repository for the first time, the submodule directories will be empty. You need to initialize and fetch them using one of these methods:

### Option 1: Clone with submodules (recommended for new clones)
```shell
git clone --recurse-submodules <url-of-this-repository>
```

### Option 2: Initialize after cloning
```shell
# If you've already cloned without --recurse-submodules
git submodule update --init --recursive
```

### Option 3: One-liner for existing clones
```shell
git submodule init && git submodule update --recursive
```

## Keeping Submodules Updated

To update submodules to the latest commit referenced by the main repository:

```shell
git submodule update --recursive
```

To pull the latest changes from submodule remotes:

```shell
git submodule update --remote --recursive
```