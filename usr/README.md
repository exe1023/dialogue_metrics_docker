# USR Dockerized Server

## Build Docker Image
```
sh build_docker.sh
```

## Run Docker Container
```
sh run_docker.sh
```

## Test the Running Docker 
```
sh test_server.sh
```

## Code Structure

Entry Point: `usr_server.py`

Main API: `usr.py`

Retrieval Dialogue Metrics API: `dr_api.py`

Masked Language Model API: `mlm_api.py`

Arguments: `arguments.py`

