from airflow import settings
from datetime import timedelta
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import load_only
from airflow.models import Variable, DagRun, Log, XCom, TaskInstance, TaskReschedule, TaskFail, \
    RenderedTaskInstanceFields
from airflow.utils import timezone
from reporting_etl_spark_jobs.utils.env_variables import DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS


# Global variable
now = timezone.utcnow

def db_cleanup_function():
    """
        Description: Delete the records from table for passed data_model based on passed column name
        before DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS days or older than that.
        return: None
    """
    max_date = now() + timedelta(-DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS)
    session = settings.Session()
    DATABASE_OBJECTS = [
        {"airflow_db_model": DagRun,
         "age_check_column": DagRun.execution_date
         },
        {"airflow_db_model": TaskInstance,
         "age_check_column": TaskInstance.queued_dttm
         },
        {"airflow_db_model": Log,
         "age_check_column": Log.dttm
         },
        {"airflow_db_model": XCom,
         "age_check_column": XCom.execution_date
         },
        {"airflow_db_model": TaskReschedule,
         "age_check_column": TaskReschedule.reschedule_date
         },
        {"airflow_db_model": TaskFail,
         "age_check_column": TaskFail.execution_date
         },
        {"airflow_db_model": RenderedTaskInstanceFields,
         "age_check_column": RenderedTaskInstanceFields.execution_date
         }

    ]

    for db_object in DATABASE_OBJECTS:
        airflow_db_model = db_object.get("airflow_db_model")
        age_check_column = db_object.get("age_check_column")
        try:
            query = session.query(airflow_db_model).options(load_only(age_check_column))
            query = query.filter(age_check_column <= max_date, )
            entries_to_delete = query.all()
            print("Table Name :" + str(airflow_db_model.__name__) + "\n" + "Query: " + str(query))
            print("Process will be Deleting " + str(len(entries_to_delete)) + " records")
            query.delete(synchronize_session=False)
            session.commit()
            print("Finished Running Cleanup Process")
        except ProgrammingError as exp:
            print(exp)