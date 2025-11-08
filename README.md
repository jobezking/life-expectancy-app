Life Expectancy Calculator   
To run locally (sensible\_browser presumes Linux desktop, otherwise copy and paste URL):

pip install \-r requirements.txt  
flask run  
sensible-browser [http://localhost:8888](http://localhost:8888) 

To run in Docker (Docker commands may require sudo):   
docker build \-t life-expectancy-app . &  
docker run \-p 8888:8888 life-expectancy-app   
sensible-browser http://localhost:8888  
When done:  
docker ps   
\# obtain the value from the "NAMES" column i.e. interesting\_less  
docker kill interesting\_less

To run in Docker Compose (Docker commands may require sudo):  
docker compose up \--build &  
sensible-browser http://localhost:8888  
docker compose down

