## Requirements for PRs to the SSO-Dashboard.

> Note in order to land a PR you must conform to the requirements outlined in https://github.com/mozilla-iam/mozilla-iam/blob/master/GitHub-Security-Settings.md

Branch Protection Rules on master, and production branches are set as follows:
    Protect this branch
    Require pull request reviews before merging
    Require signed commits
    Include administrators
    Restrict who can push to this branch
        Include the teams which should be able to affect code (i.e. write, commit, push code)
        Do NOT include the teams that may not (such as issue managers, bots, etc.)

NOTE: "Restrict who can push to this branch" is effectively the control by which you may allow specific teams to write issues without being able to change code. This does not prevent these teams from contributing through pull-requests. It prevents these teams from merging code.
