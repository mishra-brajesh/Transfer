import airflow
import logging
from airflow import settings
from sqlalchemy.orm import load_only
from airflow.configuration import conf
from datetime import datetime, timedelta
from sqlalchemy.exc import ProgrammingError
from airflow.models import DAG, DagModel, DagRun, Log, XCom, SlaMiss, TaskInstance, Variable
from reporting_etl_spark_jobs.utils.env_variables import DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS
try:
    from airflow.jobs import BaseJob
except Exception as e:
    from airflow.jobs.base_job import BaseJob

try:
    from airflow.utils import timezone
    now = timezone.utcnow
except ImportError:
    now = datetime.utcnow


DATABASE_OBJECTS = [
        {
            "airflow_db_model": BaseJob,
            "age_check_column": BaseJob.latest_heartbeat
        },
        {
            "airflow_db_model": DagRun,
            "age_check_column": DagRun.execution_date
        },
        {
            "airflow_db_model": TaskInstance,
            "age_check_column": TaskInstance.start_date
        },
        {
            "airflow_db_model": Log,
            "age_check_column": Log.dttm
        },
        {
            "airflow_db_model": XCom,
            "age_check_column": XCom.execution_date
        },
        {
            "airflow_db_model": SlaMiss,
            "age_check_column": SlaMiss.execution_date
        },
        {
            "airflow_db_model": DagModel,
            "age_check_column": DagModel.last_parsed_time
        }]
try:
    from airflow.models import TaskReschedule
    DATABASE_OBJECTS.append({
        "airflow_db_model": TaskReschedule,
        "age_check_column": TaskReschedule.start_date
    })
except Exception as e:
    logging.error(e)

try:
    from airflow.models import TaskFail
    DATABASE_OBJECTS.append({
        "airflow_db_model": TaskFail,
        "age_check_column": TaskFail.execution_date
    })
except Exception as e:
    logging.error(e)

try:
    from airflow.models import RenderedTaskInstanceFields
    DATABASE_OBJECTS.append({
        "airflow_db_model": RenderedTaskInstanceFields,
        "age_check_column": RenderedTaskInstanceFields.execution_date
    })
except Exception as e:
    logging.error(e)

try:
    from airflow.models import ImportError
    DATABASE_OBJECTS.append({
        "airflow_db_model": ImportError,
        "age_check_column": ImportError.timestamp
    })
except Exception as e:
    logging.error(e)

airflow_executor = str(conf.get("core", "executor"))
if (airflow_executor == "CeleryExecutor"):
    try:
        from celery.backends.database.models import Task, TaskSet
        DATABASE_OBJECTS.extend((
            {
                "airflow_db_model": Task,
                "age_check_column": Task.date_done,
            },
            {
                "airflow_db_model": TaskSet,
                "age_check_column": TaskSet.date_done,
            }))

    except Exception as e:
        logging.error(e)


def db_cleanup_function():
    """
        Description: Delete the records from table for passed data_model based on passed column name
        before DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS days or older than that.
        return: None
    """
    max_date = now() + timedelta(-DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS)
    session = settings.Session()

    for db_object in DATABASE_OBJECTS:
        airflow_db_model = db_object.get("airflow_db_model")
        age_check_column = db_object.get("age_check_column")
        try:
            query = session.query(airflow_db_model).options(load_only(age_check_column))
            query = query.filter(age_check_column <= max_date)
            entries_to_delete = query.all()
            print("Table Name :" + str(airflow_db_model.__name__) + "\n" + "Query: " + str(query))
            print("Process will be Deleting " + str(len(entries_to_delete)) + " records")
            query.delete(synchronize_session=False)
            session.commit()
            print("Finished Running Cleanup Process")
        except ProgrammingError as exp:
            print(exp)
