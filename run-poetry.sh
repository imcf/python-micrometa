#!/bin/bash

set -e

cd "$(dirname "$0")"

STATUS=$(git status --porcelain)

if [ -n "$STATUS" ]; then
    echo "===================================================================="
    echo "=============== ERROR: repository unclean, stopping! ==============="
    echo "===================================================================="
    echo
    git status
    echo
    echo "===================================================================="
    echo "=============== ERROR: repository unclean, stopping! ==============="
    echo "===================================================================="
    exit 1
fi

### clean up old poetry artifacts:
rm -rf dist/

### parse the version from 'pom.xml':
PACKAGE_VERSION=$(xmlstarlet sel --template -m _:project -v _:version pom.xml)
PACKAGE_NAME=$(xmlstarlet sel --template -m _:project -v _:artifactId pom.xml)
PACKAGE_DIR="src/${PACKAGE_NAME#python-}"  # strip 'python-' prefix if present

echo "Package version from POM: [$PACKAGE_VERSION]"
### make sure to have a valid Python package version:
case $PACKAGE_VERSION in
*-SNAPSHOT*)
    PACKAGE_VERSION=${PACKAGE_VERSION/-SNAPSHOT/}
    ### calculate the distance to the last release tag:
    LAST_TAG=$(git tag --list "${PACKAGE_NAME}-*" | sort | tail -n1)
    # echo "Last git tag: '$LAST_TAG'"
    COMMITS_SINCE=$(git rev-list "${LAST_TAG}..HEAD" | wc -l)
    # echo "Nr of commits since last tag: $COMMITS_SINCE"
    HEAD_ID=$(git rev-parse --short HEAD)
    # echo "HEAD commit hash: $HEAD_ID"
    PACKAGE_VERSION="${PACKAGE_VERSION}.dev${COMMITS_SINCE}+${HEAD_ID}"
    ;;
esac

echo "Using Python package version: [$PACKAGE_VERSION]"

### put the version into the project file and the package source:
sed -i "s/\${project.version}/${PACKAGE_VERSION}/" pyproject.toml
sed -i "s/\${project.version}/${PACKAGE_VERSION}/" "${PACKAGE_DIR}/__init__.py"

### now call poetry with the given parameters:
poetry "$@"

### clean up the moved source tree and restore the previous state:
git restore pyproject.toml
git restore "${PACKAGE_DIR}/__init__.py"
