# Youtube playlist summarizer

## Setup

- You'll need several API keys to run this script, check out .env.example for a list of required keys. Rename it to .env and fill in your own keys.
- You'll also need to install the required Python packages. You can do this by running `pip install -r requirements.txt`.
- You'll also need to set up a Google Cloud project and enable the YouTube Data API. Follow the instructions in the [Google Cloud documentation](https://cloud.google.com/video-intelligence/docs/setup-guide) to set up the project and enable the API.

## Usage

To run the script, simply run `python main.py` in the terminal with the following arguments:

- `--roast`: Enable roast mode.
- `--discover [SEARCH_TERMS]`: Search for videos and add them to the playlist. Replace `[SEARCH_TERMS]` with the terms you want to search for.
- `--include [WORDS]`: Include videos with these words in the title. Replace `[WORDS]` with the words you want to include.
- `--exclude [WORDS]`: Exclude videos with these words in the title. Replace `[WORDS]` with the words you want to exclude.
- `--num [NUMBER]`: Number of videos to add. Replace `[NUMBER]` with the number of videos you want to add (default: 5).

Example usage:

## Notes

- The script uses the [Exa](https://github.com/exasol/exa) API to search for videos on YouTube. It uses the `neural` search type, which means it will search for videos that are relevant to the search query. The script also uses the `include_text` and `exclude_text` parameters to filter out videos that don't match the search query.

## Contributing

Contributions are welcome! If you have any suggestions or improvements, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
