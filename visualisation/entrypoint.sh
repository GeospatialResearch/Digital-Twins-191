#!/bin/bash

# Used by docker to import environment variables into a docker container without baking them into the image

ROOT_DIR=/app
# Find the list of VITE_ variables in the environment variables
VITE_ENV_VARS=$(printenv | grep -o "VITE_\w*")

echo "Replacing env constants in JS"
echo "Env constants = ${VITE_ENV_VARS}"
for FILE in "$ROOT_DIR"/assets/index-*.js* "$ROOT_DIR"/index.html
do
  echo "Processing $FILE ...";

  for VAR_NAME in $VITE_ENV_VARS;
  do
    # Use variable indirection to lookup the value of the variable
    VAR_VALUE=$(eval "echo \${$VAR_NAME}")
    # Replace all instances of the string $VAR_NAME with $VAR_VALUE, allowing it to fail if it can't find it
    sed -i 's|'"${VAR_NAME}"'|'"${VAR_VALUE}"'|g' $FILE || true
  done
done
echo "Finished processing files for env constants"

echo "Starting nginx server now."
# Run the nginx server
nginx -g 'daemon off;'
