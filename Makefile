.PHONY: setup data train test run docker
setup: ; pip install -r requirements.txt
data:  ; python -m src.generate_sample_data
train: ; python -m src.train
test:  ; python -m unittest discover -s tests
run:   ; python -m app.app
docker: ; docker compose up --build
