# Exponea Software Engineer assignment

This app was build using Fastapi

Please refer to **Test_report.pdf** for code discussion / case studies / empirical studies and performance bencharmking.


## Getting started

First, you should install necessary requirements, by typing:  
`pip install -r requirements.txt`

To run the api, type this command:  
`uvicorn src.api:app --reload`

Then you can just run the api by sending request to the following url
`http://127.0.0.1:8000/api/smart/<timeout_param>`

To run the tests, type this command:
`pytest`

## Run app with docker 

To run this project with docker, you'll need to have [Docker](https://docs.docker.com/get-docker/) installed.

Build the container, providing a tag:  
`docker build -t fastapi-image .`

Then you can run the container, passing in a name for the container, and the previously used tag:  
`docker run -p 8000:8000 --name fastapi_app fastapi-image`

Then you can just run the api by sending request to the following url
`http://127.0.0.1:8000/api/smart/<timeout_param>`

Note that if you used the code as-is with the `--reload` option that you won't be able to kill the container using `CTRL + C`.  
Instead in another terminal window you can kill the container using Docker's kill command:  
`docker kill fastapi_app`

Notes:
run `docker ps -a` to see all containers.
run `run docker fastapi-image` to run the image that is already in created container. 