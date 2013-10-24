Everything in the External/ directory should be built into here. 

* workflow.py checks that this directory is in the user's PATH variable
* workflow.py lists this directory and checks the version of everything without a file extension, it does this by running `$FILENAME --version`
** Versions should be reported as git hashes e.g. e9e1d3c7bbca9d4e981201a324ce503b7e7ca08c
** If the build contains some changes which haven't been checked in yet, then the version string should be the previous HEAD hash, plus +CHANGES (e.g. e9e1d3c7bbca9d4e981201a324ce503b7e7ca08c+CHANGES)
* If the application exits with an error code or doesn't produce a valid hash, workflow.py will report that the tree could not be verified and won't run any tests. 
* If the application reports the wrong hash (e.g not HEAD or HEAD+changes), workflow.py will not run any tests.

