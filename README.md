# LinkedIn Job Fetcher

A simple Python script to fetch job listings from LinkedIn based on user-defined criteria using Selenium for web scraping. This project allows users to search for jobs by keywords and location and prints the job details to the console.

## Features

- **Login to LinkedIn**: Automates the login process using Selenium.
- **Search Jobs**: Fetches job listings based on keywords and location.
- **Console Output**: Prints job details including title, company, and location.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/atwalnimrat/linkedin-job-fetcher.git
   cd linkedin-job-fetcher
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` should include:
   ```plaintext
   selenium
   ```

   Make sure to also download the appropriate ChromeDriver for your version of Chrome and place it in a directory included in your PATH.

## Usage

1. **Run the script**:
   ```bash
   python linkedin-job-fetcher.py
   ```

2. **Enter your LinkedIn login credentials** and search criteria when prompted.

## Configuration for Executable

To create an executable from the Python script:

1. **Ensure PyInstaller is installed**:
   ```bash
   pip install pyinstaller
   ```

2. **Build the executable**:
   ```bash
   pyinstaller --onefile linkedin-job-fetcher.spec
   ```

   This will create a standalone executable based on the configuration in `linkedin-job-fetcher.spec`.

## Notes

- **Browser Compatibility**: This script uses ChromeDriver. Ensure that your ChromeDriver version matches your installed Chrome browser version.
- **LinkedIn Login**: This script automates the LinkedIn login process. Use it responsibly and ensure compliance with LinkedIn's terms of service.
- **Error Handling**: Basic error handling is implemented. You might need to adjust or enhance it based on your needs.

## Contributing

Feel free to submit issues or pull requests to improve the functionality of this project.
