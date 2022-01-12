## Steps ##

- Install Python 3.8
- Preferably use a [venv](https://realpython.com/python-virtual-environments-a-primer/)
- `pip install -r requirements.txt`
- Rename `config.sample.yml` to `config.yml` and fill in the information
- Set up your Google stuff
    - Create a Google Developer Project on the [Cloud Platform](https://console.cloud.google.com/)
    - [Enable Google Drive on it](https://console.cloud.google.com/apis/library/drive.googleapis.com)
    - You may be prompted to create credentials, which you can do so with the next step.
    - [Create a Service Account](https://developers.google.com/identity/protocols/oauth2/service-account).
        - Select "Application Data".
    - Place your `service_account.json` in the working directory
    - Don't forget to share your drive folder with your provided Service Account email.
