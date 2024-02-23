import os
import json
from airflow.models.dag import DAG
from airflow.models import Variable
from datetime import datetime, timedelta
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


extractor_paths = []

def create_folder_for_today(today_date):
    base_path = Variable.get('base_path') 
    postgres_path = os.path.join(base_path, 'data/postgres')
    postgres_table_paths = os.listdir(postgres_path)
    csv_path = os.path.join(base_path, 'data/csv/order_details', today_date)
    os.makedirs(csv_path, exist_ok=True)
    extractor_paths.append(csv_path)
    
    for table_name in postgres_table_paths:
        table_path = os.path.join(postgres_path, table_name, today_date)
        os.makedirs(table_path, exist_ok=True)
        extractor_paths.append(table_path)
   
def get_source_names():
    base_path = Variable.get("base_path")

    data_path = os.path.join(base_path, 'data')
    data_dirs = os.listdir(data_path)
    sources = []
    for dir in data_dirs:
        dir_path = os.path.join(data_path, dir)
        if not os.path.isdir(dir_path):
            continue
        source_paths = os.listdir(dir_path)
        for source_path in source_paths:
            source = os.path.join(dir, source_path)
            sources.append(source)
     
    return sources  

def write_config_file(file_destination):
    base_path = Variable.get("base_path")                      
    config_path = os.path.join(base_path, "elt-desafio/config.json")    
    config_file = open(config_path, "w")
    for config in file_destination:        
        new_path = config["path"].lstrip("../")
        full_path = os.path.join(base_path, new_path)
        if len(os.listdir(full_path)) == 0:
            file_destination.remove(config)
    config_file.write(json.dumps(file_destination))    
    config_file.close() 


default_args={
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "indicium_challenge_dag",
    description="Indicium challenge pipeline",
    schedule=timedelta(days=1),
    start_date=datetime(2024, 2, 19),
    catchup=False,
 
) as dag:
        
    folder_creation_task = PythonOperator(
        task_id="create_folder",
        python_callable=create_folder_for_today,
        op_kwargs={'today_date': '{{ ds }}'}
    )        

    sources = get_source_names()
    meltano_tasks = []
    tap_csv_final_config = []
    ds = '{{ ds }}'
    for source in sources:
        meltano_task = []
        source_name = source.split('/')[-1]
        set_destination_step1 = BashOperator(
            task_id=f"set_destination_path_{source_name}",
            bash_command=f"source .meltanovenv/bin/activate &&\
                meltano --cwd ./elt-desafio config target-csv-{source_name}\
                    set destination_path ../data/{source}/{ds}",
            cwd=Variable.get("base_path")
        )
        
        meltano_run_step1 = BashOperator(
            task_id=f"run_data_extractor_{source_name}",
            bash_command=f"source .meltanovenv/bin/activate &&\
                meltano --cwd ./elt-desafio run tap-{source_name} target-csv-{source_name}",
            cwd=Variable.get("base_path")
        )
        
        meltano_task.append(set_destination_step1)
        meltano_task.append(meltano_run_step1)
        meltano_tasks.append(meltano_task.copy())  

        file_config = {
            "entity": source_name, 
            "path": f"../data/{source}/{ds}", 
            "keys": []
        }
        tap_csv_final_config.append(file_config.copy()) 
    
    create_config_file = PythonOperator(
        task_id="create_json",
        python_callable=write_config_file,
        op_kwargs={"file_destination": tap_csv_final_config} 
    )
                            
    set_files_step2 = BashOperator(
        task_id="set_files",
        bash_command=f"source .meltanovenv/bin/activate &&\
            meltano --cwd ./elt-desafio config tap-final\
            set csv_files_definition config.json",
        cwd=Variable.get("base_path") 
    )
    
    meltano_run_step2 = BashOperator(
        task_id=f"run_data_extractor_step_2",
        bash_command=f"source .meltanovenv/bin/activate &&\
            meltano --cwd ./elt-desafio run tap-final target-postgres",
        cwd=Variable.get("base_path")
    )
          
    for step1 in meltano_tasks:
        folder_creation_task >> step1[0]
        step1[0] >> step1[1]  
        step1[1] >> create_config_file
    
    create_config_file >> set_files_step2 >> meltano_run_step2  

    
   
    
