"""
Creation_Date: 2022-01-20
Owner: DART_TEAM
Description: A maintenance workflow that you can deploy into Airflow to periodically clean out the
    1. Task logs(default location :[CORE] BASE_LOG_FOLDER in airflow.cfg file)
    2. MetaDB(Default: SQLlite) TableName(ColBasedOnWhichDeletionOfRecordHappen): DagRun(Execution Date), TaskInstance(queued_dttm)
   Log(dttm), XCom(execution_date), TaskReschedule(execution_date), TaskFail(execution_date), RenderedTaskInstanceFields(execution_date)
   ImportError(timestampto)
avoid those getting too big.
Pre-Req:
1. Set the Environment variable (Airflow UI Admin-> Variable)
    * airflow_log_db_cleanup_max_log_age_in_days:(Integer) -Length to retain the log and MetaDB record. If this is set to 2, the job will remove those files that are 2 days old or older.,
    * airflow_log_cleanup_base_log_folder:(String) - ~/airflow/logs : Path to logs folder in your system
"""
import airflow
from datetime import timedelta,datetime
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import DAG, Variable
from reporting_etl_spark_jobs.utils.airflow_log_db_cleanup_functions import db_cleanup_function
from reporting_etl_spark_jobs.utils.env_variables import ARGS,FILE_PATH, DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS, BASE_LOG_FOLDER

dag = DAG("Airflow_Log_DB_Cleanup",
          default_args=ARGS,
          schedule_interval="30 3 * * *",
          description=__doc__,
          catchup=False,
          template_searchpath=FILE_PATH,
          tags=['30 3 * * *','daily','Airflow_Log_DB_Cleanup']
          )

start_log_clean_up = DummyOperator(
    task_id='start_log_clean_up',
    dag=dag)

end_log_clean_up = DummyOperator(
    task_id='end_log_clean_up',
    dag=dag)

db_cleanup_op = PythonOperator(task_id="airflow_db_cleanup",
                               python_callable=db_cleanup_function,
                               dag=dag
                               )

log_cleanup_op = BashOperator(task_id="airflow_log_cleanup",
                              bash_command="bash_script_log_db_cleanup.sh",
                              params={
                                  "DIRECTORIES_TO_DELETE": str(BASE_LOG_FOLDER),
                                  "DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS": int(DEFAULT_MAX_LOG_DB_ENTRY_AGE_IN_DAYS)
                              },
                              dag=dag)

start_log_clean_up >> db_cleanup_op >> log_cleanup_op >> end_log_clean_up

