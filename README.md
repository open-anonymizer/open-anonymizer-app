# Open Anonymizer Application

Open Anonymizer is a natural language processing software that anonymizes German texts. Open Anonymizer uses a XLM-RoBERTa model for anonymizing `persons/names`, `locations`, `organizations` and a rule-based approach for anonymizing `dates`, `phone numbers`, `other numbers` and `emails`.

We also offer a graphical interface that you can see and start as described below.

---

### Start application

Make sure that poetry is installed on your machine (https://python-poetry.org/docs/#installation) and within this directory initialize your virtual environment with `poetry shell` afterwards you can start the application via

```
streamlit run app.py
```

This might take a while to start as the model is loaded when first used. 

--- 

You can anonymize single texts

![Screenshot Showcase App](screenshot_single_text.png?raw=true)

or use the file upload

![Screenshot Showcase App](screenshot_file_upload.png?raw=true)

--- 

This application can also be viewed here https://openanonymizer.codes/

--- 

You can also use Docker to run this application on another computer of your choice. However if you decide to do so, we strongly suggest that you download the model before and run the application with a production flag as described below.

```
poetry shell 
poetry install 

python3 get_model.py

docker build . -t open-anonymizer-webapp
docker run -e DEPLOYMENT=true -p 8501:8501 open-anonymizer-webapp
```

## Further information

Open Anonymizer is a part of our Master Thesis for the Mannheim Master of Applied Data Science & Measurement written by Dimitri Epp and Markus Nutz.

## License 

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
