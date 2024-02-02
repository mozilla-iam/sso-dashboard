# Development Guide

## Getting Started

In order to develop for the sso-dashboard and run the working dashboard you must install Docker desktop and have a copy of a working envfile.

Make sure that everything is working prior to feature development by running:

 `docker compose up`


 On successful boot of the docker container your shell should say:

 ```shell

Status: Downloaded newer image for 320464205386.dkr.ecr.us-west-2.amazonaws.com/sso-dashboard:16fc657835c5bf7b5a83d1f7a686539507ee94c6
 * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
 * Restarting with inotify reloader
 * Debugger is active!
 * Debugger PIN: 125-948-166

 ```

 From this point the dashboard is running in python-flask live debug mode with the autoreloader on save.  The debugger pin can be used for interactive debugging via the web shell.


## Development Standards

* Use pep8 conventions as they make sense.
* Black formatter with `120` line length wraps.
* Cover new code with adequate test coverage > 80%

## Running the test suite

Tests are written in py.test.  They can be run via:

`make test STAGE=dev`

## Releasing the Dashboard

In the Mozilla IAM account there is a CI/CD pipeline that will release the dev dashboard on merge to master.  For production releases PR master to the _production_ branch.

In the event that CI/CD is broken you may manually build the dashboard and release it using the `Makefile`.  The primary differences between the stage and dev releases are the CLUSTER that the image deployed to using Kubernetes Helm Charts.

```bash
    - make login CLUSTER_NAME=${CLUSTER_NAME}
    - make build COMMIT_SHA=${CODEBUILD_RESOLVED_SOURCE_VERSION}
    - make push DOCKER_DEST=${DOCKER_REPO}:${CODEBUILD_RESOLVED_SOURCE_VERSION}
    - make release STAGE=${DEPLOY_ENV}
```

## Debugging a Failed Release

In order to debug a failed release you will need access to Graylog at `https://graylog.infra.iam.mozilla.com/search` stdout and stderr are shipped there.
