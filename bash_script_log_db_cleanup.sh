echo "Getting Configurations..."
BASE_LOG_FOLDER="{{params.DIRECTORIES_TO_DELETE}}"
DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS="{{params.DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS}}"

cleanup() {
    echo "Executing Find Statement: $1"
    FILES_MARKED_FOR_DELETE=`eval $1`
    echo "Process will be Deleting the following File(s)/Directory(s):"
    echo "${FILES_MARKED_FOR_DELETE}"
    echo "Process will be Deleting `echo "${FILES_MARKED_FOR_DELETE}" | \
    grep -v '^$' | wc -l` File(s)/Directory(s)"     \

    if [ "${FILES_MARKED_FOR_DELETE}" != "" ];
    then
        echo "Executing Delete Statement: $2"
        eval $2
        DELETE_STMT_EXIT_CODE=$?
        if [ "${DELETE_STMT_EXIT_CODE}" != "0" ]; then
            echo "Delete process failed with exit code '${DELETE_STMT_EXIT_CODE}'"
            echo "Removing lock file..."
            rm -f """ + str(LOG_CLEANUP_PROCESS_LOCK_FILE) + """
            if [ "${REMOVE_LOCK_FILE_EXIT_CODE}" != "0" ]; then
                echo "Error removing the lock file. Check file permissions.\
                To re-run the DAG, ensure that the lock file has been \
                deleted (""" + ${LOG_CLEANUP_PROCESS_LOCK_FILE} + """)."
                exit ${REMOVE_LOCK_FILE_EXIT_CODE}
            fi
            exit ${DELETE_STMT_EXIT_CODE}
        fi
    else
        echo "WARN: No File(s)/Directory(s) to Delete"
    fi

}

echo "Finished Getting Configurations"
echo "Configurations:"
echo "BASE_LOG_FOLDER:      '${BASE_LOG_FOLDER}'"
echo "DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS:  '${DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS}'"


FIND_STATEMENT="find ${BASE_LOG_FOLDER}/*/* -type f -mtime +${DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS}"
DELETE_STMT="${FIND_STATEMENT} -exec rm -f {} \;"
cleanup "${FIND_STATEMENT}" "${DELETE_STMT}"

FIND_STATEMENT="find ${BASE_LOG_FOLDER}/*/* -type d -empty"
DELETE_STMT="${FIND_STATEMENT} -prune -exec rm -rf {} \;"
cleanup "${FIND_STATEMENT}" "${DELETE_STMT}"

FIND_STATEMENT="find ${BASE_LOG_FOLDER}/* -type d -empty"
DELETE_STMT="${FIND_STATEMENT} -prune -exec rm -rf {} \;"
cleanup "${FIND_STATEMENT}" "${DELETE_STMT}"

echo "Finished Running Cleanup Process"