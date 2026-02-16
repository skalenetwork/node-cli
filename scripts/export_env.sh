DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR=$(dirname $DIR)

export LVMPY_LOG_DIR="$PROJECT_DIR/tests/"
export  HIDE_STREAM_LOG=true 
export TEST_HOME_DIR="$PROJECT_DIR/tests/" 
export GLOBAL_SKALE_DIR="$PROJECT_DIR/tests/etc/skale"
export DOTENV_FILEPATH='tests/test-env'